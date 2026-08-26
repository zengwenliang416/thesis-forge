"""Template Package v2 PackageEditor（SCHEMA §5.2/§5.3/§5.4/§5.5，ADR-0002）。

把编译产物 docx 按锚点协议合并进 shell.docx。这是 OOXML/OPC **包级**操作：
直接操作 ZIP 条目 + lxml，不依赖 python-docx 文档模型（SPIKE §4.1：python-docx
没有跨包合并 API，且 fontTable/theme 等部件只暴露 blob）。

搬运清单（SCHEMA §5.3，spike 实证台账的工程化）：

- relationships：导入节点引用的 rId 全部重映射（allocator = shell 现有最大
  rId 编号 +1 递增，确定性）；目标部件复制进包，部件名冲突按数字后缀递增
  重命名，rels ``Target`` 同步改写；
- 部件级 rels 递归：被搬运部件（如 header/footer）内部再引用资源时递归搬运，
  部件内部 rId 命名空间独立故保持不变，只改写其 rels 的 ``Target``
  （SPIKE §3.6 的 ``NotImplementedError`` 边界在本实现中落地）；
- styles：按「被引用 + basedOn/next/link 闭包」最小搬运；冲突策略 D-3：
  先按 style token 对齐（token → 样式名为合并键），之后 **shell-wins**；
  token 无映射的冲突记 ``style-conflict-unmapped``（warning）入台账；
  ``docDefaults``/``latentStyles`` 保留 shell 不合并；
- numbering.xml：shell 未引用 numId → compiled 整体替换；shell 已引用 →
  双侧 numId/abstractNumId 确定性重映射（compiled 侧平移至 max+1 起）后合并
  （SPIKE §3.7 边界落地，OQ-3 编号侧关闭）；
- footnotes part：shell 无 footnotes.xml → 整体搬运 + 登记 relationship +
  Content Types Override；shell 已有 → ``w:id`` 双侧重映射后合并
  （separator/continuation 等保留项 shell-wins，OQ-3 脚注侧关闭）；
- ``[Content_Types].xml``：从 compiled CT 复制 Override 并改写为新部件名；
- settings/theme/fontTable/docProps：不合并（D-5）；settings 白名单字段
  （evenAndOddHeaders/updateFields/mirrorMargins）由 template.yaml 语义统一
  写入，不拷贝 compiled 的 settings。

安全策略（§5.5）：宏/外部关系/OLE 在合并时兜底拦截（lint L1 为尽早失败层）。

确定性（SPIKE §4.8，R-019）：allocator 与重命名规则保证相同输入产出字节级
相同的合并结果——ZIP entry 时间戳固定为 DOS 纪元（1980-01-01），entry 顺序
为 shell 原序 + 新部件按处理序追加，压缩固定 DEFLATE level 9。

已知边界（未实证项显式排除）：

- region manifest 分槽投递（D-4 第 1 条/C-8）依赖 Compiler 输出 region 边界，
  当前管线尚无此 manifest；本实现沿用 spike 选取策略（封面分节符之后全部
  投递 body 槽），tf_toc/tf_bibliography 锚点保留原位不投递。
"""

from __future__ import annotations

import copy
import posixpath
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from lxml import etree

from docforge.core.model import ValidationIssue

if TYPE_CHECKING:
    from .package import ResolvedTemplatePackage

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

# ZIP entry 时间戳固定为 DOS 纪元（确定性打包，对齐 SCHEMA §7.2 D-6）
_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

DEFAULT_ANCHORS = {"body": "tf_body", "toc": "tf_toc", "bibliography": "tf_bibliography"}

RID_ATTRS = ("id", "embed", "link")  # r: 命名空间下需要重映射的属性名
STYLE_REF_TAGS = ("pStyle", "rStyle", "tblStyle")
STYLE_LINK_TAGS = ("basedOn", "next", "link")
# footnotes 中 separator/continuationSeparator/continuationNotice 等保留 w:type
_FOOTNOTE_RESERVED_TYPES = ("separator", "continuationSeparator", "continuationNotice")

# settings.xml 白名单字段的 schema 后继元素（CT_Settings 顺序，SPIKE §3.5 同类约束）
_SETTINGS_SUCCESSORS = {
    "mirrorMargins": ("proofState", "defaultTabStop", "characterSpacingControl", "compat", "rsids"),
    "evenAndOddHeaders": (
        "characterSpacingControl",
        "savePreviewPicture",
        "updateFields",
        "compat",
        "rsids",
    ),
    "updateFields": ("hdrShapeDefaults", "footnotePr", "endnotePr", "compat", "rsids"),
}


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _r(tag: str) -> str:
    return f"{{{R_NS}}}{tag}"


def _pr(tag: str) -> str:
    return f"{{{PR_NS}}}{tag}"


def _ct(tag: str) -> str:
    return f"{{{CT_NS}}}{tag}"


def _serialize(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _rels_name_for(part_path: str) -> str:
    """word/header2.xml → word/_rels/header2.xml.rels"""
    directory, _, name = part_path.rpartition("/")
    return f"{directory}/_rels/{name}.rels"


def _rid_sort_key(rid: str) -> tuple[int, str]:
    match = re.fullmatch(r"rId(\d+)", rid or "")
    return (int(match.group(1)), rid) if match else (0, rid)


class PackageMergeError(ValueError):
    """合并失败；``code`` 为 SCHEMA §5 诊断码（如 missing-body-anchor）。"""

    def __init__(self, code: str, message: str, *, target: str | None = None):
        self.code = code
        self.target = target
        super().__init__(f"[{code}] {message}")


class PackageView:
    """DOCX 包的只读视图：原始字节 + 按需解析的 XML。"""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        with zipfile.ZipFile(self.path) as archive:
            self.parts = {name: archive.read(name) for name in archive.namelist()}
        self._xml_cache: dict[str, etree._Element] = {}

    def xml(self, name: str) -> etree._Element:
        if name not in self._xml_cache:
            self._xml_cache[name] = etree.fromstring(self.parts[name])
        return self._xml_cache[name]

    def rels(self, part_path: str) -> dict[str, dict[str, str]]:
        """某个部件的 relationship 表：Id → {Type, Target, TargetMode}。"""
        rels_name = _rels_name_for(part_path)
        result: dict[str, dict[str, str]] = {}
        if rels_name not in self.parts:
            return result
        for rel in self.xml(rels_name):
            result[rel.get("Id")] = {
                "Type": rel.get("Type", ""),
                "Target": rel.get("Target", ""),
                "TargetMode": rel.get("TargetMode", "Internal"),
            }
        return result


@dataclass(slots=True)
class MergeLedger:
    """搬运台账（SCHEMA §5.3：落入 build manifest，供 lint 与排障使用）。"""

    shell_docx: str
    compiled_docx: str
    output_docx: str
    anchors: dict[str, dict[str, Any]] = field(default_factory=dict)
    selection: dict[str, Any] = field(default_factory=dict)
    rid_mapping: dict[str, str] = field(default_factory=dict)
    carried_relationships: list[dict[str, Any]] = field(default_factory=list)
    footnotes: dict[str, Any] = field(default_factory=dict)
    styles: dict[str, Any] = field(default_factory=dict)
    numbering: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    not_merged: dict[str, str] = field(default_factory=dict)
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shell_docx": self.shell_docx,
            "compiled_docx": self.compiled_docx,
            "output_docx": self.output_docx,
            "anchors": self.anchors,
            "selection": self.selection,
            "rid_mapping": self.rid_mapping,
            "carried_relationships": self.carried_relationships,
            "footnotes": self.footnotes,
            "styles": self.styles,
            "numbering": self.numbering,
            "settings": self.settings,
            "security": self.security,
            "not_merged": self.not_merged,
            "issues": [
                {
                    "code": issue.code,
                    "severity": issue.severity,
                    "message": issue.message,
                    "target": issue.target,
                }
                for issue in self.issues
            ],
        }


class _CarryContext:
    """搬运上下文：目标包的新部件、新 relationship、内容类型登记与台账。"""

    def __init__(self, shell: PackageView, compiled: PackageView) -> None:
        self.shell = shell
        self.compiled = compiled
        self.dst_rels_root = copy.deepcopy(shell.xml("word/_rels/document.xml.rels"))
        self.dst_parts: dict[str, bytes] = {}
        self.dst_names = set(shell.parts)
        self.used_rids = {rel.get("Id") for rel in self.dst_rels_root}
        self.ct_root = copy.deepcopy(shell.xml("[Content_Types].xml"))
        self.compiled_ct_overrides = {
            el.get("PartName"): el.get("ContentType")
            for el in compiled.xml("[Content_Types].xml")
            if el.tag == _ct("Override")
        }
        self.report: list[dict[str, Any]] = []
        self.part_memo: dict[str, str] = {}  # src 部件 → dst 部件（去重）
        self.carried_xml_roots: list[etree._Element] = []  # 搬运来的 XML 部件（样式引用扫描用）

    def allocate_rid(self) -> str:
        numbers = [
            int(match.group(1))
            for rid in self.used_rids
            if (match := re.fullmatch(r"rId(\d+)", rid or ""))
        ]
        new_rid = f"rId{max(numbers, default=0) + 1}"
        self.used_rids.add(new_rid)
        return new_rid

    def allocate_part_name(self, src_path: str) -> str:
        """部件名冲突按数字后缀递增（header2.xml→header3.xml，image1.png→image2.png）。"""
        if src_path not in self.dst_names:
            return src_path
        stem, dot, ext = src_path.rpartition(".")
        match = re.match(r"^(.*?)(\d+)$", stem)
        base, number = (match.group(1), int(match.group(2))) if match else (stem, 0)
        while True:
            number += 1
            candidate = f"{base}{number}{dot}{ext}"
            if candidate not in self.dst_names:
                return candidate

    def ensure_content_type(self, src_path: str, dst_path: str) -> None:
        override = self.compiled_ct_overrides.get(f"/{src_path}")
        if override is None:
            return  # 由 Default（如 png/xml）覆盖，无需登记
        part_name = f"/{dst_path}"
        existing = {el.get("PartName") for el in self.ct_root if el.tag == _ct("Override")}
        if part_name not in existing:
            element = etree.SubElement(self.ct_root, _ct("Override"))
            element.set("PartName", part_name)
            element.set("ContentType", override)


class PackageEditor:
    """把编译产物 docx 合并进 shell.docx 锚点的 OPC 包级编辑器。

    参数：
    - ``shell_path``：shell.docx 路径（只读，绝不就地修改，D-1）；
    - ``anchors``：region 槽 → 锚点书签名（默认 tf_body/tf_toc/tf_bibliography）；
    - ``token_style_names``：§3.7 已声明 token 的样式名集合（D-3 冲突对齐键）；
    - ``template``：可选 TemplatePackageSpec，提供时按 D-5 写入 settings 白名单；
    - ``external_relationships`` / ``external_relationship_allowlist``：§5.5 策略。
    """

    def __init__(
        self,
        shell_path: str | Path,
        *,
        anchors: dict[str, str] | None = None,
        token_style_names: tuple[str, ...] | list[str] = (),
        template: Any = None,
        external_relationships: str = "forbid",
        external_relationship_allowlist: tuple[str, ...] | list[str] = (),
    ) -> None:
        self.shell_path = Path(shell_path)
        self.anchors = {**DEFAULT_ANCHORS, **(anchors or {})}
        self.token_style_names = frozenset(token_style_names)
        self.template = template
        self.external_policy = external_relationships
        self.external_allowlist = tuple(external_relationship_allowlist)

    @classmethod
    def from_package(cls, resolved: ResolvedTemplatePackage) -> PackageEditor:
        """从已解析的 v2 包构造：锚点、token、安全策略、settings 语义全部取自模板。"""
        if resolved.shell_docx is None:
            raise PackageMergeError(
                "missing-package-file",
                "模板包未声明 word.shell_docx，无法执行 shell 合并",
                target="word.shell_docx",
            )
        template = resolved.template
        token_names = (
            *template.styles.paragraph.declared().values(),
            *template.styles.heading.declared().values(),
            *template.styles.character.declared().values(),
        )
        return cls(
            resolved.shell_docx,
            anchors=dict(template.word.anchors),
            token_style_names=token_names,
            template=template,
            external_relationships=template.word.external_relationships,
            external_relationship_allowlist=tuple(
                template.word.external_relationship_allowlist
            ),
        )

    # ------------------------------------------------------------------
    # 安全策略（§5.5 合并时兜底拦截）
    # ------------------------------------------------------------------

    def _check_external(self, target_url: str, where: str, security_notes: list[str]) -> None:
        if self.external_policy == "allowlist" and self._in_allowlist(target_url):
            security_notes.append(f"外部关系命中白名单：{target_url}（{where}）")
            return
        raise PackageMergeError(
            "external-relationship",
            f"外部关系被策略 {self.external_policy} 拒绝：{target_url}（{where}）",
            target=where,
        )

    def _in_allowlist(self, target_url: str) -> bool:
        from urllib.parse import urlparse

        parsed = urlparse(target_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        for entry in self.external_allowlist:
            allowed = urlparse(entry)
            if allowed.scheme and origin == f"{allowed.scheme}://{allowed.netloc}":
                return True
        return False

    def _scan_security(self, view: PackageView, *, label: str) -> list[str]:
        """宏/OLE 扫描 + 收集全部外部关系（外部 rel 在搬运时逐条过策略）。"""
        names = set(view.parts)
        if any(name.endswith("vbaProject.bin") for name in names) or (
            "[Content_Types].xml" in names
            and b"macroEnabled" in view.parts["[Content_Types].xml"]
        ):
            raise PackageMergeError(
                "macro-detected",
                f"{label} 含宏（vbaProject/macroEnabled），macro_policy 仅允许 forbid",
                target=label,
            )
        if any(name.startswith(("word/embeddings/", "word/activeX/")) for name in names):
            raise PackageMergeError(
                "ole-detected",
                f"{label} 含 OLE/嵌入对象部件（word/embeddings/ 或 word/activeX/）",
                target=label,
            )
        externals: list[str] = []
        for name in sorted(n for n in names if n.endswith(".rels")):
            for rel in view.xml(name):
                if rel.get("TargetMode") == "External":
                    externals.append(rel.get("Target") or "")
        return externals

    # ------------------------------------------------------------------
    # 锚点（§5.2）
    # ------------------------------------------------------------------

    @staticmethod
    def _find_anchor_paragraph(body: etree._Element, name: str) -> etree._Element | None:
        for bookmark in body.iter(_w("bookmarkStart")):
            if bookmark.get(_w("name")) == name:
                paragraph = bookmark.getparent()
                if paragraph is None or paragraph.tag != _w("p"):
                    raise PackageMergeError(
                        "invalid-word-asset",
                        f"锚点 {name} 不在段落级，锚点协议要求书签位于空段落内",
                        target=name,
                    )
                return paragraph
        return None

    def _locate_anchors(self, shell_body: etree._Element) -> dict[str, dict[str, Any]]:
        found: dict[str, dict[str, Any]] = {}
        for slot, name in sorted(self.anchors.items()):
            paragraph = self._find_anchor_paragraph(shell_body, name)
            if paragraph is None:
                found[slot] = {"name": name, "status": "absent"}
            else:
                found[slot] = {
                    "name": name,
                    "status": "present",
                    "body_index": list(shell_body).index(paragraph),
                }
                found[slot]["paragraph"] = paragraph  # 内部句柄，落盘前剔除
        body_slot = found.get("body", {"name": self.anchors.get("body", "tf_body")})
        if body_slot["status"] == "absent":
            raise PackageMergeError(
                "missing-body-anchor",
                f"shell.docx 缺少锚点书签 {body_slot['name']}（§5.2.2：缺失 body "
                "anchor 为阻断错误）",
                target=body_slot["name"],
            )
        return found

    @staticmethod
    def _consume_anchor(shell_root: etree._Element, paragraph: etree._Element, name: str) -> None:
        """锚点消费即移除（§5.2.3 第 5 条）：移除锚点段落并成对清理书签（SPIKE §3.4）。"""
        ids = {
            el.get(_w("id"))
            for el in paragraph.iter(_w("bookmarkStart"))
            if el.get(_w("name")) == name
        }
        paragraph.getparent().remove(paragraph)
        for tag in ("bookmarkStart", "bookmarkEnd"):
            for el in list(shell_root.iter(_w(tag))):
                if el.get(_w("name")) == name or (tag == "bookmarkEnd" and el.get(_w("id")) in ids):
                    el.getparent().remove(el)

    # ------------------------------------------------------------------
    # 编译产物节点选取（spike 策略；region manifest 分槽投递见模块 docstring 边界）
    # ------------------------------------------------------------------

    @staticmethod
    def _select_imported_children(
        compiled_body: etree._Element,
    ) -> tuple[list[etree._Element], dict[str, Any]]:
        """选取 compiled 正文中「首个分节符段落之后」的全部节点（深拷贝）。

        封面/声明由 shell 持有，故丢弃封面区与其分节符；compiled 的 body 级
        final sectPr 必须显式丢弃（SPIKE §3.3），由 shell 的 main sectPr 接管。
        无分节符的 compiled 退化为导入全部正文（仍丢弃 final sectPr）。
        """
        children = list(compiled_body)
        cover_break_index = next(
            (
                i
                for i, child in enumerate(children)
                if child.tag == _w("p")
                and child.find(f"{_w('pPr')}/{_w('sectPr')}") is not None
            ),
            None,
        )
        start = cover_break_index + 1 if cover_break_index is not None else 0
        imported = [copy.deepcopy(child) for child in children[start:]]
        dropped_final_sectpr = bool(imported) and imported[-1].tag == _w("sectPr")
        if dropped_final_sectpr:
            imported = imported[:-1]
        info = {
            "compiled_body_children": len(children),
            "dropped_cover_region_children": start,
            "dropped_compiled_final_sectPr": dropped_final_sectpr,
            "imported_children": len(imported),
        }
        return imported, info

    # ------------------------------------------------------------------
    # relationships / 部件搬运（含部件级 rels 递归，SPIKE §3.6 边界落地）
    # ------------------------------------------------------------------

    def _carry_part(
        self,
        ctx: _CarryContext,
        src_path: str,
        security_notes: list[str],
        _carrying: frozenset[str] = frozenset(),
    ) -> str:
        """把 compiled 的 ``src_path`` 部件复制进包（冲突重命名），返回 dst 部件名。

        部件带自己的 .rels 时递归搬运其内部引用：部件内部 rId 命名空间独立，
        故部件 XML 中 r:id 保持不变，只重写其 rels 的 ``Target`` 指向新部件名。
        """
        if src_path in ctx.part_memo:
            return ctx.part_memo[src_path]
        if src_path in _carrying:
            raise PackageMergeError(
                "invalid-word-asset",
                f"部件级 rels 存在循环引用：{src_path}",
                target=src_path,
            )
        if src_path not in ctx.compiled.parts:
            raise PackageMergeError(
                "invalid-word-asset",
                f"compiled 的 relationship 目标部件不存在：{src_path}",
                target=src_path,
            )
        dst_path = ctx.allocate_part_name(src_path)
        inner_rels_name = _rels_name_for(src_path)
        payload = ctx.compiled.parts[src_path]
        if inner_rels_name in ctx.compiled.parts:
            new_rels_root = copy.deepcopy(ctx.compiled.xml(inner_rels_name))
            for rel in new_rels_root:
                rid = rel.get("Id")
                if rel.get("TargetMode") == "External":
                    self._check_external(
                        rel.get("Target") or "", f"{inner_rels_name}#{rid}", security_notes
                    )
                    continue
                inner_src = posixpath.normpath(
                    posixpath.join(posixpath.dirname(src_path), rel.get("Target") or "")
                )
                inner_dst = self._carry_part(
                    ctx, inner_src, security_notes, _carrying | {src_path}
                )
                rel.set("Target", posixpath.relpath(inner_dst, posixpath.dirname(dst_path)))
            ctx.dst_parts[_rels_name_for(dst_path)] = _serialize(new_rels_root)
            ctx.dst_names.add(_rels_name_for(dst_path))
        if src_path.endswith(".xml"):
            ctx.carried_xml_roots.append(etree.fromstring(payload))
        ctx.dst_parts[dst_path] = payload
        ctx.dst_names.add(dst_path)
        ctx.ensure_content_type(src_path, dst_path)
        ctx.part_memo[src_path] = dst_path
        return dst_path

    def _carry_document_relationship(
        self, ctx: _CarryContext, src_rid: str, security_notes: list[str]
    ) -> str:
        """把 compiled 文档级的一条 relationship（含目标部件）搬进 shell，返回新 rId。"""
        rel = ctx.compiled.rels("word/document.xml")[src_rid]
        if rel["TargetMode"] == "External":
            # 白名单命中的外部关系原样登记（不拷部件）；forbid 在 _check_external 抛错
            self._check_external(
                rel["Target"], f"word/_rels/document.xml.rels#{src_rid}", security_notes
            )
            new_rid = ctx.allocate_rid()
            element = etree.SubElement(ctx.dst_rels_root, _pr("Relationship"))
            element.set("Id", new_rid)
            element.set("Type", rel["Type"])
            element.set("Target", rel["Target"])
            element.set("TargetMode", "External")
            ctx.report.append(
                {
                    "src_rid": src_rid,
                    "new_rid": new_rid,
                    "type": rel["Type"].rsplit("/", 1)[-1],
                    "src_part": None,
                    "dst_part": None,
                    "renamed": False,
                    "external": True,
                }
            )
            return new_rid
        src_path = posixpath.normpath(posixpath.join("word", rel["Target"]))
        dst_path = self._carry_part(ctx, src_path, security_notes)
        new_rid = ctx.allocate_rid()
        element = etree.SubElement(ctx.dst_rels_root, _pr("Relationship"))
        element.set("Id", new_rid)
        element.set("Type", rel["Type"])
        element.set("Target", posixpath.relpath(dst_path, "word"))
        ctx.report.append(
            {
                "src_rid": src_rid,
                "new_rid": new_rid,
                "type": rel["Type"].rsplit("/", 1)[-1],
                "src_part": src_path,
                "dst_part": dst_path,
                "renamed": src_path != dst_path,
            }
        )
        return new_rid

    def _remap_rid_references(
        self, imported: list[etree._Element], ctx: _CarryContext, security_notes: list[str]
    ) -> dict[str, str]:
        """重映射 imported 节点里的全部 r:id/r:embed/r:link，返回映射表。"""
        referenced: list[str] = []
        for element in imported:
            for node in element.iter():
                for attr in RID_ATTRS:
                    value = node.get(_r(attr))
                    if value is not None:
                        referenced.append(value)
        mapping = {
            rid: self._carry_document_relationship(ctx, rid, security_notes)
            for rid in sorted(set(referenced), key=_rid_sort_key)
        }
        for element in imported:
            for node in element.iter():
                for attr in RID_ATTRS:
                    value = node.get(_r(attr))
                    if value is not None:
                        node.set(_r(attr), mapping[value])
        return mapping

    # ------------------------------------------------------------------
    # footnotes（§5.3；双侧占用时 w:id 重映射合并，OQ-3 脚注侧落地）
    # ------------------------------------------------------------------

    def _carry_footnotes(
        self, imported: list[etree._Element], ctx: _CarryContext, security_notes: list[str]
    ) -> dict[str, Any]:
        """footnotes 部件搬运：按 w:id 关联（footnoteReference），不是 r:id。"""
        used = {
            el.get(_w("id")) for element in imported for el in element.iter(_w("footnoteReference"))
        }
        if not used:
            return {"used_footnote_ids": [], "action": "none"}
        if "word/footnotes.xml" not in ctx.compiled.parts:
            return {
                "used_footnote_ids": sorted(used, key=int),
                "action": "none",
                "note": "compiled 无 footnotes.xml，导入的 footnoteReference 将悬空",
            }
        if "word/footnotes.xml" not in ctx.shell.parts:
            rel = ctx.compiled.rels("word/document.xml")
            footnote_rid = next(r for r, v in rel.items() if v["Target"] == "footnotes.xml")
            new_rid = self._carry_document_relationship(ctx, footnote_rid, security_notes)
            return {
                "used_footnote_ids": sorted(used, key=int),
                "action": "carried whole footnotes.xml",
                "new_rid": new_rid,
                "note": "w:id 无需重映射：shell 无既有脚注，id 空间不冲突",
            }
        # 双侧占用：w:id 重映射合并（保留项 separator/continuation shell-wins）
        shell_root = copy.deepcopy(ctx.shell.xml("word/footnotes.xml"))
        shell_ids = {el.get(_w("id")) for el in shell_root.iter(_w("footnote"))}
        shell_types = {
            el.get(_w("type")) for el in shell_root.iter(_w("footnote")) if el.get(_w("type"))
        }
        next_id = max((int(i) for i in shell_ids if i and int(i) >= 1), default=0) + 1
        id_map: dict[str, str] = {}
        dropped_reserved: list[str] = []
        for footnote in ctx.compiled.xml("word/footnotes.xml").iter(_w("footnote")):
            old_id = footnote.get(_w("id"))
            ftype = footnote.get(_w("type"))
            if ftype in _FOOTNOTE_RESERVED_TYPES:
                if ftype in shell_types:
                    dropped_reserved.append(f"{ftype}(id={old_id})")
                    continue
                new_element = copy.deepcopy(footnote)
                if old_id in shell_ids:
                    new_element.set(_w("id"), str(next_id))
                    next_id += 1
                shell_root.append(new_element)
                shell_ids.add(new_element.get(_w("id")))
                shell_types.add(ftype)
                continue
            new_id = str(next_id)
            next_id += 1
            id_map[old_id] = new_id
            new_element = copy.deepcopy(footnote)
            new_element.set(_w("id"), new_id)
            shell_root.append(new_element)
        ctx.dst_parts["word/footnotes.xml"] = _serialize(shell_root)
        for element in imported:
            for ref in element.iter(_w("footnoteReference")):
                old = ref.get(_w("id"))
                if old in id_map:
                    ref.set(_w("id"), id_map[old])
        return {
            "used_footnote_ids": sorted(used, key=int),
            "action": "merged with w:id remap（shell 已有 footnotes 部件）",
            "id_map": id_map,
            "carried_count": len(id_map),
            "dropped_reserved": dropped_reserved,
        }

    # ------------------------------------------------------------------
    # styles（§5.3 + D-3：token 对齐后 shell-wins）
    # ------------------------------------------------------------------

    def _merge_styles(
        self, imported: list[etree._Element], ctx: _CarryContext
    ) -> tuple[dict[str, Any], list[etree._Element]]:
        """样式搬运：被引用样式 + basedOn/next/link 闭包；冲突 shell-wins。

        返回 (台账, 新增样式元素列表)——新增样式元素供 numbering 重映射扫描。
        """
        used: set[str] = set()
        scan_roots: list[etree._Element] = [*imported, *ctx.carried_xml_roots]
        for root in scan_roots:
            for tag in STYLE_REF_TAGS:
                used.update(
                    el.get(_w("val")) for el in root.iter(_w(tag)) if el.get(_w("val"))
                )
        if "word/styles.xml" in ctx.compiled.parts:
            compiled_styles = ctx.compiled.xml("word/styles.xml")
            defined = {
                el.get(_w("styleId")): el for el in compiled_styles.iter(_w("style"))
            }
        else:
            # 最小合成 docx 可无 styles 部件：无可搬运样式
            defined = {}
        closure: set[str] = set()
        worklist = list(used)
        while worklist:
            style_id = worklist.pop()
            if style_id in closure or style_id not in defined:
                continue
            closure.add(style_id)
            element = defined[style_id]
            for tag in STYLE_LINK_TAGS:
                link = element.find(_w(tag))
                if link is not None and link.get(_w("val")):
                    worklist.append(link.get(_w("val")))

        shell_styles_root = copy.deepcopy(ctx.shell.xml("word/styles.xml"))
        shell_defined = {el.get(_w("styleId")): el for el in shell_styles_root.iter(_w("style"))}
        imported_ids: list[str] = []
        conflicts: list[dict[str, Any]] = []
        appended: list[etree._Element] = []
        issues: list[ValidationIssue] = []
        for style_id in sorted(closure):
            source_element = copy.deepcopy(defined[style_id])
            if style_id in shell_defined:
                name_el = source_element.find(_w("name"))
                compiled_name = name_el.get(_w("val")) if name_el is not None else None
                shell_name_el = shell_defined[style_id].find(_w("name"))
                shell_name = shell_name_el.get(_w("val")) if shell_name_el is not None else None
                token_aligned = bool(
                    self.token_style_names
                    & {name for name in (compiled_name, shell_name, style_id) if name}
                )
                conflicts.append(
                    {
                        "style_id": style_id,
                        "compiled_name": compiled_name,
                        "shell_name": shell_name,
                        "token_aligned": token_aligned,
                        "policy": "shell-wins",
                    }
                )
                if not token_aligned:
                    issues.append(
                        ValidationIssue(
                            code="style-conflict-unmapped",
                            severity="warning",
                            message=(
                                f"导入内容引用样式 {style_id}"
                                f"（{compiled_name or style_id}）与 shell 同名但无 token "
                                "映射：按 D-3 保留 shell 定义，compiled 定义未搬运"
                            ),
                            target=f"word/styles.xml#{style_id}",
                        )
                    )
                continue  # D-3：shell-wins，compiled 定义不搬运
            shell_styles_root.append(source_element)
            appended.append(source_element)
            imported_ids.append(style_id)
        ctx.dst_parts["word/styles.xml"] = _serialize(shell_styles_root)
        info = {
            "used_by_imported": sorted(used),
            "closure": sorted(closure),
            "imported": imported_ids,
            "conflicts": conflicts,
            "policy": "token 对齐后 shell-wins（D-3）；docDefaults/latentStyles 保留 shell",
        }
        return info, appended, issues

    # ------------------------------------------------------------------
    # numbering（§5.3；双侧占用时 numId/abstractNumId 确定性重映射，OQ-3 编号侧落地）
    # ------------------------------------------------------------------

    @staticmethod
    def _num_ids_in_use(root: etree._Element) -> set[str]:
        return {
            el.get(_w("val"))
            for el in root.iter(_w("numId"))
            if el.get(_w("val")) and el.get(_w("val")) != "0"
        }

    def _merge_numbering(
        self,
        imported: list[etree._Element],
        appended_styles: list[etree._Element],
        ctx: _CarryContext,
    ) -> dict[str, Any]:
        shell_doc = ctx.shell.xml("word/document.xml")
        shell_used = self._num_ids_in_use(shell_doc)
        if "word/styles.xml" in ctx.shell.parts:
            shell_used |= self._num_ids_in_use(ctx.shell.xml("word/styles.xml"))
        if "word/numbering.xml" not in ctx.compiled.parts:
            return {"shell_num_ids_in_use": sorted(shell_used, key=int), "action": "none"}
        if not shell_used:
            ctx.dst_parts["word/numbering.xml"] = ctx.compiled.parts["word/numbering.xml"]
            compiled_num_ids = sorted(
                {
                    el.get(_w("numId"))
                    for el in ctx.compiled.xml("word/numbering.xml").iter(_w("num"))
                },
                key=int,
            )
            return {
                "shell_num_ids_in_use": [],
                "action": "compiled numbering.xml 整体替换 shell 默认 numbering.xml",
                "compiled_num_ids": compiled_num_ids,
            }
        # 双侧占用：compiled 侧 numId/abstractNumId 平移至 shell 最大值 +1 起
        shell_root = copy.deepcopy(ctx.shell.xml("word/numbering.xml"))
        shell_abstract_ids = {
            int(el.get(_w("abstractNumId")))
            for el in shell_root.iter(_w("abstractNum"))
            if el.get(_w("abstractNumId")) and el.get(_w("abstractNumId")).isdigit()
        }
        shell_num_ids = {
            int(el.get(_w("numId")))
            for el in shell_root.iter(_w("num"))
            if el.get(_w("numId")) and el.get(_w("numId")).isdigit()
        }
        next_abstract = max(shell_abstract_ids, default=-1) + 1
        next_num = max(shell_num_ids, default=-1) + 1
        abstract_map: dict[str, str] = {}
        num_map: dict[str, str] = {}
        new_abstracts: list[etree._Element] = []
        new_nums: list[etree._Element] = []
        for child in ctx.compiled.xml("word/numbering.xml"):
            if child.tag == _w("abstractNum"):
                old = child.get(_w("abstractNumId"))
                if old is None or not old.isdigit():
                    continue  # numberingPicBullet 等无 id 项不搬运
                element = copy.deepcopy(child)
                new = str(next_abstract)
                next_abstract += 1
                abstract_map[old] = new
                element.set(_w("abstractNumId"), new)
                new_abstracts.append(element)
            elif child.tag == _w("num"):
                old = child.get(_w("numId"))
                if old is None or not old.isdigit():
                    continue
                element = copy.deepcopy(child)
                new = str(next_num)
                next_num += 1
                num_map[old] = new
                element.set(_w("numId"), new)
                new_nums.append(element)
        for element in new_nums:
            ref = element.find(_w("abstractNumId"))
            if ref is not None and ref.get(_w("val")) in abstract_map:
                ref.set(_w("val"), abstract_map[ref.get(_w("val"))])
        # schema 顺序：全部 abstractNum 必须位于 num 之前
        first_num = shell_root.find(_w("num"))
        for element in new_abstracts:
            if first_num is not None:
                first_num.addprevious(element)
            else:
                shell_root.append(element)
        for element in new_nums:
            shell_root.append(element)
        ctx.dst_parts["word/numbering.xml"] = _serialize(shell_root)
        # 重映射 imported 节点与新增样式中的 numId 引用
        for root in (*imported, *appended_styles):
            for el in root.iter(_w("numId")):
                value = el.get(_w("val"))
                if value in num_map:
                    el.set(_w("val"), num_map[value])
        return {
            "shell_num_ids_in_use": sorted(shell_used, key=int),
            "action": "双侧 numId/abstractNumId 平移重映射后合并",
            "num_id_map": num_map,
            "abstract_num_id_map": abstract_map,
        }

    # ------------------------------------------------------------------
    # settings 白名单（D-5）
    # ------------------------------------------------------------------

    def _apply_settings_whitelist(self, ctx: _CarryContext) -> dict[str, Any]:
        if self.template is None:
            return {"applied": {}, "note": "未提供 template，settings 保留 shell 原样"}
        if "word/settings.xml" not in ctx.shell.parts:
            return {"applied": {}, "note": "shell 无 settings.xml"}
        template = self.template
        even = any(
            getattr(template.sections, key).header_footer.even != "none"
            for key in ("cover", "front_matter", "main", "back_matter")
        )
        desired = {
            "evenAndOddHeaders": even,
            "updateFields": bool(template.fields.update_on_open),
            "mirrorMargins": bool(template.page.mirror_margins),
        }
        root = copy.deepcopy(ctx.shell.xml("word/settings.xml"))
        applied: dict[str, bool] = {}
        for tag, value in desired.items():
            existing = root.find(_w(tag))
            if existing is None:
                existing = etree.Element(_w(tag))
                successors = _SETTINGS_SUCCESSORS[tag]
                anchor_el = next(
                    (root.find(_w(name)) for name in successors if root.find(_w(name)) is not None),
                    None,
                )
                if anchor_el is not None:
                    anchor_el.addprevious(existing)
                else:
                    root.append(existing)
            existing.set(_w("val"), "true" if value else "false")
            applied[tag] = value
        ctx.dst_parts["word/settings.xml"] = _serialize(root)
        return {"applied": applied, "note": "白名单字段由 template.yaml 语义写入（D-5）"}

    # ------------------------------------------------------------------
    # 合并主流程
    # ------------------------------------------------------------------

    def merge(self, compiled_path: str | Path, output_path: str | Path) -> MergeLedger:
        """执行合并并写出确定性 docx；返回搬运台账。"""
        compiled_path = Path(compiled_path)
        output_path = Path(output_path)
        shell = PackageView(self.shell_path)
        compiled = PackageView(compiled_path)

        security_notes: list[str] = []
        shell_externals = self._scan_security(shell, label="shell.docx")
        compiled_externals = self._scan_security(compiled, label="compiled.docx")
        # shell 侧的外部关系同样过策略（合并兜底层，§5.5）
        for target in shell_externals:
            self._check_external(target, "shell.docx", security_notes)
        for target in compiled_externals:
            # compiled 中被导入节点实际引用的外部 rel 在搬运时拦截；这里对全包兜底
            self._check_external(target, "compiled.docx", security_notes)

        shell_root = shell.xml("word/document.xml")
        shell_body = shell_root.find(_w("body"))
        compiled_body = compiled.xml("word/document.xml").find(_w("body"))
        anchors = self._locate_anchors(shell_body)
        body_anchor = anchors["body"].pop("paragraph")
        for slot in anchors.values():
            slot.pop("paragraph", None)

        imported, selection_info = self._select_imported_children(compiled_body)
        ctx = _CarryContext(shell, compiled)
        rid_mapping = self._remap_rid_references(imported, ctx, security_notes)
        footnotes_info = self._carry_footnotes(imported, ctx, security_notes)
        styles_info, appended_styles, style_issues = self._merge_styles(imported, ctx)
        numbering_info = self._merge_numbering(imported, appended_styles, ctx)
        settings_info = self._apply_settings_whitelist(ctx)

        # 投递：imported 节点插在 body 锚点段落之前，随后消费锚点（§5.2.3 第 5 条）。
        for element in imported:
            body_anchor.addprevious(element)
        self._consume_anchor(shell_root, body_anchor, anchors["body"]["name"])
        anchors["body"]["status"] = "consumed"
        for slot, info in anchors.items():
            if slot != "body" and info["status"] == "present":
                info["status"] = "preserved"  # toc/bibliography 锚点保留原位（投递见边界说明）

        ctx.dst_parts["word/document.xml"] = _serialize(shell_root)
        ctx.dst_parts["word/_rels/document.xml.rels"] = _serialize(ctx.dst_rels_root)
        ctx.dst_parts["[Content_Types].xml"] = _serialize(ctx.ct_root)

        self._write_deterministic_zip(self.shell_path, shell, ctx.dst_parts, output_path)

        ledger = MergeLedger(
            shell_docx=str(self.shell_path),
            compiled_docx=str(compiled_path),
            output_docx=str(output_path),
            anchors=anchors,
            selection=selection_info,
            rid_mapping=rid_mapping,
            carried_relationships=ctx.report,
            footnotes=footnotes_info,
            styles=styles_info,
            numbering=numbering_info,
            settings=settings_info,
            security={"external_allowed": security_notes},
            not_merged={
                "theme1.xml": "保留 shell（D-5）",
                "fontTable.xml": "保留 shell（D-5：reference.docx 持有基线，合并不替换）",
                "docProps": "保留 shell（D-5；论文 metadata 写入机制见 OQ-12）",
                "settings.xml": (
                    "白名单外字段保留 shell（D-5）"
                    if self.template is not None
                    else "保留 shell（未提供 template）"
                ),
            },
            issues=style_issues,
        )
        return ledger

    @staticmethod
    def _write_deterministic_zip(
        shell_path: Path,
        shell: PackageView,
        dst_parts: dict[str, bytes],
        output_path: Path,
    ) -> None:
        """确定性写出：entry 顺序 = shell 原序 + 新部件处理序；时间戳固定 DOS 纪元。"""

        def write_entry(out: zipfile.ZipFile, name: str, content: bytes) -> None:
            info = zipfile.ZipInfo(name, date_time=_ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(info, content, compresslevel=9)

        with zipfile.ZipFile(shell_path) as archive:
            original_order = archive.namelist()
        with zipfile.ZipFile(output_path, "w") as out:
            for name in original_order:
                write_entry(out, name, dst_parts.get(name, shell.parts[name]))
            for name, content in dst_parts.items():
                if name not in original_order:
                    write_entry(out, name, content)


def merge_into_shell(
    shell_path: str | Path,
    compiled_path: str | Path,
    output_path: str | Path,
    **kwargs: Any,
) -> MergeLedger:
    """便捷函数：等价于 ``PackageEditor(shell_path, **kwargs).merge(...)``。"""
    return PackageEditor(shell_path, **kwargs).merge(compiled_path, output_path)

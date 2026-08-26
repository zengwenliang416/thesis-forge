"""pandoc 可选外部 math provider（ADR-0003 §2.4）。

LaTeX → ``m:oMath`` 片段转换的可选外部链路：子进程调用用户自装的
pandoc（``markdown+tex_math_dollars`` → docx，提取 document.xml 中的
``m:oMath``）。与 ADR-0003 的边界约定一致：

- 产出**仅** ``m:oMath`` 片段；编号、书签、SEQ ``\\r`` 钉值、REF 交叉
  引用包装仍由 ``renderers/docx/equations.py:render_equation`` 承担；
- 不随包分发、不进默认编译路径——默认永远是手写子集引擎
  （``core/math.py``，离线、确定性）；本 provider 只有调用方显式传入
  ``render_equation(..., omml_provider=...)`` 时才参与；
- 可用性探测在 ``info()``（版本 + 诊断），构造与 import 阶段不抛错；
- pandoc 转换失败判据沿用 spike 实证：returncode≠0，或 stderr 出现
  "Could not convert TeX math" 警告（pandoc 把失败公式当纯文本写入而不
  报错退出），或产物中 ``m:oMath`` 数量≠1（spike
  ``spikes/phase0/omml/convert_pandoc.py`` 双重判据）。

本模块属于渲染层（OOXML 语义），允许使用 lxml；不回写 core（core 不得
包含 Word 实现细节，AGENTS.md §1.1/§1.2）。
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from docforge.core.math import MathConversionError

PANDOC_MATH_PROVIDER_NAME = "pandoc-texmath"

MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
_OMATH_TAG = f"{{{MATH_NS}}}oMath"
_PANDOC_READER_FORMAT = "markdown+tex_math_dollars"
# pandoc 转换失败时写入 docx 的纯文本降级提示（stderr 同步告警）
_COULD_NOT_CONVERT = "Could not convert TeX math"


class PandocMathUnavailableError(MathConversionError):
    """在 provider 不可用时调用其转换方法（调用方应先看 info()）。"""

    def __init__(self, diagnostics: tuple[str, ...]):
        self.diagnostics = tuple(diagnostics)
        detail = "；".join(diagnostics) if diagnostics else "原因未知"
        super().__init__(f"pandoc math provider 不可用：{detail}")


class PandocMathConversionError(MathConversionError):
    """pandoc 进程运行了但该公式未产出有效 m:oMath（含 pandoc 诊断信息）。"""

    def __init__(self, latex: str, reason: str):
        self.latex = latex
        super().__init__(f"pandoc 无法把公式转为 OMML（{reason}）：{latex[:80]}")


@dataclass(frozen=True, slots=True)
class MathProviderInfo:
    """Provider 自描述（与 bibliography.ProviderInfo 同构，避免跨层耦合）。"""

    name: str
    version: str | None
    available: bool
    diagnostics: tuple[str, ...] = ()


def _probe_pandoc_version(executable: str) -> str | None:
    """``executable --version`` 首行；缺失/失败返回 None（不抛错）。"""

    if shutil.which(executable) is None:
        return None
    try:
        completed = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    first_line = completed.stdout.splitlines()[0].strip() if completed.stdout else ""
    return first_line or None


class PandocMathProvider:
    """可选外部 provider：pandoc（texmath → 原生 OMML）。"""

    def __init__(self, *, executable: str = "pandoc", timeout: float = 60.0):
        self._executable = executable
        self._timeout = timeout

    def info(self) -> MathProviderInfo:
        diagnostics: list[str] = []
        version = _probe_pandoc_version(self._executable)
        if version is None:
            diagnostics.append(
                f"未找到可执行文件 {self._executable!r}：pandoc 不随包分发，"
                "请自行安装（https://pandoc.org）后重试"
            )
        return MathProviderInfo(
            name=PANDOC_MATH_PROVIDER_NAME,
            version=version,
            available=version is not None,
            diagnostics=tuple(diagnostics),
        )

    def convert_to_omml(self, latex: str, *, display: bool = False) -> etree._Element:
        """把 LaTeX 公式转为独立的 ``m:oMath`` 根元素。

        ``display`` 只影响 pandoc 输入写法（``$$…$$`` vs ``$…$``）；提取的
        片段同为 ``m:oMath``，块级排版（居中段落、题注编号）由
        ``render_equation`` 的包装承担。
        """

        info = self.info()
        if not info.available:
            raise PandocMathUnavailableError(info.diagnostics)
        with tempfile.TemporaryDirectory(prefix="tf-pandoc-math-") as tmp:
            work = Path(tmp)
            source = work / "input.md"
            if display:
                source.write_text(f"$$\n{latex}\n$$\n", encoding="utf-8")
            else:
                # 行内上下文（spike 同款写法）：避免 pandoc 对块首 $ 的解析歧义
                source.write_text(f"行内公式 ${latex}$ 混排。\n", encoding="utf-8")
            target = work / "output.docx"
            try:
                completed = subprocess.run(
                    [
                        self._executable,
                        "-f",
                        _PANDOC_READER_FORMAT,
                        "-t",
                        "docx",
                        "-o",
                        str(target),
                        str(source),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise PandocMathConversionError(
                    latex, f"超时（>{self._timeout}s）"
                ) from error
            except OSError as error:
                raise PandocMathUnavailableError(
                    (f"无法启动 {self._executable!r}：{error}",)
                ) from error
            if completed.returncode != 0:
                raise PandocMathConversionError(
                    latex,
                    f"exit {completed.returncode}：{completed.stderr.strip()[:300]}",
                )
            if _COULD_NOT_CONVERT in completed.stderr:
                raise PandocMathConversionError(
                    latex, completed.stderr.strip()[:300]
                )
            if not target.is_file():
                raise PandocMathConversionError(latex, "pandoc 未产出 docx")
            with zipfile.ZipFile(target) as package:
                document = etree.fromstring(package.read("word/document.xml"))
        omaths = document.findall(f".//{_OMATH_TAG}")
        if len(omaths) != 1:
            raise PandocMathConversionError(
                latex, f"期望恰好 1 个 m:oMath，实际 {len(omaths)}"
            )
        return omaths[0]

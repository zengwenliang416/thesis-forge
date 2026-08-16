#!/usr/bin/env python3
"""Phase 0 字段实证：构建「生成态」样本 DOCX（不经 office finalizer 刷新）。

通过注入 no-op document_refresher 绕开 build_service 的 LibreOffice finalizer，
保留渲染器生成的原始字段状态（TOC 无 cached 条目、fldChar dirty、
SEQ \\r 钉值 + cached result、PAGE/NUMPAGES cached "1"、updateFields=true）。

样本（templates/schools 两个模板各一份）：
    samples/complete-thesis-example.docx
        examples/complete-thesis + example-university/2026.yaml
        （TOC、图/表/公式 SEQ、交叉引用 REF、roman+decimal 页码、脚注）
    samples/minimal-hut.docx
        最小构造样本（标题 + TOC + 一个图题注 + 一个 REF）+ HUT master-2026

用法：
    .venv/bin/python spikes/phase0/fields/build_samples.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

SPIKE_DIR = Path(__file__).resolve().parent
ROOT = SPIKE_DIR.parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from thesis_forge.application.services import (
    ApplicationDependencies,
    build_service,
)

COMPLETE_SOURCE = ROOT / "examples" / "complete-thesis" / "thesis.md"
COMPLETE_IMAGE = (
    ROOT / "examples" / "complete-thesis" / "images" / "acceptance-architecture.png"
)
EXAMPLE_TEMPLATE = ROOT / "templates" / "schools" / "example-university" / "2026.yaml"
HUT_TEMPLATE = (
    ROOT / "templates" / "schools" / "hunan-university-of-technology" / "master-2026.yaml"
)

SAMPLES_DIR = SPIKE_DIR / "samples"

MINIMAL_SOURCE = """---
document:
  type: master_thesis
  language: zh-CN
university:
  name: "湖南工业大学"
  name_en: "Hunan University of Technology"
thesis:
  title: "字段生命周期最小样本"
  title_en: "Minimal Field Lifecycle Sample"
author:
  name: "ThesisForge"
  student_id: "0000000000"
advisor:
  name: "指导教师"
  title: "教授"
dates:
  submitted: "2026-05-20"
render:
  template_id: "hut-master-2026"
---

# 绪论 {#chap:intro}

最小样本仅包含一个图题注与一个交叉引用。系统结构见 @fig:arch。

::: figure {#fig:arch}
src: "./minimal-image.png"
caption: "最小样本示意图"
width: "60%"
:::
"""


class _NoRefresh:
    """no-op DocumentRefresher：让 build_service 跳过 office finalizer。"""

    def refresh(self, path: str | Path) -> bool:
        return False


def _build(source: Path, template: Path, output: Path) -> None:
    dependencies = ApplicationDependencies(document_refresher=_NoRefresh())
    result = build_service(
        source,
        output,
        template_path=template,
        dependencies=dependencies,
    )
    errors = [issue for issue in result.issues if issue.severity == "error"]
    if errors:
        raise RuntimeError(f"构建 {output.name} 出现校验错误: {errors}")
    print(f"built {output.relative_to(ROOT)} ({output.stat().st_size} bytes)")


def main() -> int:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    _build(
        COMPLETE_SOURCE,
        EXAMPLE_TEMPLATE,
        SAMPLES_DIR / "complete-thesis-example.docx",
    )

    minimal_md = SAMPLES_DIR / "minimal-source.md"
    minimal_md.write_text(MINIMAL_SOURCE, encoding="utf-8")
    shutil.copyfile(COMPLETE_IMAGE, SAMPLES_DIR / "minimal-image.png")
    _build(minimal_md, HUT_TEMPLATE, SAMPLES_DIR / "minimal-hut.docx")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""CitationProvider 接口与 provider 注册表（ADR-0004）。

bibliography 子系统对外只暴露 provider 抽象：输入 BibTeX 条目集合与引用
序列（records + ordinals/locator），输出正文引用标记与文后参考文献条目
文本；不暴露任何 provider 专有对象（R-011 预防）。

内建手写 GB/T 7714-2025 引擎注册为默认 provider（离线、确定性、无运行时
依赖）。未来的 pandoc citeproc 外部 provider 按同一协议实现：

- **进程边界**：外部 provider 以子进程调用可执行文件，输入走 CSL JSON
  通道，输出解析为纯文本条目；协议方法签名不变。
- **版本探测**：构造期用 `probe_executable_version` 探测可执行文件与
  版本，写入 `ProviderInfo.version`（供 `doctor` 命令诊断）。
- **不可用诊断**：不可用时返回 `ProviderInfo(available=False,
  diagnostics=(...))` 说明原因与安装提示，而不是在 import 或编译中途
  抛错；调用方据此回退默认 provider 或给出结构化诊断。
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .engine import BibliographyRecord, UnsupportedCitationStyleError
from .formatter import Gbt7714Formatter

DEFAULT_CITATION_STYLE = "GB-T-7714-2025"
BUILTIN_PROVIDER_NAME = "builtin-gbt7714"

# 文档/模板中允许出现的样式名（大小写不敏感）→ 规范样式 id。
_STYLE_ALIASES: dict[str, str] = {
    "gb-t-7714-2025": DEFAULT_CITATION_STYLE,
    "gbt7714": DEFAULT_CITATION_STYLE,
    "gbt7714-2025": DEFAULT_CITATION_STYLE,
    "gbt7714-2025-numeric": DEFAULT_CITATION_STYLE,
}


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    """Provider 自描述：名称、支持的样式、探测到的版本与可用性诊断。"""

    name: str
    styles: tuple[str, ...]
    version: str | None
    available: bool
    diagnostics: tuple[str, ...] = ()


@runtime_checkable
class CitationProvider(Protocol):
    """引用渲染提供者：正文引用标记 + 文后参考文献条目（ADR-0004 §2.1）。"""

    def info(self) -> ProviderInfo: ...

    def format_citation(
        self,
        records: Sequence[BibliographyRecord],
        ordinals: Sequence[int],
        *,
        locator: str | None = None,
    ) -> str: ...

    def format_bibliography(
        self,
        records: Sequence[BibliographyRecord],
        ordinals: Sequence[int],
    ) -> tuple[str, ...]: ...


def probe_executable_version(executable: str) -> str | None:
    """进程边界版本探测：返回 ``executable --version`` 首行，失败返回 None。

    供外部 provider（如 pandoc）构造 :class:`ProviderInfo` 使用；内建
    provider 不调用本函数。
    """

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


class BuiltinGbt7714Provider:
    """内建手写 GB/T 7714-2025 顺序编码制 provider（默认，离线确定性）。"""

    def __init__(self, formatter: Gbt7714Formatter | None = None):
        self._formatter = formatter or Gbt7714Formatter()

    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name=BUILTIN_PROVIDER_NAME,
            styles=supported_citation_styles(),
            version=None,
            available=True,
        )

    def format_citation(
        self,
        records: Sequence[BibliographyRecord],
        ordinals: Sequence[int],
        *,
        locator: str | None = None,
    ) -> str:
        return self._formatter.format_citation(records, ordinals, locator=locator)

    def format_bibliography(
        self,
        records: Sequence[BibliographyRecord],
        ordinals: Sequence[int],
    ) -> tuple[str, ...]:
        return self._formatter.format_bibliography(records, ordinals)


def normalize_citation_style(style: str) -> str | None:
    """把用户配置的样式名规范化为内置样式 id；无法识别时返回 None。"""

    return _STYLE_ALIASES.get(style.strip().lower())


def supported_citation_styles() -> tuple[str, ...]:
    return (DEFAULT_CITATION_STYLE,)


_PROVIDER_FACTORIES: dict[str, Callable[[], CitationProvider]] = {
    DEFAULT_CITATION_STYLE: BuiltinGbt7714Provider,
}

# 显式 provider 选择（ADR-0004 §2.4）：pandoc citeproc 为可选外部 provider，
# 内建引擎永远是默认与唯一离线路径。
_EXPLICIT_PROVIDERS: dict[str, str] = {
    "builtin": BUILTIN_PROVIDER_NAME,
    BUILTIN_PROVIDER_NAME: BUILTIN_PROVIDER_NAME,
    "pandoc": "pandoc-citeproc",
    "pandoc-citeproc": "pandoc-citeproc",
}


def resolve_citation_provider(
    style: str | None, *, provider: str | None = None
) -> CitationProvider:
    """按样式名选择 provider；None 表示默认。未知样式抛出结构化错误（D-07）。

    ``provider`` 显式指定引擎（``builtin`` / ``pandoc``）；显式选择 pandoc
    时样式仍须是已支持样式，pandoc 未安装不在此抛错——由调用方读
    ``info()`` 诊断并决定回退（ADR-0004 §2.4）。
    """

    if provider is not None:
        resolved = _EXPLICIT_PROVIDERS.get(provider.strip().lower())
        if resolved is None:
            known = ", ".join(sorted(set(_EXPLICIT_PROVIDERS)))
            raise ValueError(
                f"未知 citation provider {provider!r}（允许 {known}）"
            )
        if resolved == "pandoc-citeproc":
            from .pandoc_provider import PandocCiteprocProvider

            canonical = (
                DEFAULT_CITATION_STYLE if style is None else normalize_citation_style(style)
            )
            if canonical is None:
                raise UnsupportedCitationStyleError(style or "", supported_citation_styles())
            return PandocCiteprocProvider()
        return BuiltinGbt7714Provider()
    canonical = DEFAULT_CITATION_STYLE if style is None else normalize_citation_style(style)
    if canonical is None:
        raise UnsupportedCitationStyleError(style or "", supported_citation_styles())
    return _PROVIDER_FACTORIES[canonical]()

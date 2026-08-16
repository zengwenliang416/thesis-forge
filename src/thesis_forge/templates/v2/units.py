"""Template Package v2 长度单位解析（SCHEMA §2）。

词法规则确定性、无环境依赖：禁止裸数字、符号、科学计数法与内部空格；
单位上下文矩阵见 §2.3，由 `LengthContext` 表达。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

ABSOLUTE_UNITS = frozenset({"mm", "cm", "pt", "in"})
ALL_UNITS = frozenset({"mm", "cm", "pt", "in", "em", "%"})

LENGTH_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)(mm|cm|pt|in|em|%)")

_PT_PER_IN = Decimal(72)
_PT_PER_CM = _PT_PER_IN / Decimal("2.54")
_PT_PER_MM = _PT_PER_IN / Decimal("25.4")


class LengthParseError(ValueError):
    """长度词法/上下文校验失败（lint 层映射为 invalid-template）。"""


@dataclass(frozen=True, slots=True)
class Length:
    value: Decimal
    unit: str

    def __str__(self) -> str:
        number = format(self.value, "f")
        if "." in number:
            number = number.rstrip("0").rstrip(".")
        return f"{number or '0'}{self.unit}"

    def to_points(self) -> Decimal:
        """绝对单位换算为磅（pt）；em/% 无绝对值，调用方负责上下文求值。"""
        if self.unit == "pt":
            return self.value
        if self.unit == "in":
            return self.value * _PT_PER_IN
        if self.unit == "cm":
            return self.value * _PT_PER_CM
        if self.unit == "mm":
            return self.value * _PT_PER_MM
        raise LengthParseError(f"相对单位 {self.unit} 不能换算为绝对磅值")

    def to_twips(self) -> int:
        """绝对单位换算为 twips，ROUND_HALF_UP 取整（与 Word 存储一致）。"""
        return int((self.to_points() * 20).quantize(0, rounding=ROUND_HALF_UP))


@dataclass(frozen=True, slots=True)
class LengthContext:
    """§2.3 单位上下文矩阵中的一行。"""

    allowed_units: frozenset[str]
    positive: bool = False
    allow_none: bool = False
    max_percent: Decimal | None = Decimal(100)
    min_points: Decimal | None = None
    max_points: Decimal | None = None

    def describe_units(self) -> str:
        return "/".join(sorted(self.allowed_units))


# §2.3 上下文实例
CTX_PAGE_GEOMETRY = LengthContext(ABSOLUTE_UNITS)
CTX_BORDER_WIDTH = LengthContext(
    ABSOLUTE_UNITS,
    positive=True,
    allow_none=True,
    min_points=Decimal("0.25"),
    max_points=Decimal(12),
)
CTX_FONT_SIZE = LengthContext(frozenset({"pt"}), positive=True)
CTX_FONT_SIZE_RELATIVE = LengthContext(frozenset({"pt", "em"}), positive=True)
CTX_INDENT = LengthContext(ABSOLUTE_UNITS | {"em"})
CTX_FIXED_LINE_SPACING = LengthContext(ABSOLUTE_UNITS | {"em"}, positive=True)
CTX_PARENT_WIDTH = LengthContext(ABSOLUTE_UNITS | {"%"}, positive=True)
CTX_OVERFLOW_THRESHOLD = LengthContext(
    ABSOLUTE_UNITS | {"%"}, positive=True, max_percent=None
)
CTX_IMAGE_HEIGHT = LengthContext(ABSOLUTE_UNITS, positive=True)
CTX_COLUMN_SPACING = LengthContext(ABSOLUTE_UNITS)


def parse_length(
    raw: Any,
    ctx: LengthContext,
    *,
    field_path: str = "",
) -> Length | None:
    """按 §2.2 算法解析长度；`allow_none` 上下文中字面量 ``none`` 返回 None。

    任何失败抛 `LengthParseError`，消息注明字段路径与允许单位集。
    """
    where = f"{field_path}: " if field_path else ""
    if not isinstance(raw, str):
        raise LengthParseError(f"{where}长度必须是带单位的字符串，禁止裸数字等其他类型")
    text = raw.strip()
    if ctx.allow_none and text == "none":
        return None
    match = LENGTH_RE.fullmatch(text)
    if match is None:
        raise LengthParseError(
            f"{where}长度格式无效：{raw!r}（允许 {ctx.describe_units()}，"
            "不接受符号/科学计数法/内部空格/裸数字）"
        )
    value = Decimal(match.group(1))
    unit = match.group(2)
    if unit not in ctx.allowed_units:
        raise LengthParseError(
            f"{where}单位 {unit} 不允许用于该字段（允许 {ctx.describe_units()}）"
        )
    if ctx.positive and value <= 0:
        raise LengthParseError(f"{where}长度必须大于 0：{raw!r}")
    if unit == "%" and ctx.max_percent is not None and value > ctx.max_percent:
        raise LengthParseError(f"{where}比例不得超过 {ctx.max_percent}%：{raw!r}")
    length = Length(value=value, unit=unit)
    if unit in ABSOLUTE_UNITS and (ctx.min_points is not None or ctx.max_points is not None):
        points = length.to_points()
        if ctx.min_points is not None and points < ctx.min_points:
            raise LengthParseError(f"{where}线宽不得低于 {ctx.min_points}pt：{raw!r}")
        if ctx.max_points is not None and points > ctx.max_points:
            raise LengthParseError(f"{where}线宽不得高于 {ctx.max_points}pt：{raw!r}")
    return length

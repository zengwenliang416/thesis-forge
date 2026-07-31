from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, TypeAlias


class MathConversionError(ValueError):
    pass


class MathSyntaxError(MathConversionError):
    pass


class UnsupportedMathError(MathConversionError):
    def __init__(self, command: str):
        self.command = command
        super().__init__(f"Unsupported LaTeX command: {command}")


@dataclass(frozen=True, slots=True)
class MathLiteral:
    value: str


@dataclass(frozen=True, slots=True)
class MathSequence:
    items: tuple[MathNode, ...]


@dataclass(frozen=True, slots=True)
class MathFraction:
    numerator: MathNode
    denominator: MathNode


@dataclass(frozen=True, slots=True)
class MathRadical:
    radicand: MathNode


@dataclass(frozen=True, slots=True)
class MathScript:
    base: MathNode
    subscript: MathNode | None = None
    superscript: MathNode | None = None


@dataclass(frozen=True, slots=True)
class MathNary:
    operator: str
    lower: MathNode | None = None
    upper: MathNode | None = None


@dataclass(frozen=True, slots=True)
class MathFunction:
    name: str
    argument: MathNode


@dataclass(frozen=True, slots=True)
class MathAccent:
    kind: Literal["hat", "bar"]
    base: MathNode


MathNode: TypeAlias = (
    MathLiteral
    | MathSequence
    | MathFraction
    | MathRadical
    | MathScript
    | MathNary
    | MathFunction
    | MathAccent
)


@dataclass(frozen=True, slots=True)
class MathExpression:
    root: MathNode


class MathConverter(Protocol):
    def convert(self, latex: str) -> MathExpression: ...


GREEK_SYMBOLS = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "theta": "θ",
    "lambda": "λ",
    "mu": "μ",
    "pi": "π",
    "rho": "ρ",
    "sigma": "σ",
    "phi": "φ",
    "omega": "ω",
    "Gamma": "Γ",
    "Delta": "Δ",
    "Theta": "Θ",
    "Lambda": "Λ",
    "Pi": "Π",
    "Sigma": "Σ",
    "Phi": "Φ",
    "Omega": "Ω",
}
OPERATOR_SYMBOLS = {
    "cdot": "·",
    "times": "×",
    "le": "≤",
    "leq": "≤",
    "ge": "≥",
    "geq": "≥",
    "neq": "≠",
    "infty": "∞",
    "pm": "±",
}
FUNCTION_NAMES = {"sin", "cos", "tan", "log", "ln", "exp", "max", "min"}


class LatexMathConverter:
    """Convert the documented deterministic LaTeX subset to a semantic math tree."""

    def convert(self, latex: str) -> MathExpression:
        parser = _LatexParser(latex.strip())
        root = parser.parse_sequence()
        if not parser.at_end:
            raise MathSyntaxError(f"Unexpected token at offset {parser.position}")
        if not root.items:
            raise MathSyntaxError("Equation is empty")
        return MathExpression(root=root)


class _LatexParser:
    def __init__(self, source: str):
        self.source = source
        self.position = 0

    @property
    def at_end(self) -> bool:
        return self.position >= len(self.source)

    def parse_sequence(self, stop: str | None = None) -> MathSequence:
        items: list[MathNode] = []
        while not self.at_end:
            self._skip_whitespace()
            if self.at_end:
                break
            if stop is not None and self.source[self.position] == stop:
                self.position += 1
                return MathSequence(tuple(items))
            if self.source[self.position] == "}":
                raise MathSyntaxError(f"Unexpected '}}' at offset {self.position}")
            items.append(self._parse_atom_with_scripts())
        if stop is not None:
            raise MathSyntaxError(f"Missing closing {stop!r}")
        return MathSequence(tuple(items))

    def _parse_atom_with_scripts(self) -> MathNode:
        node = self._parse_atom()
        subscript = None
        superscript = None
        while True:
            self._skip_whitespace()
            if self.at_end or self.source[self.position] not in "_^":
                break
            marker = self.source[self.position]
            self.position += 1
            value = self._parse_script_value()
            if marker == "_":
                if subscript is not None:
                    raise MathSyntaxError("Duplicate subscript")
                subscript = value
            else:
                if superscript is not None:
                    raise MathSyntaxError("Duplicate superscript")
                superscript = value

        if isinstance(node, MathNary):
            return MathNary(
                operator=node.operator,
                lower=subscript,
                upper=superscript,
            )
        if subscript is not None or superscript is not None:
            return MathScript(
                base=node,
                subscript=subscript,
                superscript=superscript,
            )
        return node

    def _parse_script_value(self) -> MathNode:
        self._skip_whitespace()
        if self.at_end:
            raise MathSyntaxError("Missing script value")
        if self.source[self.position] == "{":
            return self._parse_group()
        return self._parse_atom()

    def _parse_atom(self) -> MathNode:
        self._skip_whitespace()
        if self.at_end:
            raise MathSyntaxError("Expected math atom")
        char = self.source[self.position]
        if char == "{":
            return self._parse_group()
        if char == "\\":
            return self._parse_command()
        if char in "_^}":
            raise MathSyntaxError(f"Unexpected {char!r} at offset {self.position}")
        self.position += 1
        return MathLiteral(char)

    def _parse_group(self) -> MathNode:
        if self.source[self.position] != "{":
            raise MathSyntaxError(f"Expected '{{' at offset {self.position}")
        self.position += 1
        return self.parse_sequence(stop="}")

    def _parse_required_group(self, command: str) -> MathNode:
        self._skip_whitespace()
        if self.at_end or self.source[self.position] != "{":
            raise MathSyntaxError(f"\\{command} requires a braced argument")
        return self._parse_group()

    def _parse_command(self) -> MathNode:
        start = self.position
        self.position += 1
        command_start = self.position
        while not self.at_end and self.source[self.position].isalpha():
            self.position += 1
        command = self.source[command_start : self.position]
        if not command:
            if self.at_end:
                raise MathSyntaxError("Trailing backslash")
            escaped = self.source[self.position]
            self.position += 1
            if escaped in "{}_^\\":
                return MathLiteral(escaped)
            raise UnsupportedMathError(self.source[start : self.position])

        if command == "frac":
            return MathFraction(
                numerator=self._parse_required_group(command),
                denominator=self._parse_required_group(command),
            )
        if command == "sqrt":
            return MathRadical(self._parse_required_group(command))
        if command == "sum":
            return MathNary("∑")
        if command in {"hat", "bar"}:
            self._skip_whitespace()
            base = (
                self._parse_group()
                if not self.at_end and self.source[self.position] == "{"
                else self._parse_atom()
            )
            return MathAccent(command, base)
        if command in FUNCTION_NAMES:
            self._skip_whitespace()
            argument = self._parse_atom_with_scripts()
            return MathFunction(command, argument)
        if command in GREEK_SYMBOLS:
            return MathLiteral(GREEK_SYMBOLS[command])
        if command in OPERATOR_SYMBOLS:
            return MathLiteral(OPERATOR_SYMBOLS[command])
        raise UnsupportedMathError(f"\\{command}")

    def _skip_whitespace(self) -> None:
        while not self.at_end and self.source[self.position].isspace():
            self.position += 1

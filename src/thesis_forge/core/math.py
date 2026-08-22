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
class MathLimitFunction:
    """Limit-style operator such as ``\\lim`` with optional lower/upper limits."""

    name: str
    lower: MathNode | None = None
    upper: MathNode | None = None


@dataclass(frozen=True, slots=True)
class MathFunction:
    name: str
    argument: MathNode


@dataclass(frozen=True, slots=True)
class MathAccent:
    kind: Literal["hat", "bar", "vec", "dot", "ddot", "tilde"]
    base: MathNode


@dataclass(frozen=True, slots=True)
class MathDelimiter:
    """``\\left ... \\right`` auto-sized delimiters; ``None`` marks an invisible
    delimiter (``.``)."""

    left: str | None
    right: str | None
    body: MathNode


@dataclass(frozen=True, slots=True)
class MathMatrix:
    """Matrix-like environment (matrix/pmatrix/bmatrix/vmatrix/cases)."""

    rows: tuple[tuple[MathNode, ...], ...]
    left: str | None = None
    right: str | None = None
    column_alignment: Literal["center", "left"] = "center"


@dataclass(frozen=True, slots=True)
class MathEquationArray:
    """Multi-row aligned derivation; each row is a tuple of cells split at ``&``."""

    rows: tuple[tuple[MathNode, ...], ...]


@dataclass(frozen=True, slots=True)
class MathBinomial:
    top: MathNode
    bottom: MathNode


@dataclass(frozen=True, slots=True)
class MathTextRun:
    """Upright text inside math: ``\\text`` (normal text) or ``\\mathrm``."""

    text: str
    style: Literal["text", "mathrm"]


MathNode: TypeAlias = (
    MathLiteral
    | MathSequence
    | MathFraction
    | MathRadical
    | MathScript
    | MathNary
    | MathLimitFunction
    | MathFunction
    | MathAccent
    | MathDelimiter
    | MathMatrix
    | MathEquationArray
    | MathBinomial
    | MathTextRun
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
    "zeta": "ζ",
    "eta": "η",
    "theta": "θ",
    "iota": "ι",
    "kappa": "κ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "xi": "ξ",
    "pi": "π",
    "rho": "ρ",
    "sigma": "σ",
    "tau": "τ",
    "upsilon": "υ",
    "phi": "φ",
    "chi": "χ",
    "psi": "ψ",
    "omega": "ω",
    "varepsilon": "ε",
    "vartheta": "ϑ",
    "varpi": "ϖ",
    "varrho": "ϱ",
    "varsigma": "ς",
    "varphi": "φ",
    "Gamma": "Γ",
    "Delta": "Δ",
    "Theta": "Θ",
    "Lambda": "Λ",
    "Xi": "Ξ",
    "Pi": "Π",
    "Sigma": "Σ",
    "Upsilon": "Υ",
    "Phi": "Φ",
    "Psi": "Ψ",
    "Omega": "Ω",
}
OPERATOR_SYMBOLS = {
    "cdot": "·",
    "times": "×",
    "div": "÷",
    "pm": "±",
    "mp": "∓",
    "le": "≤",
    "leq": "≤",
    "ge": "≥",
    "geq": "≥",
    "neq": "≠",
    "approx": "≈",
    "sim": "∼",
    "simeq": "≃",
    "cong": "≅",
    "equiv": "≡",
    "propto": "∝",
    "ll": "≪",
    "gg": "≫",
    "in": "∈",
    "ni": "∋",
    "notin": "∉",
    "subset": "⊂",
    "supset": "⊃",
    "subseteq": "⊆",
    "supseteq": "⊇",
    "cup": "∪",
    "cap": "∩",
    "setminus": "∖",
    "emptyset": "∅",
    "forall": "∀",
    "exists": "∃",
    "nabla": "∇",
    "partial": "∂",
    "infty": "∞",
    "to": "→",
    "gets": "←",
    "rightarrow": "→",
    "leftarrow": "←",
    "longrightarrow": "⟶",
    "longleftarrow": "⟵",
    "Rightarrow": "⇒",
    "Leftarrow": "⇐",
    "Leftrightarrow": "⇔",
    "mapsto": "↦",
    "land": "∧",
    "wedge": "∧",
    "lor": "∨",
    "vee": "∨",
    "neg": "¬",
    "lnot": "¬",
    "circ": "∘",
    "bullet": "∙",
    "oplus": "⊕",
    "otimes": "⊗",
    "perp": "⊥",
    "parallel": "∥",
    "mid": "∣",
    "asymp": "≍",
    "vdash": "⊢",
    "models": "⊨",
    "ldots": "…",
    "cdots": "⋯",
    "ddots": "⋱",
}
NARY_OPERATORS = {
    "sum": "∑",
    "prod": "∏",
    "int": "∫",
    "oint": "∮",
    "bigcup": "⋃",
    "bigcap": "⋂",
}
LIMIT_FUNCTIONS = {
    "lim": "lim",
    "liminf": "lim inf",
    "limsup": "lim sup",
}
FUNCTION_NAMES = {
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "arcsin",
    "arccos",
    "arctan",
    "sinh",
    "cosh",
    "tanh",
    "coth",
    "log",
    "ln",
    "lg",
    "exp",
    "max",
    "min",
    "sup",
    "inf",
    "det",
    "dim",
    "ker",
    "deg",
    "arg",
    "gcd",
    "hom",
    "Pr",
}
ACCENT_COMMANDS = {"hat", "bar", "vec", "dot", "ddot", "tilde"}
MATRIX_ENVIRONMENTS = {
    "matrix": (None, None),
    "pmatrix": ("(", ")"),
    "bmatrix": ("[", "]"),
    "vmatrix": ("|", "|"),
    "cases": ("{", None),
}
SUPPORTED_ENVIRONMENTS = frozenset({*MATRIX_ENVIRONMENTS, "aligned"})
_DELIMITER_COMMANDS = {
    "langle": "⟨",
    "rangle": "⟩",
    "lbrace": "{",
    "rbrace": "}",
    "vert": "|",
    "Vert": "‖",
}
# Function arguments stop at these binary/relation tokens (so groups like
# ``p(x_i)`` stay inside ``\log p(x_i)`` instead of floating outside).
_ARGUMENT_STOP_CHARS = frozenset("+-=<>,;")
_ARGUMENT_BOUNDARY_COMMANDS = frozenset({"begin", "end", "right"})


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


def preflight_latex(latex: str) -> MathExpression:
    """Parse a formula before compilation so render-time failures become validation issues."""

    return LatexMathConverter().convert(latex)


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
        if isinstance(node, MathLimitFunction):
            return MathLimitFunction(
                name=node.name,
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

    def _parse_raw_group(self, command: str) -> str:
        """Read a braced group as raw text (no math parsing), brace-balanced."""
        self._skip_whitespace()
        if self.at_end or self.source[self.position] != "{":
            raise MathSyntaxError(f"\\{command} requires a braced argument")
        self.position += 1
        start = self.position
        depth = 1
        while not self.at_end:
            char = self.source[self.position]
            if char == "\\":
                self.position += 2
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    text = self.source[start : self.position]
                    self.position += 1
                    return text
            self.position += 1
        raise MathSyntaxError("Missing closing '}'")

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
            if escaped == "\\":
                raise MathSyntaxError(
                    "Bare \\\\ line break is only supported inside "
                    "matrix/cases/aligned environments"
                )
            if escaped in "{}_^":
                return MathLiteral(escaped)
            raise UnsupportedMathError(self.source[start : self.position])

        if command == "frac":
            return MathFraction(
                numerator=self._parse_required_group(command),
                denominator=self._parse_required_group(command),
            )
        if command == "sqrt":
            return MathRadical(self._parse_required_group(command))
        if command == "binom":
            return MathBinomial(
                top=self._parse_required_group(command),
                bottom=self._parse_required_group(command),
            )
        if command in NARY_OPERATORS:
            return MathNary(NARY_OPERATORS[command])
        if command in LIMIT_FUNCTIONS:
            return MathLimitFunction(LIMIT_FUNCTIONS[command])
        if command == "begin":
            return self._parse_environment()
        if command == "end":
            raise MathSyntaxError("\\end without matching \\begin")
        if command == "left":
            return self._parse_delimited()
        if command == "right":
            raise MathSyntaxError("\\right without matching \\left")
        if command in {"text", "mathrm"}:
            return MathTextRun(
                text=self._parse_raw_group(command),
                style="text" if command == "text" else "mathrm",
            )
        if command in ACCENT_COMMANDS:
            self._skip_whitespace()
            base = (
                self._parse_group()
                if not self.at_end and self.source[self.position] == "{"
                else self._parse_atom()
            )
            return MathAccent(command, base)
        if command in FUNCTION_NAMES:
            return self._parse_function(command)
        if command in GREEK_SYMBOLS:
            return MathLiteral(GREEK_SYMBOLS[command])
        if command in OPERATOR_SYMBOLS:
            return MathLiteral(OPERATOR_SYMBOLS[command])
        raise UnsupportedMathError(f"\\{command}")

    def _parse_function(self, name: str) -> MathNode:
        # Function names may carry scripts directly (\sin^2, \log_2, \max_a);
        # the scripts attach to the whole function application.
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
        argument = self._parse_function_argument()
        node = MathFunction(name, argument)
        if subscript is not None or superscript is not None:
            return MathScript(base=node, subscript=subscript, superscript=superscript)
        return node

    def _parse_function_argument(self) -> MathNode:
        """Consume the argument run of a function (atoms until a binary/relation
        operator or a structural boundary), keeping groups like ``p(x_i)`` inside
        the function instead of letting the parentheses float outside."""
        items: list[MathNode] = []
        depth = 0
        while True:
            self._skip_whitespace()
            if self.at_end:
                break
            char = self.source[self.position]
            if char in "}&":
                break
            if depth == 0 and char in _ARGUMENT_STOP_CHARS:
                break
            if depth == 0 and char in ")]":
                break
            if char == "\\" and self._is_argument_boundary_command():
                break
            if char in "([":
                depth += 1
            elif char in ")]":
                depth -= 1
            items.append(self._parse_atom_with_scripts())
        if not items:
            raise MathSyntaxError("Expected math atom")
        if len(items) == 1:
            return items[0]
        return MathSequence(tuple(items))

    def _is_argument_boundary_command(self) -> bool:
        if self.source.startswith("\\\\", self.position):
            return True
        name = self._peek_command_name()
        if name is None:
            return False
        return (
            name in OPERATOR_SYMBOLS
            or name in FUNCTION_NAMES
            or name in LIMIT_FUNCTIONS
            or name in NARY_OPERATORS
            or name in _ARGUMENT_BOUNDARY_COMMANDS
        )

    def _peek_command_name(self) -> str | None:
        position = self.position + 1
        start = position
        while position < len(self.source) and self.source[position].isalpha():
            position += 1
        if position == start:
            return None
        return self.source[start:position]

    def _at_command(self, name: str) -> bool:
        if not self.source.startswith(f"\\{name}", self.position):
            return False
        following = self.position + len(name) + 1
        return following >= len(self.source) or not self.source[following].isalpha()

    def _parse_environment(self) -> MathNode:
        name = self._parse_raw_group("begin")
        if name not in SUPPORTED_ENVIRONMENTS:
            raise UnsupportedMathError(f"\\begin{{{name}}}")
        rows: list[tuple[MathNode, ...]] = []
        cells: list[MathNode] = []
        while True:
            cells.append(self._parse_environment_cell())
            if self.at_end:
                raise MathSyntaxError(f"Missing \\end{{{name}}}")
            if self.source.startswith("\\\\", self.position):
                self.position += 2
                rows.append(tuple(cells))
                cells = []
                continue
            if self.source[self.position] == "&":
                self.position += 1
                continue
            if self._at_command("end"):
                break
            raise MathSyntaxError(
                f"Unexpected token in {name} environment at offset {self.position}"
            )
        rows.append(tuple(cells))
        self.position += len("\\end")
        end_name = self._parse_raw_group("end")
        if end_name != name:
            raise MathSyntaxError(f"\\end{{{end_name}}} does not match \\begin{{{name}}}")
        if name == "aligned":
            return MathEquationArray(rows=tuple(rows))
        left, right = MATRIX_ENVIRONMENTS[name]
        return MathMatrix(
            rows=tuple(rows),
            left=left,
            right=right,
            column_alignment="left" if name == "cases" else "center",
        )

    def _parse_environment_cell(self) -> MathNode:
        items: list[MathNode] = []
        while not self.at_end:
            self._skip_whitespace()
            if self.at_end:
                break
            char = self.source[self.position]
            if char == "&" or self.source.startswith("\\\\", self.position):
                break
            if char == "\\" and self._at_command("end"):
                break
            if char == "}":
                raise MathSyntaxError(f"Unexpected '}}' at offset {self.position}")
            items.append(self._parse_atom_with_scripts())
        if not items:
            return MathSequence(())
        if len(items) == 1:
            return items[0]
        return MathSequence(tuple(items))

    def _parse_delimited(self) -> MathNode:
        left = self._parse_delimiter_value("left")
        items: list[MathNode] = []
        while True:
            self._skip_whitespace()
            if self.at_end:
                raise MathSyntaxError("Missing \\right")
            if self._at_command("right"):
                break
            items.append(self._parse_atom_with_scripts())
        self.position += len("\\right")
        right = self._parse_delimiter_value("right")
        if not items:
            body: MathNode = MathSequence(())
        elif len(items) == 1:
            body = items[0]
        else:
            body = MathSequence(tuple(items))
        return MathDelimiter(left=left, right=right, body=body)

    def _parse_delimiter_value(self, command: str) -> str | None:
        self._skip_whitespace()
        if self.at_end:
            raise MathSyntaxError(f"\\{command} requires a delimiter")
        char = self.source[self.position]
        if char == "\\":
            self.position += 1
            name_start = self.position
            while not self.at_end and self.source[self.position].isalpha():
                self.position += 1
            if self.position == name_start:
                escaped = self.source[self.position]
                self.position += 1
                if escaped in "|{}":
                    return {"|": "‖", "{": "{", "}": "}"}[escaped]
                raise UnsupportedMathError(self.source[name_start - 1 : self.position])
            name = self.source[name_start : self.position]
            if name in _DELIMITER_COMMANDS:
                return _DELIMITER_COMMANDS[name]
            raise UnsupportedMathError(f"\\{name}")
        self.position += 1
        if char == ".":
            return None
        return char

    def _skip_whitespace(self) -> None:
        while not self.at_end and self.source[self.position].isspace():
            self.position += 1

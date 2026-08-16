# ThesisForge Math Spec v0.2

ThesisForge keeps block-equation source as LaTeX in the Domain Model. The DOCX
pipeline converts that source through a renderer-neutral `MathConverter`
contract:

```text
LaTeX source -> MathConverter -> MathExpression -> DOCX OMML renderer
```

`MathExpression` contains semantic math nodes and never contains python-docx,
lxml or OOXML objects. A different converter can replace the V1 implementation
without changing Parser, Domain Model, Compiler or the OMML renderer contract.

The subset below is defined against the 50-formula corpus in
`spikes/phase0/omml/corpus/formulas.yaml` (ADR-0003); the built-in
`LatexMathConverter` covers 49/50 of it.

## V1 Supported Subset

- identifiers, digits and ordinary Unicode characters;
- `+`, `-`, `=`, `/`, parentheses, brackets, commas, periods and other
  literal punctuation;
- braced groups such as `{a+b}`;
- subscript and superscript: `x_i`, `x^2`, `x_i^2`, including scripts attached
  to function names (`\sin^2 \theta`, `\log_2 n`);
- fractions: `\frac{a}{b}`; binomials: `\binom{n}{k}` (rendered as a bar-less
  fraction wrapped in parentheses);
- square roots: `\sqrt{x}`;
- N-ary operators with optional lower/upper limits: `\sum`, `\prod`, `\int`,
  `\oint`, `\bigcup`, `\bigcap` (e.g. `\sum_{i=1}^n`, `\int_{a}^{b}`);
- limit-style functions with limits below/above: `\lim`, `\liminf`, `\limsup`
  (e.g. `\lim_{n \to \infty}`);
- Greek letters: the full lowercase set `\alpha` … `\omega`, the variants
  `\varepsilon`, `\vartheta`, `\varpi`, `\varrho`, `\varsigma`, `\varphi`, and
  the uppercase letters `\Gamma`, `\Delta`, `\Theta`, `\Lambda`, `\Xi`, `\Pi`,
  `\Sigma`, `\Upsilon`, `\Phi`, `\Psi`, `\Omega`;
- function names: `\sin`, `\cos`, `\tan`, `\cot`, `\sec`, `\csc`, `\arcsin`,
  `\arccos`, `\arctan`, `\sinh`, `\cosh`, `\tanh`, `\coth`, `\log`, `\ln`,
  `\lg`, `\exp`, `\max`, `\min`, `\sup`, `\inf`, `\det`, `\dim`, `\ker`,
  `\deg`, `\arg`, `\gcd`, `\hom`, `\Pr`; a following parenthesized group stays
  inside the function argument (`\log p(x_i)`), the argument stops at binary
  or relation operators (`+ - = < > , ;`);
- accents: `\hat`, `\bar`, `\vec`, `\dot`, `\ddot`, `\tilde`;
- operators and relations: `\cdot`, `\times`, `\div`, `\pm`, `\mp`, `\le`,
  `\leq`, `\ge`, `\geq`, `\neq`, `\approx`, `\sim`, `\simeq`, `\cong`,
  `\equiv`, `\propto`, `\ll`, `\gg`, `\in`, `\ni`, `\notin`, `\subset`,
  `\supset`, `\subseteq`, `\supseteq`, `\cup`, `\cap`, `\setminus`,
  `\emptyset`, `\forall`, `\exists`, `\nabla`, `\partial`, `\infty`, `\to`,
  `\gets`, `\rightarrow`, `\leftarrow`, `\longrightarrow`, `\longleftarrow`,
  `\Rightarrow`, `\Leftarrow`, `\Leftrightarrow`, `\mapsto`, `\land`, `\wedge`,
  `\lor`, `\vee`, `\neg`, `\lnot`, `\circ`, `\bullet`, `\oplus`, `\otimes`,
  `\perp`, `\parallel`, `\mid`, `\asymp`, `\vdash`, `\models`, `\ldots`,
  `\cdots`, `\ddots`;
- upright text: `\mathrm{...}` (upright math style) and `\text{...}` (normal
  text; CJK characters and spaces are preserved);
- auto-sized delimiters `\left ... \right` with any of `( ) [ ] | \{ \} \|`
  `\langle \rangle \lbrace \rbrace \vert \Vert`, or `.` for an invisible
  delimiter;
- environments with `&` cell separators and `\\` row breaks: `matrix`,
  `pmatrix`, `bmatrix`, `vmatrix`, `cases`, and `aligned` (`&` marks the
  alignment cells of each row).

Whitespace separates tokens but does not create visible math runs.

## Unsupported Input

V1 is not a complete TeX engine. Macros, user-defined commands, packages and
environments other than the ones listed above are unsupported — for example
`\mathbb`, `\mathcal`, `\boldsymbol`, `\operatorname`, `array` and `align`.
A bare `\\` outside matrix/cases/aligned environments is a syntax error, not a
line break. Unknown commands raise `UnsupportedMathError`; malformed groups,
scripts or environments raise `MathSyntaxError`. Either error aborts the build
with a structured message.

The renderer must not silently replace unsupported equations with plain text,
PNG, screenshots or partial OMML. CLI build reports the conversion error and
does not claim a successful editable equation.

# ThesisForge Math Spec v0.1

ThesisForge keeps block-equation source as LaTeX in the Domain Model. The DOCX
pipeline converts that source through a renderer-neutral `MathConverter`
contract:

```text
LaTeX source -> MathConverter -> MathExpression -> DOCX OMML renderer
```

`MathExpression` contains semantic math nodes and never contains python-docx,
lxml or OOXML objects. A different converter can replace the V1 implementation
without changing Parser, Domain Model, Compiler or the OMML renderer contract.

## V1 Supported Subset

- identifiers, digits and ordinary Unicode characters;
- `+`, `-`, `=`, `/`, parentheses, brackets, commas and periods;
- braced groups such as `{a+b}`;
- subscript and superscript: `x_i`, `x^2`, `x_i^2`;
- fractions: `\frac{a}{b}`;
- square roots: `\sqrt{x}`;
- sums with optional limits: `\sum_i`, `\sum_{i=1}^n`;
- Greek letters including `\alpha`, `\beta`, `\gamma`, `\theta`, `\lambda`,
  `\mu`, `\pi`, `\sigma`, `\phi`, `\omega` and uppercase variants;
- basic functions: `\sin`, `\cos`, `\tan`, `\log`, `\ln`, `\exp`, `\max`,
  `\min`;
- accents: `\hat{x}`, `\bar{x}`;
- common operators: `\cdot`, `\times`, `\le`, `\ge`, `\neq`, `\pm`,
  `\infty`.

Whitespace separates tokens but does not create visible math runs.

## Unsupported Input

V1 is not a complete TeX engine. Environments, matrices, alignment commands,
macros, user-defined commands and packages are unsupported. Unknown commands
raise `UnsupportedMathError`; malformed groups or scripts raise
`MathSyntaxError`.

The renderer must not silently replace unsupported equations with plain text,
PNG, screenshots or partial OMML. CLI build reports the conversion error and
does not claim a successful editable equation.

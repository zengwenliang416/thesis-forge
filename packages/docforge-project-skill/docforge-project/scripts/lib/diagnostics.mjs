export function diagnostic(code, severity, target, message, action, line) {
  return Object.freeze({
    code,
    severity,
    target,
    message,
    action,
    ...(line ? { line } : {}),
  });
}

export class DiagnosticError extends Error {
  constructor(message, diagnostics) {
    super(message);
    this.name = "DiagnosticError";
    this.diagnostics = Object.freeze([...diagnostics]);
  }
}

export function throwIfBlocked(diagnostics, message = "Import plan is blocked") {
  if (diagnostics.some((item) => item.severity === "error")) {
    throw new DiagnosticError(message, diagnostics);
  }
}

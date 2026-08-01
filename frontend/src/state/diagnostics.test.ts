import fixture from "../../../tests/fixtures/diagnostics-zh-cn-v1.json";
import type { SerializedDiagnostic } from "../transport/dto";
import {
  diagnosticSummary,
  presentDiagnostics,
  selectVisibleDiagnostics,
} from "./diagnostics";

describe("diagnostic presentation", () => {
  it("matches the shared zh-CN localization contract", () => {
    const diagnostics = fixture.cases.map((item) => item.input);
    const expectedByCode = Object.fromEntries(
      fixture.cases.map((item) => [item.input.code, item.expectedMessage]),
    );

    expect(
      Object.fromEntries(
        presentDiagnostics(diagnostics as SerializedDiagnostic[]).map(
          (diagnostic) => [diagnostic.code, diagnostic.message],
        ),
      ),
    ).toEqual(expectedByCode);
  });

  it("orders issues deterministically and filters without dropping summary counts", () => {
    const diagnostics = presentDiagnostics([
      {
        severity: "warning",
        code: "heading-level-jump",
        message: "jump",
        line: 12,
        target: "sec:later",
        details: {},
      },
      {
        severity: "error",
        code: "missing-template",
        message: "missing",
        line: null,
        target: "template",
        details: { selector: "template" },
      },
      {
        severity: "error",
        code: "missing-reference",
        message: "missing",
        line: 4,
        target: "fig:missing",
        details: {},
      },
    ]);

    expect(diagnostics.map((item) => item.code)).toEqual([
      "missing-template",
      "missing-reference",
      "heading-level-jump",
    ]);
    expect(diagnosticSummary(diagnostics)).toEqual({
      all: 3,
      error: 2,
      warning: 1,
      info: 0,
    });
    expect(
      selectVisibleDiagnostics(diagnostics, "error").map((item) => item.code),
    ).toEqual(["missing-template", "missing-reference"]);
  });
});

import { PROTOCOL_VERSION } from "./dto";
import {
  assertBuildEvent,
  type BuildReport,
  type BuildStage,
  type CompletedBuildEvent,
} from "./buildEvents";

const stages: BuildStage[] = [
  "parse",
  "validate",
  "compile",
  "render",
  "finalize",
  "postflight",
  "preview",
];

function report(overrides: Partial<BuildReport> = {}): BuildReport {
  return {
    schemaVersion: "thesisforge.build-report.v2",
    buildId: "build-1",
    intent: "publish",
    outcome: "succeeded",
    startedAt: "2026-08-20T10:00:00Z",
    completedAt: "2026-08-20T10:00:04Z",
    stages: stages.map((name) => ({
      name,
      status: "succeeded" as const,
      startedAt: null,
      completedAt: null,
    })),
    failedStage: null,
    primaryDiagnosticId: null,
    diagnostics: [],
    logs: [
      {
        sequence: 0,
        stage: "parse",
        level: "info",
        message: "Project parsed.",
      },
    ],
    output: {
      docxPath: "build/thesis.docx",
      pdfPath: "build/thesis.pdf",
      previewStale: false,
      successfulBuildId: "build-1",
    },
    ...overrides,
  };
}

function diagnostic(
  overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    id: "diag-1",
    severity: "error",
    category: "internal",
    code: "TF-INTERNAL-001",
    stage: "render",
    message: "bad",
    source: null,
    target: null,
    suggestion: null,
    relatedLocations: [],
    details: {},
    ...overrides,
  };
}

function reportWithDiagnostics(diagnostics: unknown[]): unknown {
  const value = report() as unknown as Record<string, unknown>;
  value.diagnostics = diagnostics;
  return value;
}

function reportWithPreview(preview: unknown): unknown {
  const value = report() as unknown as Record<string, unknown>;
  const output = value.output as Record<string, unknown>;
  output.finalPreview = preview;
  return value;
}

function expectInvalidReport(
  value: unknown,
  requestId: string,
): void {
  expect(() =>
    assertBuildEvent({
      protocol: PROTOCOL_VERSION,
      requestId,
      type: "completed",
      report: value,
    }),
  ).toThrow("无效的 ThesisForge BuildReport");
}

describe("build event DTO", () => {
  it("accepts strict progress and completed BuildReport events", () => {
    expect(
      assertBuildEvent(
        {
          protocol: PROTOCOL_VERSION,
          requestId: "build-progress",
          type: "progress",
          stage: "render",
        },
        "build-progress",
      ),
    ).toMatchObject({ type: "progress", stage: "render" });

    const terminal = assertBuildEvent(
      {
        protocol: PROTOCOL_VERSION,
        requestId: "build-completed",
        type: "completed",
        report: report(),
      },
      "build-completed",
    );
    if (terminal.type !== "completed") {
      throw new Error("expected completed event");
    }
    const completed: CompletedBuildEvent = terminal;
    expect(completed.report).toMatchObject({
      schemaVersion: "thesisforge.build-report.v2",
      outcome: "succeeded",
    });
  });

  it("accepts an unlocated LibreOffice preview descriptor", () => {
    const event = assertBuildEvent({
      protocol: PROTOCOL_VERSION,
      requestId: "preview-unlocated",
      type: "completed",
      report: reportWithPreview({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
      }),
    });
    if (event.type !== "completed") {
      throw new Error("expected completed event");
    }
    expect(event.report.output?.finalPreview).toMatchObject({
      engine: "libreoffice",
      fileName: "thesis.preview.pdf",
    });
  });

  it("accepts an unlocated Microsoft Word preview descriptor", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-word-unlocated",
        type: "completed",
        report: reportWithPreview({
          engine: "microsoft-word",
          label: "Microsoft Word PDF",
          fileName: "thesis.preview.pdf",
        }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("accepts a Tauri-authorized preview descriptor", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-tauri-authorized",
        type: "completed",
        report: reportWithPreview({
          engine: "libreoffice",
          label: "LibreOffice PDF",
          fileName: "thesis.preview.pdf",
          authorizationId: "a".repeat(32),
        }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("accepts an authorized Microsoft Word preview descriptor", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-word-authorized",
        type: "completed",
        report: reportWithPreview({
          engine: "microsoft-word",
          label: "Microsoft Word PDF",
          fileName: "thesis.preview.pdf",
          authorizationId: "f".repeat(32),
        }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("accepts a Web download preview descriptor", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-web-download",
        type: "completed",
        report: reportWithPreview({
          engine: "libreoffice",
          label: "LibreOffice PDF",
          fileName: "thesis.preview.pdf",
          downloadId: "b".repeat(32),
        }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("accepts a Web live-preview descriptor", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "preview-web-live",
        type: "completed",
        report: reportWithPreview({
          engine: "libreoffice",
          label: "LibreOffice PDF",
          fileName: "thesis.preview.pdf",
          downloadId: "c".repeat(32),
          livePreviewId: "d".repeat(32),
        }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("preserves omitted and null preview values", () => {
    const omitted = assertBuildEvent({
      protocol: PROTOCOL_VERSION,
      requestId: "preview-omitted",
      type: "completed",
      report: report(),
    });
    if (omitted.type !== "completed") {
      throw new Error("expected completed event");
    }
    expect(omitted.report.output).not.toHaveProperty("finalPreview");

    const nullPreview = assertBuildEvent({
      protocol: PROTOCOL_VERSION,
      requestId: "preview-null",
      type: "completed",
      report: reportWithPreview(null),
    });
    if (nullPreview.type !== "completed") {
      throw new Error("expected completed event");
    }
    expect(nullPreview.report.output?.finalPreview).toBeNull();
  });

  it("rejects a path-bearing preview descriptor", () => {
    expectInvalidReport(
      reportWithPreview({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
        path: "/private/thesis.preview.pdf",
      }),
      "preview-path",
    );
  });

  it("rejects an unsupported preview engine", () => {
    expectInvalidReport(
      reportWithPreview({
        engine: "wps",
        label: "WPS PDF",
        fileName: "thesis.preview.pdf",
      }),
      "preview-engine",
    );
  });

  it("rejects a wrong preview label", () => {
    expectInvalidReport(
      reportWithPreview({
        engine: "libreoffice",
        label: "Microsoft Word PDF",
        fileName: "thesis.preview.pdf",
      }),
      "preview-label",
    );
  });

  it("rejects invalid preview identifiers", () => {
    expectInvalidReport(
      reportWithPreview({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
        downloadId: "invalid",
      }),
      "preview-download-id",
    );
    expectInvalidReport(
      reportWithPreview({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
        downloadId: "e".repeat(32),
        livePreviewId: "invalid",
      }),
      "preview-live-id",
    );
  });

  it("rejects an undefined downloadId property", () => {
    expectInvalidReport(
      reportWithPreview({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
        downloadId: undefined,
      }),
      "preview-undefined-download",
    );
  });

  it("rejects an undefined authorizationId property", () => {
    expectInvalidReport(
      reportWithPreview({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
        authorizationId: undefined,
      }),
      "preview-undefined-authorization",
    );
  });

  it("rejects an undefined livePreviewId property", () => {
    expectInvalidReport(
      reportWithPreview({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
        livePreviewId: undefined,
      }),
      "preview-undefined-live",
    );
  });

  it("rejects preview authorization domain collisions", () => {
    expectInvalidReport(
      reportWithPreview({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
        downloadId: "e".repeat(32),
        authorizationId: "f".repeat(32),
      }),
      "preview-mixed-ids",
    );
    expectInvalidReport(
      reportWithPreview({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
        livePreviewId: "a".repeat(32),
      }),
      "preview-live-without-download",
    );
  });

  it("rejects preview descriptor extra keys", () => {
    expectInvalidReport(
      reportWithPreview({
        engine: "libreoffice",
        label: "LibreOffice PDF",
        fileName: "thesis.preview.pdf",
        extra: true,
      }),
      "preview-extra-key",
    );
  });

  it("accepts a schema-valid stage subset", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "build-stage-subset",
        type: "completed",
        report: report({
          stages: [{ name: "parse", status: "succeeded" }],
        }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("accepts pending and running stage statuses", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "build-stage-statuses",
        type: "completed",
        report: report({
          stages: [
            { name: "parse", status: "running" },
            { name: "validate", status: "pending" },
          ],
        }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("preserves string, boolean, null, and finite number details", () => {
    const event = assertBuildEvent({
      protocol: PROTOCOL_VERSION,
      requestId: "build-details",
      type: "completed",
      report: reportWithDiagnostics([
        diagnostic({
          details: {
            label: "validation",
            blocking: true,
            note: null,
            count: 2,
          },
        }),
      ]),
    });
    if (event.type !== "completed") {
      throw new Error("expected completed event");
    }
    expect(event.report.diagnostics[0].details).toEqual({
      label: "validation",
      blocking: true,
      note: null,
      count: 2,
    });
  });

  it("accepts arbitrary RFC3339 fractional precision", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "date-fraction",
        type: "completed",
        report: report({
          startedAt: "2026-08-20T10:00:00.1234567890Z",
        }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("accepts lowercase RFC3339 t and z", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "date-case",
        type: "completed",
        report: report({ startedAt: "2026-08-20t10:00:00z" }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("accepts a valid leap second at 23:59:60", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "date-leap-second",
        type: "completed",
        report: report({ startedAt: "1990-12-31T23:59:60Z" }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("accepts year-zero Gregorian leap day", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "date-year-zero",
        type: "completed",
        report: report({ startedAt: "0000-02-29T23:59:59-00:00" }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("rejects a leap second outside 23:59:60", () => {
    expectInvalidReport(
      report({ startedAt: "2026-08-20T10:00:60Z" }),
      "date-invalid-second",
    );
  });

  it("rejects an invalid leap-second minute", () => {
    expectInvalidReport(
      report({ startedAt: "2026-08-20T23:58:60Z" }),
      "date-invalid-minute",
    );
  });

  it("rejects an invalid calendar date", () => {
    expectInvalidReport(
      report({ startedAt: "2026-02-30T10:05:00Z" }),
      "date-invalid-calendar",
    );
  });

  it("accepts omitted optional report dates", () => {
    const value = report() as unknown as Record<string, unknown>;
    delete value.startedAt;
    delete value.completedAt;
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "date-omitted",
        type: "completed",
        report: value,
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("accepts null optional report dates", () => {
    expect(
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "date-null",
        type: "completed",
        report: report({ startedAt: null, completedAt: null }),
      }),
    ).toMatchObject({ type: "completed" });
  });

  it("rejects an undefined startedAt report property", () => {
    const value = report() as unknown as Record<string, unknown>;
    value.startedAt = undefined;
    expectInvalidReport(value, "date-undefined-started");
  });

  it("rejects an undefined completedAt report property", () => {
    const value = report() as unknown as Record<string, unknown>;
    value.completedAt = undefined;
    expectInvalidReport(value, "date-undefined-completed");
  });

  it("rejects an undefined startedAt stage property", () => {
    const value = report() as unknown as Record<string, unknown>;
    value.stages = [{ name: "parse", status: "succeeded", startedAt: undefined }];
    expectInvalidReport(value, "stage-undefined-started");
  });

  it("rejects an undefined completedAt stage property", () => {
    const value = report() as unknown as Record<string, unknown>;
    value.stages = [
      { name: "parse", status: "succeeded", completedAt: undefined },
    ];
    expectInvalidReport(value, "stage-undefined-completed");
  });

  it("rejects NaN diagnostic details", () => {
    expectInvalidReport(
      reportWithDiagnostics([diagnostic({ details: { count: Number.NaN } })]),
      "detail-nan",
    );
  });

  it("rejects positive infinity diagnostic details", () => {
    expectInvalidReport(
      reportWithDiagnostics([
        diagnostic({ details: { count: Number.POSITIVE_INFINITY } }),
      ]),
      "detail-positive-infinity",
    );
  });

  it("rejects negative infinity diagnostic details", () => {
    expectInvalidReport(
      reportWithDiagnostics([
        diagnostic({ details: { count: Number.NEGATIVE_INFINITY } }),
      ]),
      "detail-negative-infinity",
    );
  });

  it("rejects unknown primary diagnostics", () => {
    expectInvalidReport(
      report({ primaryDiagnosticId: "missing" }),
      "unknown-primary",
    );
  });

  it("rejects a reverse line range", () => {
    expectInvalidReport(
      reportWithDiagnostics([
        diagnostic({
          source: {
            file: "thesis.md",
            startLine: 10,
            startColumn: 1,
            endLine: 5,
            endColumn: 2,
          },
        }),
      ]),
      "reverse-lines",
    );
  });

  it("rejects a reverse same-line column range", () => {
    expectInvalidReport(
      reportWithDiagnostics([
        diagnostic({
          source: {
            file: "thesis.md",
            startLine: 10,
            startColumn: 10,
            endLine: 10,
            endColumn: 5,
          },
        }),
      ]),
      "reverse-columns",
    );
  });

  it("rejects a legacy success terminal event", () => {
    expect(() =>
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "legacy-success",
        type: "success",
        result: {},
      }),
    ).toThrow("无效的 ThesisForge 构建事件");
  });

  it("rejects a legacy error terminal event", () => {
    expect(() =>
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "legacy-error",
        type: "error",
        error: { kind: "canceled", message: "构建已取消" },
      }),
    ).toThrow("无效的 ThesisForge 构建事件");
  });

  it("rejects an event-level extra key", () => {
    expect(() =>
      assertBuildEvent({
        protocol: PROTOCOL_VERSION,
        requestId: "extra-event",
        type: "completed",
        report: report(),
        extra: true,
      } as unknown),
    ).toThrow("无效的 ThesisForge 构建事件");
  });

  it("rejects a report-level extra key", () => {
    const value = report() as unknown as Record<string, unknown>;
    value.extra = true;
    expectInvalidReport(value, "extra-report");
  });

  it("rejects a stage-level extra key", () => {
    const value = report() as unknown as Record<string, unknown>;
    value.stages = [{ name: "parse", status: "succeeded", extra: true }];
    expectInvalidReport(value, "extra-stage");
  });

  it("rejects a diagnostic-level extra key", () => {
    expectInvalidReport(
      reportWithDiagnostics([diagnostic({ extra: true })]),
      "extra-diagnostic",
    );
  });

  it("rejects a source-level extra key", () => {
    expectInvalidReport(
      reportWithDiagnostics([
        diagnostic({
          source: {
            file: "thesis.md",
            startLine: 1,
            startColumn: 1,
            endLine: 1,
            endColumn: 4,
            extra: true,
          },
        }),
      ]),
      "extra-source",
    );
  });
});

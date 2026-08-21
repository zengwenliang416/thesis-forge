import { PROTOCOL_VERSION, type CommandEnvelope } from "./dto";
import type { BuildEvent, BuildReport } from "./buildEvents";
import { TauriWorkbenchTransport } from "./tauri";
import { WebWorkbenchTransport } from "./web";

const request: CommandEnvelope = {
  protocol: PROTOCOL_VERSION,
  requestId: "build-1",
  operation: "build",
  payload: {
    source: {
      kind: "desktop",
      path: "/tmp/thesis.md",
      fileName: "thesis.md",
    },
    output: {
      kind: "desktop",
      path: "/tmp/thesis.docx",
      fileName: "thesis.docx",
    },
  },
};

const events: BuildEvent[] = [
  {
    protocol: PROTOCOL_VERSION,
    requestId: "build-1",
    type: "progress",
    stage: "parse",
  },
  {
    protocol: PROTOCOL_VERSION,
    requestId: "build-1",
    type: "completed",
    report: {
      schemaVersion: "thesisforge.build-report.v2",
      buildId: "build-1",
      intent: "publish",
      outcome: "succeeded",
      stages: [{ name: "parse", status: "succeeded" }],
      failedStage: null,
      primaryDiagnosticId: null,
      diagnostics: [],
      logs: [],
      output: {
        docxPath: "thesis.docx",
        pdfPath: null,
        previewStale: false,
        successfulBuildId: "build-1",
      } satisfies BuildReport["output"],
    },
  },
];

describe("build transport parity", () => {
  it("reads incremental Web NDJSON and sends explicit cancellation", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const streamRef: {
      current: ReadableStreamDefaultController<Uint8Array> | null;
    } = { current: null };
    const body = new ReadableStream({
      start(controller) {
        streamRef.current = controller;
        controller.enqueue(
          new TextEncoder().encode(`${JSON.stringify(events[0])}\n`),
        );
      },
    });
    const transport = new WebWorkbenchTransport({
      fetch: async (url, init) => {
        calls.push({ url: String(url), init });
        if (String(url).endsWith("/build-cancel")) {
          return new Response(JSON.stringify({ ok: true }), { status: 202 });
        }
        return new Response(body, { status: 200 });
      },
    });
    const seen: BuildEvent[] = [];
    const abort = new AbortController();

    const running = transport.runBuild(
      request,
      seen.push.bind(seen),
      abort.signal,
    );
    await vi.waitFor(() => expect(seen).toEqual([events[0]]));
    expect(calls[0].url).toBe("/api/v1/build-stream");
    expect(calls[0].init?.signal).toBe(abort.signal);

    abort.abort();
    await Promise.resolve();
    expect(calls.at(-1)?.url).toBe("/api/v1/build-cancel");
    streamRef.current?.close();
    await running;
  });

  it("forwards Tauri Channel events and aborts by request ID", async () => {
    const calls: Array<{ command: string; args?: Record<string, unknown> }> = [];
    let handler: ((event: unknown) => void) | null = null;
    const buildRef: { finish: (() => void) | null } = { finish: null };
    const transport = new TauriWorkbenchTransport(
      async (command, args) => {
        calls.push({ command, args });
        if (command === "run_build") {
          handler?.(events[0]);
          await new Promise<void>((resolve) => {
            buildRef.finish = resolve;
          });
        }
        return null;
      },
      (onmessage) => {
        handler = onmessage;
        return { onmessage };
      },
    );
    const seen: BuildEvent[] = [];
    const abort = new AbortController();

    const running = transport.runBuild(
      request,
      seen.push.bind(seen),
      abort.signal,
    );
    await vi.waitFor(() => expect(seen).toEqual([events[0]]));
    expect(calls[0].command).toBe("run_build");

    abort.abort();
    await Promise.resolve();
    expect(calls.at(-1)).toMatchObject({
      command: "cancel_build",
      args: { requestId: "build-1" },
    });
    buildRef.finish?.();
    await running;
  });
});

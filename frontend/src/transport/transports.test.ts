import {
  assertCommandResponse,
  PROTOCOL_VERSION,
  readSerializedDiagnostics,
  type CommandEnvelope,
  type CommandResponse,
} from "./dto";
import { TauriWorkbenchTransport } from "./tauri";
import { WebWorkbenchTransport } from "./web";
import type { ProjectIdentityRef } from "./WorkbenchTransport";

const request: CommandEnvelope = {
  protocol: PROTOCOL_VERSION,
  requestId: "request-1",
  operation: "inspect",
  payload: {
    source: {
      kind: "web-workspace",
      workspaceId: "workspace-1",
      fileName: "thesis.md",
    },
  },
};

const response: CommandResponse = {
  protocol: PROTOCOL_VERSION,
  requestId: "request-1",
  ok: true,
  result: {
    source: { kind: "web-workspace", name: "thesis.md" },
    outline: [],
    diagnostics: [],
  },
};

describe("runtime transports", () => {
  it("sends the versioned envelope through the Web HTTP adapter", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const transport = new WebWorkbenchTransport({
      baseUrl: "http://127.0.0.1:8765",
      fetch: async (url, init) => {
        calls.push({ url: String(url), init });
        return new Response(JSON.stringify(response), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      },
    });

    await expect(transport.dispatch(request)).resolves.toEqual(response);
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toBe("http://127.0.0.1:8765/api/v1/dispatch");
    expect(JSON.parse(String(calls[0].init?.body))).toEqual(request);
  });

  it("sends the same envelope through one Tauri command", async () => {
    const calls: Array<{ command: string; args?: Record<string, unknown> }> = [];
    const transport = new TauriWorkbenchTransport(async (command, args) => {
      calls.push({ command, args });
      return response;
    });

    await expect(transport.dispatch(request)).resolves.toEqual(response);
    expect(calls).toEqual([
      {
        command: "dispatch_workbench",
        args: { request },
      },
    ]);
  });

  it("creates an opaque Web workspace before returning an opened source", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const transport = new WebWorkbenchTransport({
      baseUrl: "http://127.0.0.1:8765",
      fetch: async (url, init) => {
        calls.push({ url: String(url), init });
        return new Response(
          JSON.stringify({
            protocol: PROTOCOL_VERSION,
            ok: true,
            source: {
              kind: "web-workspace",
              workspaceId: "a".repeat(32),
              fileName: "thesis.md",
            },
            text: "# 绪论\n",
          }),
          { status: 201, headers: { "content-type": "application/json" } },
        );
      },
    });

    await expect(
      transport.openSource({ fileName: "thesis.md", text: "# 绪论\n" }),
    ).resolves.toEqual({
      source: {
        kind: "web-workspace",
        workspaceId: "a".repeat(32),
        fileName: "thesis.md",
      },
      text: "# 绪论\n",
    });
    expect(calls[0].url).toBe("http://127.0.0.1:8765/api/v1/workspaces");
  });

  it("uses the native Tauri source picker without browser path assumptions", async () => {
    const calls: string[] = [];
    const transport = new TauriWorkbenchTransport(async (command) => {
      calls.push(command);
      return {
        source: {
          kind: "desktop",
          path: "/Users/test/thesis.md",
          fileName: "thesis.md",
        },
        text: "# 绪论\n",
      };
    });

    await expect(transport.openSource()).resolves.toEqual({
      source: {
        kind: "desktop",
        path: "/Users/test/thesis.md",
        fileName: "thesis.md",
      },
      text: "# 绪论\n",
    });
    expect(calls).toEqual(["pick_source"]);
  });

  it("returns the typed project identity and source snapshot through one Tauri command", async () => {
    const calls: Array<{ command: string; args?: Record<string, unknown> }> = [];
    const transport = new TauriWorkbenchTransport(async (command, args) => {
      calls.push({ command, args });
      return {
        project: {
          id: "project-1",
          root: "/Users/test/thesis",
          manifestPath: "/Users/test/thesis/thesisforge.yaml",
        },
        source: {
          kind: "desktop",
          path: "/Users/test/thesis/thesis.md",
          fileName: "thesis.md",
        },
        text: "# 绪论\n",
      };
    });

    await expect(transport.openProject()).resolves.toEqual({
      project: {
        id: "project-1",
        root: "/Users/test/thesis",
        manifestPath: "/Users/test/thesis/thesisforge.yaml",
      },
      source: {
        kind: "desktop",
        path: "/Users/test/thesis/thesis.md",
        fileName: "thesis.md",
      },
      text: "# 绪论\n",
    });
    expect(calls).toEqual([{ command: "pick_project", args: undefined }]);
  });

  it("resolves a Web preview from its opaque workspace descriptor", async () => {
    const calls: string[] = [];
    const transport = new WebWorkbenchTransport({
      baseUrl: "http://127.0.0.1:8765",
      fetch: async (url) => {
        calls.push(String(url));
        return new Response(new TextEncoder().encode("%PDF-1.7\n"), {
          status: 200,
          headers: { "content-type": "application/pdf" },
        });
      },
    });

    const bytes = await transport.resolveFinalPreview({
      engine: "libreoffice",
      label: "LibreOffice PDF",
      fileName: "thesis.preview.pdf",
      downloadId: "a".repeat(32),
    });

    expect(new TextDecoder().decode(bytes)).toBe("%PDF-1.7\n");
    expect(calls).toEqual([
      `http://127.0.0.1:8765/api/v1/workspaces/${"a".repeat(32)}/files/thesis.preview.pdf`,
    ]);
  });

  it("prepares and discards a Web live preview through server capabilities", async () => {
    const calls: Array<{ url: string; body: unknown }> = [];
    const output = {
      kind: "web-download" as const,
      workspaceId: "a".repeat(32),
      fileName: `.thesisforge-live-preview-${"b".repeat(32)}.docx`,
      livePreviewId: "b".repeat(32),
    };
    const transport = new WebWorkbenchTransport({
      baseUrl: "http://127.0.0.1:8765",
      fetch: async (url, init) => {
        calls.push({
          url: String(url),
          body: JSON.parse(String(init?.body)),
        });
        return Response.json(
          String(url).endsWith("/api/v1/live-previews")
            ? {
                protocol: PROTOCOL_VERSION,
                ok: true,
                output,
              }
            : {
                protocol: PROTOCOL_VERSION,
                ok: true,
              },
          { status: String(url).endsWith("/api/v1/live-previews") ? 201 : 200 },
        );
      },
    });
    const source = {
      kind: "web-workspace" as const,
      workspaceId: "a".repeat(32),
      fileName: "thesis.md",
    };

    await expect(transport.prepareLivePreviewOutput(source)).resolves.toEqual(
      output,
    );
    await transport.discardLivePreviewOutput(output);

    expect(calls).toEqual([
      {
        url: "http://127.0.0.1:8765/api/v1/live-previews",
        body: { source },
      },
      {
        url: "http://127.0.0.1:8765/api/v1/live-previews/discard",
        body: { output },
      },
    ]);
  });

  it("imports a browser-selected Office PDF through the transport contract", async () => {
    const transport = new WebWorkbenchTransport({
      pickPdf: async () => ({
        fileName: "word-export.pdf",
        bytes: new TextEncoder().encode("%PDF-1.7\n"),
      }),
    });

    const selected = await transport.pickFinalPreview();
    expect(selected?.descriptor).toEqual({
      engine: "microsoft-word",
      label: "Microsoft Word PDF",
      fileName: "word-export.pdf",
    });
    expect(selected?.bytes).toBeInstanceOf(Uint8Array);
  });

  it("uses Tauri picker authorization and raw PDF reader commands", async () => {
    const calls: Array<{ command: string; args?: Record<string, unknown> }> = [];
    const descriptor = {
      engine: "microsoft-word" as const,
      label: "Microsoft Word PDF" as const,
      fileName: "word-export.pdf",
      authorizationId: "b".repeat(32),
    };
    const transport = new TauriWorkbenchTransport(async (command, args) => {
      calls.push({ command, args });
      if (command === "pick_pdf_preview") {
        return descriptor;
      }
      return new TextEncoder().encode("%PDF-1.7\n").buffer;
    });

    const selected = await transport.pickFinalPreview();
    expect(selected?.descriptor).toEqual(descriptor);
    expect(selected?.bytes).toBeInstanceOf(Uint8Array);
    expect(calls).toEqual([
      { command: "pick_pdf_preview", args: undefined },
      {
        command: "read_pdf_preview",
        args: { descriptor },
      },
    ]);
  });

  it("accepts PDF bytes serialized by the Tauri postMessage fallback", async () => {
    const descriptor = {
      engine: "microsoft-word" as const,
      label: "Microsoft Word PDF" as const,
      fileName: "word-export.pdf",
      authorizationId: "b".repeat(32),
    };
    const serializedBytes = Array.from(
      new TextEncoder().encode("%PDF-1.7\n"),
    );
    const transport = new TauriWorkbenchTransport(async () => serializedBytes);

    await expect(transport.resolveFinalPreview(descriptor)).resolves.toEqual(
      new Uint8Array(serializedBytes),
    );
  });

  it("prepares and discards a Tauri live preview output through native commands", async () => {
    const calls: Array<{ command: string; args?: Record<string, unknown> }> = [];
    const output = {
      kind: "desktop" as const,
      path: "/tmp/thesisforge-live-preview-a/thesisforge-live-preview-a.docx",
      fileName: "thesisforge-live-preview-a.docx",
    };
    const transport = new TauriWorkbenchTransport(async (command, args) => {
      calls.push({ command, args });
      return command === "prepare_live_preview_output" ? output : null;
    });

    await expect(
      transport.prepareLivePreviewOutput({
        kind: "desktop",
        path: "/Users/test/thesis.md",
        fileName: "thesis.md",
      }),
    ).resolves.toEqual(output);
    await transport.discardLivePreviewOutput(output);

    expect(calls).toEqual([
      { command: "prepare_live_preview_output", args: undefined },
      { command: "discard_live_preview_output", args: { output } },
    ]);
  });

  it("rejects incomplete success and failure envelopes", () => {
    expect(() =>
      assertCommandResponse({
        protocol: PROTOCOL_VERSION,
        requestId: "request-1",
        ok: true,
      }),
    ).toThrow("无效的 ThesisForge transport 响应");
    expect(() =>
      assertCommandResponse({
        protocol: PROTOCOL_VERSION,
        requestId: "request-1",
        ok: false,
      }),
    ).toThrow("无效的 ThesisForge transport 响应");
  });

  it("rejects malformed serialized diagnostics", () => {
    expect(() =>
      assertCommandResponse({
        protocol: PROTOCOL_VERSION,
        requestId: "validate-1",
        ok: true,
        result: {
          diagnostics: [
            {
              severity: "fatal",
              code: "missing-template",
              message: "missing",
            },
          ],
        },
      }),
    ).toThrow("无效的 ThesisForge transport 响应");
  });

  it("rejects coerced enum values and non-finite diagnostic details", () => {
    const diagnostic = {
      severity: "error",
      code: "TF-VALIDATION",
      message: "invalid",
      line: 1,
      target: null,
      details: {},
    };
    const rejectedDiagnostics = [
      { ...diagnostic, severity: ["error"] },
      { ...diagnostic, severity: { value: "error" } },
      { ...diagnostic, details: { count: Number.NaN } },
      { ...diagnostic, details: { count: Number.POSITIVE_INFINITY } },
    ];

    for (const invalid of rejectedDiagnostics) {
      expect(() =>
        readSerializedDiagnostics({ diagnostics: [invalid] }, true),
      ).toThrow("无效的 ThesisForge transport 响应");
    }

    expect(() =>
      assertCommandResponse({
        protocol: PROTOCOL_VERSION,
        requestId: "request-1",
        ok: false,
        error: {
          kind: ["transport"],
          message: "invalid",
        },
      }),
    ).toThrow("无效的 ThesisForge transport 响应");
  });

  it("requires diagnostics for validation result consumers", () => {
    expect(() => readSerializedDiagnostics({}, true)).toThrow(
      "无效的 ThesisForge transport 响应",
    );
    expect(readSerializedDiagnostics({ diagnostics: [] }, true)).toEqual([]);
  });
});

describe("project identity envelope", () => {
  const project: ProjectIdentityRef = {
    id: "thesis-2026",
    root: "/home/user/thesis",
    manifestPath: "/home/user/thesis/thesisforge.yaml",
  };

  function projectRequest(
    operation: CommandEnvelope["operation"],
    requestId: string,
  ): CommandEnvelope {
    return {
      protocol: PROTOCOL_VERSION,
      requestId,
      operation,
      payload: {
        source: {
          kind: "desktop",
          path: "/home/user/thesis/thesis.md",
          fileName: "thesis.md",
        },
        project,
      },
    };
  }

  function okResponse(requestId: string): CommandResponse {
    return {
      protocol: PROTOCOL_VERSION,
      requestId,
      ok: true,
      result: {},
    };
  }

  function captureWebTransport() {
    const calls: Array<{ url: string; body: unknown }> = [];
    const transport = new WebWorkbenchTransport({
      baseUrl: "http://127.0.0.1:8765",
      fetch: async (url, init) => {
        calls.push({ url: String(url), body: JSON.parse(String(init?.body)) });
        const envelope = JSON.parse(String(init?.body)) as CommandEnvelope;
        return new Response(JSON.stringify(okResponse(envelope.requestId)), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      },
    });
    return { calls, transport };
  }

  it.each(["inspect", "validate", "save"] as const)(
    "serializes payload.project intact for Web dispatch of %s",
    async (operation) => {
      const { calls, transport } = captureWebTransport();
      const envelope = projectRequest(operation, `project-${operation}-1`);

      await transport.dispatch(envelope);

      expect(calls).toHaveLength(1);
      expect(calls[0].url).toBe("http://127.0.0.1:8765/api/v1/dispatch");
      expect(calls[0].body).toEqual(envelope);
      expect(
        (calls[0].body as CommandEnvelope).payload.project,
      ).toEqual(project);
    },
  );

  it("serializes payload.project intact through the Web build stream request", async () => {
    const calls: Array<{ url: string; body: unknown }> = [];
    const event = {
      protocol: PROTOCOL_VERSION,
      requestId: "project-build-1",
      type: "progress",
      stage: "parse",
    };
    const transport = new WebWorkbenchTransport({
      baseUrl: "http://127.0.0.1:8765",
      fetch: async (url, init) => {
        calls.push({ url: String(url), body: JSON.parse(String(init?.body)) });
        return new Response(`${JSON.stringify(event)}\n`, {
          status: 200,
          headers: { "content-type": "application/x-ndjson" },
        });
      },
    });
    const envelope = projectRequest("build", "project-build-1");
    const events: unknown[] = [];

    await transport.runBuild(
      envelope,
      (buildEvent) => events.push(buildEvent),
      new AbortController().signal,
    );

    expect(calls).toHaveLength(1);
    expect(calls[0].url).toBe("http://127.0.0.1:8765/api/v1/build-stream");
    expect(calls[0].body).toEqual(envelope);
    expect(events).toEqual([event]);
  });

  it("passes the project-bearing envelope through Tauri dispatch unchanged", async () => {
    const calls: Array<{ command: string; args?: Record<string, unknown> }> =
      [];
    const transport = new TauriWorkbenchTransport(async (command, args) => {
      calls.push({ command, args });
      const envelope = (args as { request: CommandEnvelope }).request;
      return okResponse(envelope.requestId);
    });
    const envelope = projectRequest("preview", "project-preview-1");

    await transport.dispatch(envelope);

    expect(calls).toEqual([
      { command: "dispatch_workbench", args: { request: envelope } },
    ]);
  });

  it("survives a JSON round-trip with the project payload", () => {
    const envelope = projectRequest("build", "project-roundtrip-1");

    expect(JSON.parse(JSON.stringify(envelope))).toEqual(envelope);
  });

  it("still dispatches envelopes without project on both transports", async () => {
    const legacy: CommandEnvelope = {
      protocol: PROTOCOL_VERSION,
      requestId: "legacy-upload-1",
      operation: "inspect",
      payload: {
        source: {
          kind: "web-upload",
          uploadId: "a".repeat(32),
          fileName: "thesis.md",
        },
      },
    };

    const { calls, transport: web } = captureWebTransport();
    await expect(web.dispatch(legacy)).resolves.toEqual(
      okResponse("legacy-upload-1"),
    );
    expect(calls).toHaveLength(1);
    expect(calls[0].body).toEqual(legacy);

    const tauriCalls: Array<{
      command: string;
      args?: Record<string, unknown>;
    }> = [];
    const tauri = new TauriWorkbenchTransport(async (command, args) => {
      tauriCalls.push({ command, args });
      return okResponse("legacy-upload-1");
    });
    await expect(tauri.dispatch(legacy)).resolves.toEqual(
      okResponse("legacy-upload-1"),
    );
    expect(tauriCalls).toEqual([
      { command: "dispatch_workbench", args: { request: legacy } },
    ]);
  });
});

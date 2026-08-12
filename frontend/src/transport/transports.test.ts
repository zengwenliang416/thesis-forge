import {
  assertCommandResponse,
  PROTOCOL_VERSION,
  readSerializedDiagnostics,
  type CommandEnvelope,
  type CommandResponse,
} from "./dto";
import { TauriWorkbenchTransport } from "./tauri";
import { WebWorkbenchTransport } from "./web";

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

  it("imports a browser-selected WPS PDF through the transport contract", async () => {
    const transport = new WebWorkbenchTransport({
      pickPdf: async () => ({
        fileName: "wps-export.pdf",
        bytes: new TextEncoder().encode("%PDF-1.7\n"),
      }),
    });

    const selected = await transport.pickFinalPreview();
    expect(selected?.descriptor).toEqual({
      engine: "wps",
      label: "WPS PDF",
      fileName: "wps-export.pdf",
    });
    expect(selected?.bytes).toBeInstanceOf(Uint8Array);
  });

  it("uses Tauri picker authorization and raw PDF reader commands", async () => {
    const calls: Array<{ command: string; args?: Record<string, unknown> }> = [];
    const descriptor = {
      engine: "wps" as const,
      label: "WPS PDF" as const,
      fileName: "wps-export.pdf",
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

  it("requires diagnostics for validation result consumers", () => {
    expect(() => readSerializedDiagnostics({}, true)).toThrow(
      "无效的 ThesisForge transport 响应",
    );
    expect(readSerializedDiagnostics({ diagnostics: [] }, true)).toEqual([]);
  });
});

import {
  assertCommandResponse,
  type CommandEnvelope,
  type CommandOutputRef,
  type SourceRef,
} from "./dto";
import { assertBuildEvent, type BuildEvent } from "./buildEvents";
import type {
  OpenSourceInput,
  OpenedSource,
  WorkbenchTransport,
} from "./WorkbenchTransport";
import {
  readFinalPreviewDescriptor,
  readPdfBytes,
  type FinalPreviewDescriptor,
  type ResolvedFinalPreview,
} from "./finalPreview";

interface WebTransportOptions {
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
  pickPdf?: () => Promise<{ fileName: string; bytes: Uint8Array } | null>;
}

export class WebWorkbenchTransport implements WorkbenchTransport {
  readonly runtime = "web" as const;
  readonly capabilities = {
    nativePaths: false,
    saveWorkspace: true,
    saveAs: false,
    download: true,
  };

  readonly #baseUrl: string;
  readonly #fetch: typeof globalThis.fetch;
  readonly #pickPdf: () => Promise<{
    fileName: string;
    bytes: Uint8Array;
  } | null>;

  constructor(options: WebTransportOptions = {}) {
    this.#baseUrl = (options.baseUrl ?? "").replace(/\/$/, "");
    this.#fetch = options.fetch ?? globalThis.fetch.bind(globalThis);
    this.#pickPdf = options.pickPdf ?? pickBrowserPdf;
  }

  async openSource(input?: OpenSourceInput): Promise<OpenedSource> {
    if (!input) {
      throw new Error("Web source input is required");
    }
    const response = await this.#fetch(`${this.#baseUrl}/api/v1/workspaces`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify(input),
    });
    const body: unknown = await response.json();
    if (
      !response.ok ||
      typeof body !== "object" ||
      body === null ||
      !("protocol" in body) ||
      body.protocol !== "thesisforge.workbench.v1" ||
      !("ok" in body) ||
      body.ok !== true ||
      !("source" in body) ||
      typeof body.source !== "object" ||
      body.source === null ||
      !("text" in body) ||
      typeof body.text !== "string"
    ) {
      throw new Error("创建 Web 工作区失败");
    }
    return {
      source: body.source as OpenedSource["source"],
      text: body.text,
    };
  }

  async dispatch(request: CommandEnvelope, signal?: AbortSignal) {
    const response = await this.#fetch(`${this.#baseUrl}/api/v1/dispatch`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify(request),
      signal,
    });
    const body: unknown = await response.json();
    const commandResponse = assertCommandResponse(body);
    if (!response.ok && commandResponse.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return commandResponse;
  }

  async runBuild(
    request: CommandEnvelope,
    onEvent: (event: BuildEvent) => void,
    signal: AbortSignal,
  ): Promise<void> {
    const cancel = () => {
      void this.#fetch(`${this.#baseUrl}/api/v1/build-cancel`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ requestId: request.requestId }),
      });
    };
    signal.addEventListener("abort", cancel, { once: true });
    try {
      const response = await this.#fetch(
        `${this.#baseUrl}/api/v1/build-stream`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(request),
          signal,
        },
      );
      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        buffer += decoder.decode(value, { stream: !done });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (line.trim()) {
            onEvent(
              assertBuildEvent(JSON.parse(line) as unknown, request.requestId),
            );
          }
        }
        if (done) {
          break;
        }
      }
      if (buffer.trim()) {
        onEvent(
          assertBuildEvent(JSON.parse(buffer) as unknown, request.requestId),
        );
      }
    } finally {
      signal.removeEventListener("abort", cancel);
    }
  }

  async prepareLivePreviewOutput(
    source: SourceRef,
  ): Promise<CommandOutputRef> {
    if (source.kind !== "web-workspace") {
      throw new Error("Web 实时预览需要持久工作区");
    }
    const response = await this.#fetch(`${this.#baseUrl}/api/v1/live-previews`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ source }),
    });
    const body: unknown = await response.json();
    if (
      !response.ok ||
      typeof body !== "object" ||
      body === null ||
      !("ok" in body) ||
      body.ok !== true ||
      !("output" in body) ||
      typeof body.output !== "object" ||
      body.output === null
    ) {
      throw new Error("准备 Web 实时预览失败");
    }
    return body.output as CommandOutputRef;
  }

  async discardLivePreviewOutput(output: CommandOutputRef): Promise<void> {
    await this.#fetch(`${this.#baseUrl}/api/v1/live-previews/discard`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ output }),
    });
  }

  async resolveFinalPreview(
    descriptor: FinalPreviewDescriptor,
  ): Promise<Uint8Array> {
    const preview = readFinalPreviewDescriptor(descriptor);
    if (preview.engine !== "libreoffice" || !preview.downloadId) {
      throw new Error("Web 自动预览缺少工作区定位信息");
    }
    const resource = preview.livePreviewId
      ? `live-previews/${preview.livePreviewId}`
      : `files/${encodeURIComponent(preview.fileName)}`;
    const response = await this.#fetch(
      `${this.#baseUrl}/api/v1/workspaces/${preview.downloadId}/${resource}`,
      {
        method: "GET",
        headers: { accept: "application/pdf" },
      },
    );
    if (
      !response.ok ||
      response.headers.get("content-type")?.split(";")[0].trim() !==
        "application/pdf"
    ) {
      throw new Error(`读取 Web PDF 失败（HTTP ${response.status}）`);
    }
    return readPdfBytes(await response.arrayBuffer());
  }

  async pickFinalPreview(): Promise<ResolvedFinalPreview | null> {
    const picked = await this.#pickPdf();
    if (!picked) {
      return null;
    }
    const descriptor = readFinalPreviewDescriptor({
      engine: "wps",
      label: "WPS PDF",
      fileName: picked.fileName,
    });
    return {
      descriptor,
      bytes: readPdfBytes(picked.bytes),
    };
  }
}

async function pickBrowserPdf(): Promise<{
  fileName: string;
  bytes: Uint8Array;
} | null> {
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "application/pdf,.pdf";
    input.addEventListener(
      "change",
      () => {
        const file = input.files?.[0];
        if (!file) {
          resolve(null);
          return;
        }
        void file
          .arrayBuffer()
          .then((buffer) =>
            resolve({ fileName: file.name, bytes: new Uint8Array(buffer) }),
          )
          .catch(() => resolve(null));
      },
      { once: true },
    );
    input.addEventListener("cancel", () => resolve(null), { once: true });
    input.click();
  });
}

import { assertCommandResponse, type CommandEnvelope } from "./dto";
import { assertBuildEvent, type BuildEvent } from "./buildEvents";
import type {
  OpenSourceInput,
  OpenedSource,
  WorkbenchTransport,
} from "./WorkbenchTransport";

interface WebTransportOptions {
  baseUrl?: string;
  fetch?: typeof globalThis.fetch;
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

  constructor(options: WebTransportOptions = {}) {
    this.#baseUrl = (options.baseUrl ?? "").replace(/\/$/, "");
    this.#fetch = options.fetch ?? globalThis.fetch.bind(globalThis);
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
}

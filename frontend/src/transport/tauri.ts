import { Channel } from "@tauri-apps/api/core";
import { assertCommandResponse, type CommandEnvelope } from "./dto";
import { assertBuildEvent, type BuildEvent } from "./buildEvents";
import type { OpenedSource, WorkbenchTransport } from "./WorkbenchTransport";

export type TauriInvoke = (
  command: string,
  args?: Record<string, unknown>,
) => Promise<unknown>;

interface TauriChannel<T> {
  onmessage: (message: T) => void;
}

type TauriChannelFactory = (
  onmessage: (message: unknown) => void,
) => TauriChannel<unknown>;

export class TauriWorkbenchTransport implements WorkbenchTransport {
  readonly runtime = "tauri" as const;
  readonly capabilities = {
    nativePaths: true,
    saveWorkspace: false,
    saveAs: true,
    download: false,
  };

  constructor(
    private readonly invoke: TauriInvoke,
    private readonly channelFactory: TauriChannelFactory = (onmessage) =>
      new Channel(onmessage),
  ) {}

  async openSource(): Promise<OpenedSource | null> {
    const result = await this.invoke("pick_source");
    if (result === null) {
      return null;
    }
    if (
      typeof result !== "object" ||
      !("source" in result) ||
      !("text" in result) ||
      typeof result.text !== "string"
    ) {
      throw new Error("无效的 Tauri source picker 响应");
    }
    return result as OpenedSource;
  }

  async dispatch(request: CommandEnvelope) {
    return assertCommandResponse(
      await this.invoke("dispatch_workbench", { request }),
    );
  }

  async runBuild(
    request: CommandEnvelope,
    onEvent: (event: BuildEvent) => void,
    signal: AbortSignal,
  ): Promise<void> {
    const channel = this.channelFactory((value) =>
      onEvent(assertBuildEvent(value, request.requestId)),
    );
    const cancel = () => {
      void this.invoke("cancel_build", { requestId: request.requestId });
    };
    signal.addEventListener("abort", cancel, { once: true });
    try {
      await this.invoke("run_build", { request, onEvent: channel });
    } finally {
      signal.removeEventListener("abort", cancel);
    }
  }
}

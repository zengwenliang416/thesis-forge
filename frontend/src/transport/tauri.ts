import { Channel } from "@tauri-apps/api/core";
import {
  assertCommandResponse,
  type CommandEnvelope,
  type CommandOutputRef,
  type SourceRef,
} from "./dto";
import { assertBuildEvent, type BuildEvent } from "./buildEvents";
import type { OpenedSource, WorkbenchTransport } from "./WorkbenchTransport";
import {
  readFinalPreviewDescriptor,
  readPdfBytes,
  type FinalPreviewDescriptor,
  type ResolvedFinalPreview,
} from "./finalPreview";

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

  async prepareLivePreviewOutput(
    source: SourceRef,
  ): Promise<CommandOutputRef> {
    if (source.kind !== "desktop") {
      throw new Error("Tauri 实时预览需要本地 Markdown 文稿");
    }
    const output = await this.invoke("prepare_live_preview_output");
    if (
      typeof output !== "object" ||
      output === null ||
      !("kind" in output) ||
      output.kind !== "desktop" ||
      !("path" in output) ||
      typeof output.path !== "string" ||
      !("fileName" in output) ||
      typeof output.fileName !== "string"
    ) {
      throw new Error("无效的 Tauri 实时预览输出响应");
    }
    return output as CommandOutputRef;
  }

  async discardLivePreviewOutput(output: CommandOutputRef): Promise<void> {
    await this.invoke("discard_live_preview_output", { output });
  }

  async resolveFinalPreview(
    descriptor: FinalPreviewDescriptor,
  ): Promise<Uint8Array> {
    const preview = readFinalPreviewDescriptor(descriptor);
    if (preview.downloadId !== undefined) {
      throw new Error("Tauri 最终预览不能包含 Web workspace ID");
    }
    if (!preview.authorizationId) {
      throw new Error("Tauri 最终预览缺少授权定位信息");
    }
    return readPdfBytes(
      await this.invoke("read_pdf_preview", { descriptor: preview }),
    );
  }

  async pickFinalPreview(): Promise<ResolvedFinalPreview | null> {
    const result = await this.invoke("pick_pdf_preview");
    if (result === null) {
      return null;
    }
    const descriptor = readFinalPreviewDescriptor(result);
    return {
      descriptor,
      bytes: await this.resolveFinalPreview(descriptor),
    };
  }
}

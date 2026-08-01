import { assertCommandResponse, type CommandEnvelope } from "./dto";
import type { OpenedSource, WorkbenchTransport } from "./WorkbenchTransport";

export type TauriInvoke = (
  command: string,
  args?: Record<string, unknown>,
) => Promise<unknown>;

export class TauriWorkbenchTransport implements WorkbenchTransport {
  readonly runtime = "tauri" as const;
  readonly capabilities = {
    nativePaths: true,
    saveWorkspace: false,
    saveAs: true,
    download: false,
  };

  constructor(private readonly invoke: TauriInvoke) {}

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
}

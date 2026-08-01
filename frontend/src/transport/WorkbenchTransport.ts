import type {
  CommandEnvelope,
  CommandResponse,
  RuntimeKind,
  SourceRef,
} from "./dto";

export interface RuntimeCapabilities {
  nativePaths: boolean;
  saveWorkspace: boolean;
  saveAs: boolean;
  download: boolean;
}

export interface OpenSourceInput {
  fileName: string;
  text: string;
}

export interface OpenedSource {
  source: SourceRef;
  text: string;
}

export interface WorkbenchTransport {
  readonly runtime: RuntimeKind;
  readonly capabilities: RuntimeCapabilities;
  openSource(input?: OpenSourceInput): Promise<OpenedSource | null>;
  dispatch(request: CommandEnvelope, signal?: AbortSignal): Promise<CommandResponse>;
}

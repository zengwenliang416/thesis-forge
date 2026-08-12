import type {
  CommandEnvelope,
  CommandResponse,
  RuntimeKind,
  SourceRef,
} from "./dto";
import type { BuildEvent } from "./buildEvents";
import type {
  FinalPreviewDescriptor,
  ResolvedFinalPreview,
} from "./finalPreview";

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
  runBuild?(
    request: CommandEnvelope,
    onEvent: (event: BuildEvent) => void,
    signal: AbortSignal,
  ): Promise<void>;
  resolveFinalPreview(
    descriptor: FinalPreviewDescriptor,
  ): Promise<Uint8Array>;
  pickFinalPreview(): Promise<ResolvedFinalPreview | null>;
}

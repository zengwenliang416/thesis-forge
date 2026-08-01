import { ChevronLeft, Download } from "lucide-react";
import type { RuntimeCapabilities } from "../transport/WorkbenchTransport";
import type { RuntimeKind } from "../transport/dto";
import type { WorkspaceState } from "../state/workspace";

interface OutputFeedbackProps {
  runtime: RuntimeKind;
  capabilities: RuntimeCapabilities;
  state: WorkspaceState;
}

export function OutputFeedback({
  runtime,
  capabilities,
  state,
}: OutputFeedbackProps) {
  return (
    <footer className="global-status">
      <span>
        <ChevronLeft aria-hidden="true" />
        Markdown → ThesisDocument → Validation → Template → RenderPlan → DOCX
      </span>
      <span role="status" aria-label="输出结果">
        {capabilities.download ? <Download aria-hidden="true" /> : null}
        {state.output
          ? state.output.name
          : `尚无输出 · ${runtime === "tauri" ? "macOS / Windows" : "Browser"}`}
      </span>
    </footer>
  );
}

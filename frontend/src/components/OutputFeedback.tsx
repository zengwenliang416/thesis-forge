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
        Markdown → Microsoft Word · 本地优先 · 模板驱动
      </span>
      <span role="status" aria-label="输出结果">
        {capabilities.download ? <Download aria-hidden="true" /> : null}
        {state.output
          ? state.output.name
          : `准备生成 DOCX · ${runtime === "tauri" ? "桌面" : "浏览器"}`}
      </span>
    </footer>
  );
}

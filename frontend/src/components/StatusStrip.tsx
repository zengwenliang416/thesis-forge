import type { RuntimeKind } from "../transport/dto";
import type { WorkspaceState } from "../state/workspace";

interface StatusStripProps {
  state: WorkspaceState;
  runtime: RuntimeKind;
  title: string;
  detail: string;
  onRecover(): void;
}

export function StatusStrip({
  state,
  runtime,
  title,
  detail,
  onRecover,
}: StatusStripProps) {
  const recoverable = ["error", "permission", "canceled", "disabled"].includes(
    state.status,
  );

  return (
    <section className="status-strip" aria-live="polite">
      <div>
        <span className="status-dot" aria-hidden="true" />
        <strong>{title}</strong>
        <span>{state.errorMessage ?? detail}</span>
      </div>
      <div className="status-tools">
        {recoverable ? (
          <button
            type="button"
            className="button recovery-action"
            onClick={onRecover}
          >
            恢复工作区
          </button>
        ) : null}
        <BuildProgress state={state} />
        <TemplateSelector disabled={!state.source} />
        <div className="runtime-chip">
          {runtime === "tauri" ? "本地桌面" : "Web 工作区"}
        </div>
      </div>
    </section>
  );
}

export function BuildProgress({ state }: { state: WorkspaceState }) {
  return (
    <div
      className="build-progress-shell"
      role="status"
      aria-label="构建进度"
    >
      <span>{state.operation?.kind === "build" ? "构建中" : "等待构建"}</span>
      <div aria-hidden="true">
        {["解析", "验证", "编译", "渲染", "完成"].map((stage) => (
          <i key={stage} title={stage} />
        ))}
      </div>
    </div>
  );
}

export function TemplateSelector({ disabled }: { disabled: boolean }) {
  return (
    <label className="template-control">
      <span>学校模板</span>
      <select aria-label="学校模板" disabled={disabled}>
        <option>基础本科论文模板</option>
      </select>
    </label>
  );
}

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
    <section
      className="status-strip"
      aria-live="polite"
      data-building={state.operation?.kind === "build"}
    >
      <span
        className="status-dot"
        aria-hidden="true"
        title={state.errorMessage ?? detail}
      />
      <span className="status-title">{title}</span>
      <span className={recoverable ? "status-message" : "status-sr-text"}>
        {state.errorMessage ?? detail}
      </span>
      {recoverable ? (
        <button
          type="button"
          className="recovery-action"
          aria-label="恢复工作区"
          onClick={onRecover}
        >
          恢复
        </button>
      ) : null}
      <BuildProgress state={state} />
      <span className="visually-hidden">
        {runtime === "tauri" ? "Microsoft Word 桌面" : "浏览器工作区"}
      </span>
    </section>
  );
}

export function BuildProgress({ state }: { state: WorkspaceState }) {
  const stages = [
    ["parse", "解析"],
    ["validate", "验证"],
    ["compile", "编译"],
    ["render", "渲染"],
    ["finalize", "完成"],
  ] as const;
  const completed = new Set(state.buildProgress);
  const complete =
    state.output !== null &&
    state.operation === null &&
    state.buildErrorKind === null;
  return (
    <div
      className="build-progress-shell"
      role="status"
      aria-label="构建进度"
    >
      <span>
        {state.operation?.kind === "build"
          ? "构建中"
          : complete
            ? "构建完成"
            : "等待构建"}
      </span>
      <div aria-hidden="true">
        {stages.map(([stage, label]) => (
          <i key={stage} title={label} data-complete={completed.has(stage)}>
            <span className="visually-hidden">{label}</span>
          </i>
        ))}
      </div>
    </div>
  );
}

import type { RuntimeKind } from "../transport/dto";
import type { WorkspaceState } from "../state/workspace";

interface StatusStripProps {
  state: WorkspaceState;
  runtime: RuntimeKind;
  title: string;
  detail: string;
  onRecover(): void;
  onTemplateSelected(templateId: string | null): void;
}

export function StatusStrip({
  state,
  runtime,
  title,
  detail,
  onRecover,
  onTemplateSelected,
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
        <TemplateSelector
          value={state.templateId}
          disabled={
            !state.source ||
            !state.source.reference ||
            state.dirty ||
            state.status === "loading"
          }
          onSelected={onTemplateSelected}
        />
        <div className="runtime-chip">
          {runtime === "tauri" ? "本地桌面" : "Web 工作区"}
        </div>
      </div>
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

export function TemplateSelector({
  value,
  disabled,
  onSelected,
}: {
  value: string | null;
  disabled: boolean;
  onSelected(templateId: string | null): void;
}) {
  return (
    <label className="template-control">
      <span>学校模板</span>
      <select
        aria-label="学校模板"
        value={value ?? ""}
        disabled={disabled}
        onChange={(event) => onSelected(event.currentTarget.value || null)}
      >
        <option value="">使用文稿声明模板</option>
        <option value="bachelor-base">基础本科论文模板</option>
        <option value="example-university-2026">
          示例大学 2026 模板
        </option>
      </select>
    </label>
  );
}

import { FileText, FolderOpen, Hammer, Save, Search, X } from "lucide-react";
import type { ReactNode, RefObject } from "react";
import type {
  WorkspaceActions,
  WorkspaceState,
} from "../state/workspace";

interface ProductBarProps {
  state: WorkspaceState;
  actions: WorkspaceActions;
  fileInputRef: RefObject<HTMLInputElement | null>;
  onChooseSource(): void;
  onFileSelected(files: File[]): void;
  onSave(): void;
  onValidate(): void;
  onBuild(): void;
  onCancel(): void;
  onTemplateSelected(templateId: string | null): void;
  children?: ReactNode;
}

export function ProductBar({
  state,
  actions,
  fileInputRef,
  onChooseSource,
  onFileSelected,
  onSave,
  onValidate,
  onBuild,
  onCancel,
  onTemplateSelected,
  children,
}: ProductBarProps) {
  return (
    <header className="product-bar">
      <div className="brand-block">
        <div className="brand-mark" aria-hidden="true">
          DF
        </div>
        <div>
          <strong>DocForge</strong>
          <span>Markdown → Word 文档工坊</span>
        </div>
      </div>
      <div className="document-identity">
        <span className="document-presence" aria-hidden="true" />
        <FileText aria-hidden="true" />
        <div>
          <strong>
            {state.project?.name ?? state.source?.name ?? "尚未打开项目"}
          </strong>
          <span>
            {state.project ? `活动源：${state.source?.name} · ` : ""}
            {state.dirty ? "有未保存修改" : "文档已保存"}
          </span>
        </div>
      </div>
      {children}
      <div className="primary-actions" role="toolbar" aria-label="文档操作">
        <input
          ref={fileInputRef}
          className="visually-hidden"
          type="file"
          accept=".yaml,.yml,.md,text/yaml,text/markdown"
          multiple
          tabIndex={-1}
          onChange={(event) => {
            const files = Array.from(event.currentTarget.files ?? []);
            if (files.length > 0) {
              onFileSelected(files);
            }
            event.currentTarget.value = "";
          }}
        />
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
        <button
          type="button"
          className="button secondary open-action"
          disabled={!actions.canOpen}
          onClick={onChooseSource}
          aria-label="打开 Markdown 或 DocForge 项目"
        >
          <FolderOpen aria-hidden="true" />
          打开
        </button>
        <button
          type="button"
          className="button secondary"
          disabled={!actions.canSave}
          aria-label="保存文档"
          onClick={onSave}
        >
          <Save aria-hidden="true" />
          保存
        </button>
        <button
          type="button"
          className="button secondary"
          disabled={!actions.canValidate}
          aria-label="检查文档"
          onClick={onValidate}
        >
          <Search aria-hidden="true" />
          检查
        </button>
        {state.operation?.kind === "build" && actions.canCancel ? (
          <button
            type="button"
            className="button secondary"
            aria-label="取消构建"
            onClick={onCancel}
          >
            <X aria-hidden="true" />
            取消构建
          </button>
        ) : null}
        <button
          type="button"
          className="button primary"
          disabled={!actions.canBuild}
          aria-label="生成 DOCX"
          onClick={onBuild}
        >
          <Hammer aria-hidden="true" />
          生成 DOCX
        </button>
      </div>
    </header>
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
      <span>模板</span>
      <select
        aria-label="Word 模板"
        value={value ?? ""}
        disabled={disabled}
        onChange={(event) => onSelected(event.currentTarget.value || null)}
      >
        <option value="">使用项目声明模板</option>
        <option value="bachelor-base">基础 Word 模板</option>
        <option value="example-university-2026">示例大学 2026 模板</option>
      </select>
    </label>
  );
}

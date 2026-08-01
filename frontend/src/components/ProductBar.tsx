import { FileText, FolderOpen, Hammer, Save, Search, X } from "lucide-react";
import type { RefObject } from "react";
import type {
  WorkspaceActions,
  WorkspaceState,
} from "../state/workspace";

interface ProductBarProps {
  state: WorkspaceState;
  actions: WorkspaceActions;
  fileInputRef: RefObject<HTMLInputElement | null>;
  onChooseSource(): void;
  onFileSelected(file: File): void;
  onSave(): void;
  onValidate(): void;
  onBuild(): void;
  onCancel(): void;
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
}: ProductBarProps) {
  return (
    <header className="product-bar">
      <div className="brand-block">
        <div className="brand-mark" aria-hidden="true">
          TF
        </div>
        <div>
          <strong>ThesisForge</strong>
          <span>确定性论文编译工作台</span>
        </div>
      </div>
      <div className="document-identity">
        <FileText aria-hidden="true" />
        <div>
          <strong>{state.source?.name ?? "尚未打开文稿"}</strong>
          <span>{state.dirty ? "有未保存修改" : "保存快照已同步"}</span>
        </div>
      </div>
      <div className="primary-actions" role="toolbar" aria-label="文稿操作">
        <input
          ref={fileInputRef}
          className="visually-hidden"
          type="file"
          accept=".md,text/markdown,text/plain"
          tabIndex={-1}
          onChange={(event) => {
            const file = event.currentTarget.files?.[0];
            if (file) {
              onFileSelected(file);
            }
            event.currentTarget.value = "";
          }}
        />
        <button
          type="button"
          className="button secondary open-action"
          disabled={!actions.canOpen}
          onClick={onChooseSource}
          aria-label="打开 Markdown 文稿"
        >
          <FolderOpen aria-hidden="true" />
          打开
        </button>
        <button
          type="button"
          className="button secondary"
          disabled={!actions.canSave}
          aria-label="保存文稿"
          onClick={onSave}
        >
          <Save aria-hidden="true" />
          保存
        </button>
        <button
          type="button"
          className="button secondary"
          disabled={!actions.canValidate}
          aria-label="验证论文"
          onClick={onValidate}
        >
          <Search aria-hidden="true" />
          验证
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
          aria-label="构建 DOCX"
          onClick={onBuild}
        >
          <Hammer aria-hidden="true" />
          构建 DOCX
        </button>
      </div>
    </header>
  );
}

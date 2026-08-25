import {
  CheckCircle2,
  FileText,
  FileWarning,
  LoaderCircle,
  RefreshCw,
  Search,
  Upload,
} from "lucide-react";
import {
  useMemo,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import type {
  ContentSelection,
  OutlineItem,
} from "../state/preview";
import type {
  PreviewMode,
  WorkspaceState,
} from "../state/workspace";
import type {
  SerializedPreviewBlock,
  SerializedPreviewContent,
  SerializedPreviewMarker,
  SerializedPreviewRun,
} from "../transport/dto";
import { PanelHeader } from "./PanelHeader";
import { ReviewPanel } from "./ReviewPanel";
import { usePdfObjectUrl } from "./usePdfObjectUrl";

interface PreviewPanelProps {
  state: WorkspaceState;
  onActivated(selection: ContentSelection): void;
}

function activateOnKeyboard(
  event: KeyboardEvent<HTMLElement>,
  activate: () => void,
) {
  if (event.key !== "Enter" && event.key !== " ") {
    return;
  }
  event.preventDefault();
  activate();
}

function MarkerList({ markers }: { markers: SerializedPreviewMarker[] }) {
  if (markers.length === 0) {
    return null;
  }
  return (
    <span className="preview-markers">
      {markers.map((marker) => (
        <span
          key={`${marker.severity}:${marker.code}`}
          className="preview-marker"
          data-severity={marker.severity}
          aria-label={`${marker.severity} ${marker.code}`}
          title={marker.code}
        />
      ))}
    </span>
  );
}

function selection(item: OutlineItem | SerializedPreviewBlock): ContentSelection {
  return { selectionId: item.selectionId, line: item.line };
}

export function OutlinePanel({ state, onActivated }: PreviewPanelProps) {
  const [query, setQuery] = useState("");
  const visibleOutline = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    if (!normalized) {
      return state.outline;
    }
    return state.outline.filter((item) =>
      `${item.text} ${item.semanticId ?? ""}`
        .toLocaleLowerCase()
        .includes(normalized),
    );
  }, [query, state.outline]);

  return (
    <aside
      className="panel outline-panel"
      aria-label="文档大纲"
      data-mobile-active={state.mobilePanel === "outline"}
    >
      <div className="outline-toolbar">
        <strong>文档大纲</strong>
        <span aria-hidden="true">×</span>
      </div>
      <div className="outline-content">
        <label className="outline-search">
          <Search aria-hidden="true" />
          <span className="visually-hidden">搜索标题</span>
          <input
            type="search"
            value={query}
            placeholder="搜索标题..."
            onChange={(event) => setQuery(event.currentTarget.value)}
          />
        </label>
        {state.outline.length === 0 ? (
          <p className="outline-message">
            打开并保存 Markdown 后，将显示带稳定语义 ID 的文档结构。
          </p>
        ) : (
          <nav className="outline-tree" aria-label="文档标题结构">
            {visibleOutline.map((item) => (
              <button
                key={item.selectionId}
                type="button"
                className="outline-item"
                style={{ "--outline-level": item.level } as CSSProperties}
                aria-pressed={state.activeSelectionId === item.selectionId}
                aria-label={`${item.text} ${
                  item.line === null ? "无行号" : `第 ${item.line} 行`
                }`}
                onClick={() => onActivated(selection(item))}
              >
                <span>{item.text}</span>
                <code>{item.semanticId ?? `L${item.line ?? "-"}`}</code>
                <MarkerList markers={item.markers} />
              </button>
            ))}
          </nav>
        )}
        {state.outline.length > 0 && visibleOutline.length === 0 ? (
          <p className="outline-message">没有匹配的标题。</p>
        ) : null}
      </div>
      <div className="panel-footer">
        <span>共 {state.outline.length} 个标题</span>
        <code>{state.source?.name ?? "未打开"}</code>
      </div>
    </aside>
  );
}

function formattedTextRun(
  run: Extract<SerializedPreviewRun, { type: "text" }>,
): ReactNode {
  let body: ReactNode = run.text;
  if (run.code) {
    body = <code className="preview-inline-code">{body}</code>;
  }
  if (run.italic) {
    body = <em>{body}</em>;
  }
  if (run.bold) {
    body = <strong>{body}</strong>;
  }
  return body;
}

function Runs({ runs }: { runs: SerializedPreviewRun[] }) {
  return (
    <>
      {runs.map((run, index) => {
        const key = `${run.type}:${index}`;
        if (run.type === "text") {
          return <span key={key}>{formattedTextRun(run)}</span>;
        }
        if (run.type === "reference") {
          return (
            <span key={key} className="preview-reference" title={run.targetId}>
              {run.text}
            </span>
          );
        }
        if (run.type === "citation") {
          return (
            <span key={key} className="preview-citation" title={run.keys.join(", ")}>
              {run.text}
            </span>
          );
        }
        if (run.type === "footnote-reference") {
          return (
            <sup key={key} title={run.label}>
              {run.footnoteId}
            </sup>
          );
        }
        if (run.type === "hyperlink") {
          return (
            <a key={key} href={run.destination}>
              {run.text}
            </a>
          );
        }
        if (run.type === "math") {
          return (
            <span key={key} className="preview-math">
              {run.text}
            </span>
          );
        }
        if (run.type === "soft-break") {
          return (
            <span key={key} className="preview-soft-break">
              {" "}
            </span>
          );
        }
        if (run.type === "hard-break") {
          return <br key={key} className="preview-hard-break" />;
        }
        return null;
      })}
    </>
  );
}

function Content({ content }: { content: SerializedPreviewContent }) {
  if (content.type === "cover") {
    return (
      <div className="preview-cover">
        {content.fields.map((field) => (
          <p key={field.label}>
            <span>{field.label}</span>
            <strong>{field.value}</strong>
          </p>
        ))}
      </div>
    );
  }
  if (content.type === "section") {
    return <div className="preview-section-break">分节：{content.role}</div>;
  }
  if (content.type === "toc") {
    return (
      <div className="preview-toc">
        目录（H{content.minLevel}-H{content.maxLevel}）
      </div>
    );
  }
  if (content.type === "code-block") {
    return (
      <pre
        className="preview-code-block"
        data-language={content.language ?? ""}
      >
        {content.code}
      </pre>
    );
  }
  if (content.type === "blockquote") {
    return (
      <blockquote className="preview-blockquote">
        {content.children.map((child, index) => (
          <div
            key={`${child.kind}:${index}`}
            className="preview-blockquote-child"
            data-kind={child.kind}
            data-preview-state={child.state}
          >
            <Content content={child.content} />
          </div>
        ))}
      </blockquote>
    );
  }
  if (content.type === "text") {
    const body = content.runs.length ? <Runs runs={content.runs} /> : content.text;
    if (content.level !== null) {
      return <h3 data-level={content.level}>{body}</h3>;
    }
    return <p>{body}</p>;
  }
  if (content.type === "list") {
    const ListTag = content.ordered ? "ol" : "ul";
    return (
      <ListTag start={content.ordered ? (content.start ?? undefined) : undefined}>
        {content.items.map((item, index) => (
          <li key={`${item.ordinal ?? index}:${item.text}`} data-level={item.level}>
            {item.runs.length ? <Runs runs={item.runs} /> : item.text}
          </li>
        ))}
      </ListTag>
    );
  }
  if (content.type === "figure") {
    return (
      <figure data-available={content.available}>
        <div className="preview-figure-placeholder">
          {content.available ? "本地图片资源" : "图片资源不可用"}
        </div>
        <figcaption>
          <strong>{content.label}</strong>
          <span>{content.caption}</span>
          <code>{content.src}</code>
        </figcaption>
      </figure>
    );
  }
  if (content.type === "table") {
    return (
      <figure>
        <figcaption>
          <strong>{content.label}</strong>
          <span>{content.caption}</span>
        </figcaption>
        <table>
          <tbody>
            {content.rows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.cells.map((cell, cellIndex) => {
                  const Cell = row.header ? "th" : "td";
                  return (
                    <Cell key={cellIndex} style={{ textAlign: cell.alignment ?? "left" }}>
                      {cell.text}
                    </Cell>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </figure>
    );
  }
  if (content.type === "equation") {
    return (
      <div className="preview-equation">
        <code>{content.latex}</code>
        <span>{content.label}</span>
      </div>
    );
  }
  if (content.type === "listing") {
    return (
      <figure>
        <figcaption>{content.caption}</figcaption>
        <pre data-language={content.language ?? ""}>{content.code}</pre>
      </figure>
    );
  }
  if (content.type === "algorithm") {
    return (
      <figure>
        <figcaption>{content.caption}</figcaption>
        <pre>{content.body}</pre>
      </figure>
    );
  }
  if (content.type === "footnote") {
    return (
      <p className="preview-footnote">
        <sup>{content.footnoteId}</sup>
        {content.runs.length ? <Runs runs={content.runs} /> : content.text}
      </p>
    );
  }
  if (content.type === "bibliography") {
    return (
      <ol className="preview-bibliography">
        {content.entries.map((entry) => (
          <li key={entry.key} value={entry.ordinal}>
            {entry.text}
          </li>
        ))}
      </ol>
    );
  }
  return (
    <div className="preview-unsupported">
      <code>{content.originalKind}</code>
      <strong>暂不支持此结构类型</strong>
    </div>
  );
}

function contentLabel(content: SerializedPreviewContent): string {
  if (content.type === "text") return content.text;
  if (content.type === "figure" || content.type === "table") {
    return content.caption || content.label;
  }
  if (content.type === "equation") return content.label || content.latex;
  if (content.type === "listing" || content.type === "algorithm") {
    return content.caption;
  }
  if (content.type === "footnote") return `脚注 ${content.footnoteId}`;
  if (content.type === "bibliography") return "参考文献";
  if (content.type === "cover") return "文档封面";
  if (content.type === "section") return `分节 ${content.role}`;
  if (content.type === "toc") return "目录";
  if (content.type === "code-block") return "代码块";
  if (content.type === "blockquote") return "引用块";
  if (content.type === "list") return "列表";
  return content.originalKind;
}

function PreviewBlock({
  block,
  active,
  onActivated,
}: {
  block: SerializedPreviewBlock;
  active: boolean;
  onActivated(selection: ContentSelection): void;
}) {
  const activate = () => onActivated(selection(block));
  return (
    <section
      className="preview-block"
      data-kind={block.kind}
      data-preview-state={block.state}
      role="button"
      tabIndex={0}
      aria-pressed={active}
      aria-label={`${contentLabel(block.content)} ${
        block.line === null ? "无行号" : `第 ${block.line} 行`
      }`}
      onClick={activate}
      onKeyDown={(event) => activateOnKeyboard(event, activate)}
    >
      <MarkerList markers={block.markers} />
      <Content content={block.content} />
    </section>
  );
}

export function PaperPreview({ state, onActivated }: PreviewPanelProps) {
  return (
    <section
      className="panel preview-panel"
      role="region"
      aria-label="文档结构预览"
      data-mobile-active={state.mobilePanel === "preview"}
    >
      <div className="preview-standalone-title">文档结构预览</div>
      <PaperPreviewBody state={state} onActivated={onActivated} />
    </section>
  );
}

function PaperPreviewBody({ state, onActivated }: PreviewPanelProps) {
  const preview = state.preview;
  return (
    <div className="paper-stage">
      <article className="paper">
        <span className="paper-running-head">DocForge · 文档结构预览</span>
        <div className="structure-preview-warning" role="note">
          快速结构预览，不代表 Microsoft Word 最终排版与分页
        </div>
        {preview.status === "empty" ? (
          <div className="preview-message">
            <h1>等待载入文档</h1>
            <p>打开文档后，预览与大纲将来自同一保存快照。</p>
          </div>
        ) : preview.status === "blocked" ? (
          <div className="preview-message preview-message-blocked">
            <h1>结构预览暂不可用</h1>
            <p>{preview.message}</p>
          </div>
        ) : (
          <div className="preview-document">
            {preview.blocks.map((block) => (
              <PreviewBlock
                key={block.selectionId}
                block={block}
                active={state.activeSelectionId === block.selectionId}
                onActivated={onActivated}
              />
            ))}
          </div>
        )}
        <div className="paper-rule" />
        <p className="paper-note">{preview.disclaimer}</p>
      </article>
    </div>
  );
}

export function PreviewModeControl({
  mode,
  onChanged,
}: {
  mode: PreviewMode;
  onChanged(mode: PreviewMode): void;
}) {
  return (
    <div
      className="preview-mode-control"
      role="tablist"
      aria-label="预览模式"
      style={{ gridTemplateColumns: "repeat(3, auto)" }}
    >
      <button
        type="button"
        role="tab"
        aria-selected={mode === "structure"}
        onClick={() => onChanged("structure")}
      >
        结构
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === "final-layout"}
        onClick={() => onChanged("final-layout")}
      >
        实时版式
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === "review"}
        onClick={() => onChanged("review")}
      >
        审阅
      </button>
    </div>
  );
}

function FinalPreviewActions({
  onBuild,
}: {
  onBuild(): void;
}) {
  return (
    <div className="final-preview-actions">
      <button type="button" className="button secondary" onClick={onBuild}>
        <RefreshCw aria-hidden="true" />
        立即刷新预览
      </button>
    </div>
  );
}

export function FinalLayoutPreview({
  state,
  onBuild,
  onSelectOfficePdf,
}: {
  state: WorkspaceState;
  onBuild(): void;
  onSelectOfficePdf(): void;
}) {
  const preview = state.finalPreview;
  const objectUrl = usePdfObjectUrl(preview.bytes);
  const building =
    state.operation?.kind === "build" || preview.status === "building";

  return (
    <div className="final-preview" data-preview-status={building ? "building" : preview.status}>
      {preview.status === "stale" && objectUrl ? (
        <div className="final-preview-banner" role="status">
          <span>预览已过期。{preview.message}</span>
          <button type="button" onClick={onBuild}>
            立即刷新
          </button>
        </div>
      ) : null}
      {building && objectUrl ? (
        <div className="final-preview-banner final-preview-banner-live" role="status">
          <LoaderCircle className="spin" aria-hidden="true" />
          <span>{preview.message ?? "正在生成最新 PDF，当前仍显示上一版页面。"}</span>
        </div>
      ) : null}
      {preview.status === "ready" && objectUrl && preview.message ? (
        <div className="final-preview-banner" role="alert">
          <span>{preview.message}</span>
          <button type="button" onClick={onSelectOfficePdf}>
            重新选择
          </button>
        </div>
      ) : null}

      {objectUrl &&
      (preview.status === "ready" ||
        preview.status === "stale" ||
        preview.status === "building") ? (
        <iframe
          className="final-preview-frame"
          title="最终版式 PDF"
          src={objectUrl}
        />
      ) : building ? (
        <div className="final-preview-state" role="status">
          <LoaderCircle className="spin" aria-hidden="true" />
          <h3>正在生成最终版式</h3>
          <p>正在根据当前编辑内容生成临时 DOCX 与真实 PDF 页面。</p>
        </div>
      ) : (
        <div className="final-preview-state">
          <FileWarning aria-hidden="true" />
          <h3>
            {preview.status === "failed"
              ? "最终预览加载失败"
              : preview.status === "unavailable"
                ? "Microsoft Word PDF 未生成"
                : "尚无最终版式"}
          </h3>
          <p>
            {preview.message ??
              "桌面端使用 Microsoft Word 生成实时 PDF；也可选择从 Word 导出的 PDF。"}
          </p>
          <FinalPreviewActions onBuild={onBuild} />
        </div>
      )}
    </div>
  );
}

export function DualPreviewPanel({
  state,
  onActivated,
  onModeChanged,
  onBuild,
  onSelectOfficePdf,
}: PreviewPanelProps & {
  onModeChanged(mode: PreviewMode): void;
  onBuild(): void;
  onSelectOfficePdf(): void;
}) {
  const finalLayout = state.previewMode === "final-layout";
  const reviewMode = state.previewMode === "review";
  const preview = state.finalPreview;
  const building =
    state.operation?.kind === "build" || preview.status === "building";
  const statusLabel = building
    ? "实时更新中"
    : preview.status === "ready"
      ? "当前 Word 预览"
      : preview.status === "stale"
        ? "已过期"
        : preview.status === "failed"
          ? "失败"
          : preview.status === "unavailable"
            ? "不可用"
            : "未生成";
  return (
    <section
      className="panel preview-panel dual-preview-panel"
      role="region"
      aria-label={
        finalLayout
          ? "Microsoft Word 版式预览"
          : reviewMode
            ? "文档内容审阅"
            : "文档结构预览"
      }
      data-mobile-active={state.mobilePanel === "preview"}
    >
      <div className="preview-panel-toolbar">
        <div className="word-compatibility">
          <CheckCircle2 aria-hidden="true" />
          <strong>Microsoft Word 兼容</strong>
          {preview.descriptor ? (
            <span className="preview-engine-label">
              {preview.descriptor.label}
            </span>
          ) : null}
          <span>{statusLabel}</span>
        </div>
        <div className="preview-toolbar-actions">
          <PreviewModeControl mode={state.previewMode} onChanged={onModeChanged} />
          <button
            type="button"
            className="preview-pdf-action"
            aria-label="选择 Word PDF"
            onClick={onSelectOfficePdf}
          >
            <Upload aria-hidden="true" />
            <span>选择 PDF</span>
          </button>
        </div>
      </div>
      {finalLayout ? (
        <FinalLayoutPreview
          state={state}
          onBuild={onBuild}
          onSelectOfficePdf={onSelectOfficePdf}
        />
      ) : reviewMode ? (
        <ReviewPanel state={state} onActivated={onActivated} />
      ) : (
        <PaperPreviewBody state={state} onActivated={onActivated} />
      )}
    </section>
  );
}

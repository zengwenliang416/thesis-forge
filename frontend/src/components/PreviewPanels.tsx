import { BookOpen, FileText, PanelRight } from "lucide-react";
import type { CSSProperties, KeyboardEvent } from "react";
import type {
  ContentSelection,
  OutlineItem,
} from "../state/preview";
import type { WorkspaceState } from "../state/workspace";
import type {
  SerializedPreviewBlock,
  SerializedPreviewContent,
  SerializedPreviewMarker,
  SerializedPreviewRun,
} from "../transport/dto";
import { PanelHeader } from "./PanelHeader";

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
  return (
    <aside
      className="panel outline-panel"
      aria-label="论文大纲"
      data-mobile-active={state.mobilePanel === "outline"}
    >
      <PanelHeader icon={<BookOpen />} kicker="THESIS DOCUMENT" title="论文大纲" />
      <div className="outline-content">
        <div className="outline-root">
          <FileText aria-hidden="true" />
          <span>{state.source?.name ?? "等待载入文稿"}</span>
        </div>
        {state.outline.length === 0 ? (
          <p className="outline-message">
            打开并保存 Markdown 后，将显示带稳定语义 ID 的论文结构。
          </p>
        ) : (
          <nav className="outline-tree" aria-label="论文标题结构">
            {state.outline.map((item) => (
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
      </div>
      <div className="panel-footer">
        <span>协议</span>
        <code>workbench.v1</code>
      </div>
    </aside>
  );
}

function Runs({ runs }: { runs: SerializedPreviewRun[] }) {
  return (
    <>
      {runs.map((run, index) => {
        const key = `${run.type}:${index}`;
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
        return <span key={key}>{run.text}</span>;
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
  if (content.type === "cover") return "论文封面";
  if (content.type === "section") return `分节 ${content.role}`;
  if (content.type === "toc") return "目录";
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
  const preview = state.preview;
  return (
    <section
      className="panel preview-panel"
      role="region"
      aria-label="论文结构预览"
      data-mobile-active={state.mobilePanel === "preview"}
    >
      <PanelHeader
        icon={<PanelRight />}
        kicker="RENDER PLAN"
        title="论文结构预览"
      />
      <div className="paper-stage">
        <article className="paper">
          <span className="paper-running-head">本科毕业论文 · 结构预览</span>
          {preview.status === "empty" ? (
            <div className="preview-message">
              <h1>等待载入论文</h1>
              <p>打开文稿后，预览与大纲将来自同一保存快照。</p>
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
    </section>
  );
}

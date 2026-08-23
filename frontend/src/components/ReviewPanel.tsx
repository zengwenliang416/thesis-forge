import { BookOpen } from "lucide-react";
import type { KeyboardEvent, ReactNode } from "react";
import type { ContentSelection } from "../state/preview";
import type { WorkspaceState } from "../state/workspace";
import type {
  SerializedPreviewBlock,
  SerializedPreviewContent,
  SerializedPreviewRun,
} from "../transport/dto";
import { PanelHeader } from "./PanelHeader";

export interface ReviewPanelProps {
  state: WorkspaceState;
  onActivated(selection: ContentSelection): void;
}

const TECHNICAL_MARKER_RE =
  /\[@[^\]]+\]|\{#[A-Za-z0-9_.:-]+\}|(?<![\w-])@?(?:fig|tbl|eq|sec|chap|lst|alg|para|fn|ref|footnote|citation|table|figure|equation|section|chapter|listing|algorithm|source|target|selection|node|line|bookmark|span|kind|status|project|asset):[A-Za-z0-9_.-]+|(?<![\w])@[A-Za-z][A-Za-z0-9_.-]*/g;
const TECHNICAL_MARKER_TEST_RE =
  /\[@[^\]]+\]|\{#[A-Za-z0-9_.:-]+\}|(?<![\w-])@?(?:fig|tbl|eq|sec|chap|lst|alg|para|fn|ref|footnote|citation|table|figure|equation|section|chapter|listing|algorithm|source|target|selection|node|line|bookmark|span|kind|status|project|asset):[A-Za-z0-9_.-]+|(?<![\w])@[A-Za-z][A-Za-z0-9_.-]*/;
const FOOTNOTE_MARKER_RE = /\[\^[^\]]+\]/g;
const ABSOLUTE_PATH_RE =
  /(?<![\w:])\/[A-Za-z0-9._~-]+(?:\/[A-Za-z0-9._~:+-]+)+(?:[^\s]*)?/g;
const WINDOWS_PATH_RE = /(?<![\w])(?:[A-Za-z]:\\|\\\\)[^\s]+/g;
const UNSAFE_URL_METADATA_RE = /[?#%]/;
const UNSAFE_URL_PATH_RE =
  /\/(?:source|target|selection|node|line)(?:\/|$)|\/[A-Za-z0-9_.-]*(?:key|cite|citation|ref|reference)[A-Za-z0-9_.-]*(?:\/|$)/i;
const UNSAFE_URL_TOKEN_RE =
  /\b[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*[-_.](?:key|cite|citation|ref|reference)\b|\b(?:cite|citation|ref|reference|secret)[-_.][A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*\b/i;
const OPAQUE_CITATION_KEY_RE =
  /\b[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*[-_.](?:key|cite|citation|ref|reference)\b|\b(?:cite|citation|ref|reference|secret)[-_.][A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*\b/gi;
const OPAQUE_TECHNICAL_TOKEN_RE =
  /\b[A-Za-z][A-Za-z0-9_.-]*-[A-Za-z0-9_.-]+\b/g;
const MATH_SYMBOLS: Record<string, string> = {
  alpha: "α",
  approx: "≈",
  beta: "β",
  cdot: "·",
  chi: "χ",
  delta: "δ",
  epsilon: "ε",
  geq: "≥",
  gamma: "γ",
  infty: "∞",
  int: "∫",
  lambda: "λ",
  leq: "≤",
  leftarrow: "←",
  mu: "μ",
  neq: "≠",
  omega: "ω",
  phi: "φ",
  pi: "π",
  pm: "±",
  prod: "∏",
  rightarrow: "→",
  sigma: "σ",
  sqrt: "√",
  sum: "∑",
  theta: "θ",
  times: "×",
  to: "→",
};

function readerText(value: string, strict = false): string {
  const cleaned = value
    .replace(TECHNICAL_MARKER_RE, "")
    .replace(FOOTNOTE_MARKER_RE, "脚注")
    .replace(ABSOLUTE_PATH_RE, "")
    .replace(WINDOWS_PATH_RE, "")
    .replace(OPAQUE_CITATION_KEY_RE, "")
    .replace(/[ \t]{2,}/g, " ");
  return (strict ? cleaned.replace(OPAQUE_TECHNICAL_TOKEN_RE, "") : cleaned)
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

function mathText(latex: string): string {
  let value = latex
    .replace(/\\\\/g, "\n")
    .replace(/\\\(|\\\)/g, "")
    .replace(/\${1,2}/g, "")
    .replace(/\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}/g, "($1)/($2)")
    .replace(/\\sqrt\s*\{([^{}]*)\}/g, "√($1)")
    .replace(/\\(?:mathrm|mathbf|mathit)\s*\{([^{}]*)\}/g, "$1")
    .replace(/\\(?:operatorname|text)\s*\{([^{}]*)\}/g, "$1")
    .replace(/\\(?:left|right)\b/g, "")
    .replace(/\\([A-Za-z]+)\b/g, (_, command: string) => {
      return MATH_SYMBOLS[command] ?? command;
    })
    .replace(/\^\{([^{}]*)\}/g, "^$1")
    .replace(/_\{([^{}]*)\}/g, "_$1")
    .replace(/\\[,;!:]/g, " ")
    .replace(/[{}]/g, "")
    .replace(/\\/g, "");
  value = readerText(value)
    .replace(/[ \t]*\n[ \t]*/g, "\n")
    .replace(/[ \t]{2,}/g, " ");
  return value || "公式";
}

function safeHref(destination: string): string | undefined {
  const value = destination.trim();
  return /^https?:/i.test(value) &&
    !UNSAFE_URL_METADATA_RE.test(value) &&
    !UNSAFE_URL_PATH_RE.test(value) &&
    !UNSAFE_URL_TOKEN_RE.test(value) &&
    !TECHNICAL_MARKER_TEST_RE.test(value)
    ? value
    : undefined;
}

function safeImageSource(source: string): string | undefined {
  const value = source.trim();
  return /^https?:\/\//i.test(value) &&
    !UNSAFE_URL_METADATA_RE.test(value) &&
    !UNSAFE_URL_PATH_RE.test(value) &&
    !UNSAFE_URL_TOKEN_RE.test(value) &&
    !TECHNICAL_MARKER_TEST_RE.test(value)
    ? value
    : undefined;
}

function citationText(run: Extract<SerializedPreviewRun, { type: "citation" }>) {
  const text = readerText(run.text);
  const includesCitationKey = run.keys.some(
    (key) => key.length > 0 && text.includes(key),
  );
  if (
    text &&
    !TECHNICAL_MARKER_TEST_RE.test(run.text) &&
    !includesCitationKey
  ) {
    return text;
  }
  if (run.ordinals.length > 0) {
    return `[${run.ordinals.join(", ")}]`;
  }
  return "引用";
}

function bibliographyText(
  text: string,
  key: string,
  ordinal: number,
): string {
  const visible = readerText(text);
  const withoutKey = key ? readerText(visible.split(key).join("")) : visible;
  return withoutKey || `参考文献 ${ordinal}`;
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

function ReviewRuns({ runs }: { runs: SerializedPreviewRun[] }) {
  return (
    <>
      {runs.map((run, index) => {
        const key = `${run.type}-${index}`;
        switch (run.type) {
          case "hyperlink": {
            const text = readerText(run.text) || "链接";
            const href = safeHref(run.destination);
            return href ? (
              <a key={key} href={href}>
                {text}
              </a>
            ) : (
              <span key={key}>{text}</span>
            );
          }
          case "math": {
            const text = mathText(run.text || run.latex);
            return (
              <span key={key} className="review-math" aria-label={text}>
                {text}
              </span>
            );
          }
          case "footnote-reference":
            return (
              <sup key={key} title={`脚注 ${run.footnoteId}`}>
                {readerText(run.text) || `脚注${run.footnoteId}`}
              </sup>
            );
          case "soft-break":
            return (
              <span key={key} className="review-soft-break">
                {" "}
              </span>
            );
          case "hard-break":
            return <br key={key} className="review-hard-break" />;
          case "text":
            return <span key={key}>{readerText(run.text)}</span>;
          case "reference":
            return <span key={key}>{readerText(run.text) || "引用"}</span>;
          case "citation":
            return <span key={key}>{citationText(run)}</span>;
        }
      })}
    </>
  );
}

function textBody(text: string, runs: SerializedPreviewRun[]): ReactNode {
  return runs.length ? <ReviewRuns runs={runs} /> : readerText(text);
}

function headingTag(
  level: number | null,
): "h1" | "h2" | "h3" | "h4" | "h5" | "h6" {
  const safeLevel = Math.min(6, Math.max(1, level ?? 2));
  return `h${safeLevel}` as "h1" | "h2" | "h3" | "h4" | "h5" | "h6";
}

function sectionLabel(role: "cover" | "front_matter" | "main"): string {
  switch (role) {
    case "cover":
      return "封面";
    case "front_matter":
      return "前置内容";
    case "main":
      return "正文";
  }
}

function contentLabel(content: SerializedPreviewContent): string {
  switch (content.type) {
    case "text":
      return readerText(content.text) || "正文";
    case "list":
      return "列表";
    case "figure":
    case "table":
      return readerText(content.caption) || readerText(content.label) || "内容";
    case "equation":
      return readerText(content.label) || "公式";
    case "listing":
    case "algorithm":
      return readerText(content.caption) || "代码内容";
    case "footnote":
      return `脚注 ${content.footnoteId}`;
    case "bibliography":
      return "参考文献";
    case "cover":
      return "论文封面";
    case "section":
      return sectionLabel(content.role);
    case "toc":
      return "目录";
    case "unsupported":
      return "无法显示的内容";
  }
}

function ReviewContent({ content }: { content: SerializedPreviewContent }) {
  switch (content.type) {
    case "cover":
      return (
        <div className="review-cover">
          {content.fields.map((field, index) => (
            <p key={`${field.label}-${index}`}>
              <span>{readerText(field.label)}</span>
              <strong>{readerText(field.value)}</strong>
            </p>
          ))}
        </div>
      );
    case "section":
      return (
        <div className="review-section" aria-label={sectionLabel(content.role)}>
          <span>{sectionLabel(content.role)}</span>
        </div>
      );
    case "toc":
      return <div className="review-toc">目录</div>;
    case "text": {
      const body = textBody(content.text, content.runs);
      if (content.level === null) {
        return <p>{body}</p>;
      }
      const Heading = headingTag(content.level);
      return <Heading>{body}</Heading>;
    }
    case "list": {
      const ListTag = content.ordered ? "ol" : "ul";
      return (
        <ListTag
          start={content.ordered ? (content.start ?? undefined) : undefined}
        >
          {content.items.map((item, index) => (
            <li key={`${item.ordinal ?? index}:${item.text}`}>
              {textBody(item.text, item.runs)}
            </li>
          ))}
        </ListTag>
      );
    }
    case "figure":
      {
        const label = readerText(content.label) || "图片";
        const caption = readerText(content.caption);
        const alternative = [label, caption].filter(Boolean).join(" ");
        const source = content.available
          ? safeImageSource(content.src)
          : undefined;
        return (
          <figure>
            {source ? (
              <img
                className="review-figure"
                src={source}
                alt={alternative}
              />
            ) : (
              <div
                className="review-figure-placeholder"
                role="img"
                aria-label={alternative}
              >
                {content.available ? "图片资源" : "图片资源暂不可用"}
              </div>
            )}
            <figcaption>
              <strong>{label}</strong>
              {caption ? <span>{caption}</span> : null}
            </figcaption>
          </figure>
        );
      }
    case "table":
      {
        const label = readerText(content.label) || "表格";
        const caption = readerText(content.caption);
        return (
          <figure>
            <figcaption>
              <strong>{label}</strong>
              {caption ? <span>{caption}</span> : null}
            </figcaption>
            <table>
              <tbody>
                {content.rows.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {row.cells.map((cell, cellIndex) => {
                      const Cell = row.header ? "th" : "td";
                      return (
                        <Cell
                          key={cellIndex}
                          style={{ textAlign: cell.alignment ?? "left" }}
                        >
                          {readerText(cell.text)}
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
    case "equation":
      {
        const equation = mathText(content.latex);
        const label = readerText(content.label) || "公式";
        return (
          <div className="review-equation" role="math" aria-label={equation}>
            <span>{equation}</span>
            <strong>{label}</strong>
          </div>
        );
      }
    case "listing":
      return (
        <figure>
          <figcaption>{readerText(content.caption)}</figcaption>
          <pre data-language={readerText(content.language ?? "")}>
            {content.code}
          </pre>
        </figure>
      );
    case "algorithm":
      return (
        <figure>
          <figcaption>{readerText(content.caption)}</figcaption>
          <pre>{readerText(content.body)}</pre>
        </figure>
      );
    case "footnote":
      return (
        <p className="review-footnote">
          <sup>{content.footnoteId}</sup>
          {textBody(content.text, content.runs)}
        </p>
      );
    case "bibliography":
      return (
        <ol className="review-bibliography">
          {content.entries.map((entry) => (
            <li key={entry.ordinal} value={entry.ordinal}>
              {bibliographyText(entry.text, entry.key, entry.ordinal)}
            </li>
          ))}
        </ol>
      );
    case "unsupported":
      return (
        <div className="review-unsupported" role="alert">
          <strong>此内容无法在 Review 中显示</strong>
          <span>返回结构视图查看对应诊断。</span>
        </div>
      );
  }
}

function ReviewBlockView({
  block,
  active,
  onActivated,
}: {
  block: SerializedPreviewBlock;
  active: boolean;
  onActivated(selection: ContentSelection): void;
}) {
  const activate = () =>
    onActivated({ selectionId: block.selectionId, line: block.line });
  return (
    <section
      className="review-block"
      data-review-state={block.state}
      role="button"
      tabIndex={0}
      aria-pressed={active}
      aria-label={contentLabel(block.content)}
      onClick={activate}
      onKeyDown={(event) => activateOnKeyboard(event, activate)}
    >
      <ReviewContent content={block.content} />
    </section>
  );
}

export function ReviewPanel({ state, onActivated }: ReviewPanelProps) {
  const review = state.preview;
  const blockedMessage = readerText(
    review.message ?? "存在验证错误，无法生成 Review。",
    true,
  );
  return (
    <section
      className="panel review-panel"
      role="region"
      aria-label="论文内容审阅"
      data-mobile-active={state.mobilePanel === "preview"}
    >
      <PanelHeader icon={<BookOpen />} kicker="REVIEW" title="内容审阅" />
      <div className="review-content">
        {review.status === "empty" ? (
          <div className="review-message">
            <h1>等待载入论文</h1>
            <p>打开文稿后，这里会显示不含技术标记的阅读内容。</p>
          </div>
        ) : review.status === "blocked" ? (
          <div className="review-message review-message-blocked" role="alert">
            <h1>内容审阅暂不可用</h1>
            <p>{blockedMessage || "存在验证错误，无法生成 Review。"}</p>
          </div>
        ) : (
          <article className="review-document" data-status={review.status}>
            {review.blocks.map((block) => (
              <ReviewBlockView
                key={block.selectionId}
                block={block}
                active={state.activeSelectionId === block.selectionId}
                onActivated={onActivated}
              />
            ))}
          </article>
        )}
      </div>
      <div className="panel-footer">
        <span>读者视图</span>
        <code>技术标记已隐藏</code>
      </div>
    </section>
  );
}

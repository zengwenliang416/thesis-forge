import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { BuildReport } from "../transport/buildEvents";
import { BUILD_REPORT_SCHEMA_VERSION } from "../transport/constants";
import { BuildOutputPanel } from "./BuildOutputPanel";

const report: BuildReport = {
  schemaVersion: BUILD_REPORT_SCHEMA_VERSION,
  buildId: "build-42",
  intent: "publish",
  outcome: "failed",
  startedAt: "2026-08-23T10:00:00Z",
  completedAt: "2026-08-23T10:00:03Z",
  stages: [
    { name: "parse", status: "succeeded" },
    { name: "validate", status: "failed" },
    { name: "compile", status: "skipped" },
  ],
  failedStage: "validate",
  primaryDiagnosticId: "diagnostic-1",
  diagnostics: [
    {
      id: "diagnostic-1",
      severity: "error",
      category: "semantic",
      code: "TF-SOURCE-001",
      stage: "validate",
      message: "引用目标不存在",
      source: {
        file: "document.md",
        startLine: 12,
        startColumn: 3,
        endLine: 12,
        endColumn: 16,
      },
      target: "fig:model",
      suggestion: "补充对应的图或修正引用目标。",
      relatedLocations: [],
      details: {},
    },
    {
      id: "diagnostic-2",
      severity: "warning",
      category: "source",
      code: "TF-SOURCE-002",
      stage: "parse",
      message: "标题层级存在跳跃",
      source: null,
      target: null,
      suggestion: null,
      relatedLocations: [],
      details: {},
    },
  ],
  logs: [
    {
      sequence: 1,
      stage: "parse",
      level: "info",
      message: "读取 Markdown",
    },
    {
      sequence: 2,
      stage: "validate",
      level: "error",
      message: "验证失败",
    },
  ],
  output: {
    docxPath: null,
    pdfPath: "build/document.preview.pdf",
    previewStale: true,
    successfulBuildId: "build-41",
  },
};

describe("BuildOutputPanel", () => {
  it("renders typed stage state and an expanded primary diagnostic", () => {
    const onCopy = vi.fn();
    render(<BuildOutputPanel report={report} onCopy={onCopy} />);

    expect(screen.getByRole("region", { name: "构建输出" })).toBeVisible();
    expect(screen.getByText("构建失败")).toBeVisible();
    expect(screen.getByText("build-42")).toBeVisible();
    expect(screen.getByLabelText("验证：失败")).toHaveAttribute(
      "data-stage-status",
      "failed",
    );
    expect(screen.getByText("TF-SOURCE-001")).toBeVisible();
    expect(screen.getByText("引用目标不存在")).toBeVisible();
    expect(screen.getByText("document.md:12:3")).toBeVisible();
    expect(screen.getByText("补充对应的图或修正引用目标。")).toBeVisible();
    expect(screen.getByRole("button", { name: "复制诊断" })).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("上一次成功预览");
  });

  it("switches between diagnostic views and keeps the primary diagnostic in its matching severity", async () => {
    const user = userEvent.setup();
    render(<BuildOutputPanel report={report} />);

    await user.click(screen.getByRole("tab", { name: "警告 1" }));
    expect(screen.getByText("标题层级存在跳跃")).toBeVisible();
    expect(screen.queryByText("引用目标不存在")).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "错误 1" }));
    expect(screen.getByText("引用目标不存在")).toBeVisible();
    expect(screen.queryByText("标题层级存在跳跃")).not.toBeInTheDocument();
  });

  it("selects raw logs and copies a selected log or all logs", async () => {
    const user = userEvent.setup();
    const onCopy = vi.fn();
    render(<BuildOutputPanel report={report} onCopy={onCopy} />);

    await user.click(screen.getByRole("tab", { name: "原始日志" }));
    const log = screen.getByRole("button", { name: "选择第 1 条日志" });
    await user.click(log);
    expect(log).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(/读取 Markdown/, { selector: "pre" })).toBeVisible();

    await user.click(screen.getByRole("button", { name: "复制第 1 条日志" }));
    expect(onCopy).toHaveBeenCalledWith("[1] 解析 · info\n读取 Markdown");
    await user.click(screen.getByRole("button", { name: "复制全部日志" }));
    expect(onCopy).toHaveBeenLastCalledWith(
      "[1] 解析 · info\n读取 Markdown\n\n[2] 验证 · error\n验证失败",
    );
  });
});

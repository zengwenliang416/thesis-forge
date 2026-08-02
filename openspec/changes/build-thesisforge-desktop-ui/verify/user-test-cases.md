# User-Aligned Test Cases: build-thesisforge-desktop-ui

## User Test Case Scope

- Cases are derived from `requirements.md`, `acceptance.md`, `acceptance.json`, `prototype/handoff.md`, `tasks.md`, and `development/handoff-to-verify.md`.
- The set preserves one independently executable case for every acceptance assertion `A1` through `A12`.
- GitHub runner billing is excluded from the product acceptance authority; local Web/macOS/Windows execution remains required.

## Aligned Test Cases

### `utc-a1-shared-cross-platform-workbench` — Web、macOS 与 Windows 打开同一套中文浅色工作台

- Actor: 通过浏览器或桌面安装包使用 ThesisForge 的论文作者
- User goal: 在三个目标平台获得一致的论文编辑与构建工作台
- Preconditions: Web production build 可访问，macOS 与 Windows 原生包已构建并安装；桌面验收环境移除 API 凭据并阻断外部网络
- Steps: 分别打开 Web build、macOS ThesisForge.app 和 Windows MSI 安装应用；检查产品栏、大纲、编辑器、预览、诊断、模板、构建和输出区域
- Expected results: 三个运行时显示同一套 React + TypeScript + Vite 工作台；界面固定为 zh-CN 浅色主题，并清楚标识 Web 或本地桌面能力差异
- Boundary / error / permission states: 桌面端在断网且无 API key 时仍可启动和构建；Web 端不声称具有本地原生路径权限
- Acceptance refs: acceptance.json#A1
### `utc-a2-open-saved-snapshot` — 打开 Markdown 后从同一保存快照填充工作台

- Actor: 需要检查论文结构的论文作者
- User goal: 打开一份论文并同时查看大纲、源文、预览和诊断
- Preconditions: 存在一份 UTF-8 Markdown 论文和可解析模板
- Steps: 通过 Web workspace/upload 或桌面原生文件选择打开论文；等待 inspect/preview 完成并检查四个工作区区域
- Expected results: 大纲、编辑器、预览和诊断来自同一保存快照；加载、空白、错误和恢复状态不会丢失已打开内容
- Boundary / error / permission states: 文件缺失、编码错误、浏览器能力限制和读取权限失败
- Acceptance refs: acceptance.json#A2
### `utc-a3-explicit-atomic-save` — 脏编辑必须显式保存且失败不损坏原文

- Actor: 编辑本地或 Web workspace 文稿的论文作者
- User goal: 控制保存时机并避免失败写入破坏已有内容
- Preconditions: 已打开一份可编辑 Markdown 文稿
- Steps: 修改编辑器内容并观察 dirty 状态；确认 Validate/Build 被禁用后执行 Save 或 Save As；注入只读路径或 replace 失败并检查旧内容
- Expected results: 没有 autosave，只有成功保存才清除 dirty 状态；失败保存保留先前字节，inspect/validate/build 不修改源文件
- Boundary / error / permission states: 只读路径、替换失败、未变化保存、Web 下载语义
- Acceptance refs: acceptance.json#A3
### `utc-a4-template-diagnostics` — 模板选择与结构化诊断复用确定性核心契约

- Actor: 需要匹配学校格式并修复问题的论文作者
- User goal: 选择学校模板并定位全部验证问题
- Preconditions: 已打开保存状态的 Markdown 文稿
- Steps: 选择有效、缺失、损坏和不兼容模板；筛选诊断并激活带行号或 target 的问题
- Expected results: 诊断包含 severity、code、message、line 和 target；fatal 问题阻止 Build，warning-only 仍允许构建
- Boundary / error / permission states: 未知本地化 code、无行号问题、模板解析失败
- Acceptance refs: acceptance.json#A4
### `utc-a5-ordered-build-progress` — 构建显示五阶段进度并返回最终 DOCX

- Actor: 需要从论文源生成 DOCX 的论文作者
- User goal: 看到确定性的构建进度和最终输出身份
- Preconditions: 文稿已保存且没有 fatal 诊断
- Steps: 启动构建并观察 parse、validate、compile、render、finalize；打开或下载最终输出
- Expected results: 五阶段顺序固定且重复点击被抑制；成功状态显示 DOCX 路径或 Web download identity
- Boundary / error / permission states: 慢构建、回调失败、旧 generation 的迟到完成
- Acceptance refs: acceptance.json#A5
### `utc-a6-failure-preserves-output` — 失败、取消和过期结果保留已有有效输出

- Actor: 在异常环境下构建论文的论文作者
- User goal: 发生错误时不丢失已有 DOCX 并获得可操作恢复提示
- Preconditions: 目标位置已有一份有效 DOCX
- Steps: 分别触发 validation、permission、render、finalize 和 cancellation 失败；重试并制造旧 token 的迟到完成
- Expected results: 旧输出字节保持不变，临时文件被清理；取消不报告成功，旧结果不覆盖新状态，恢复和重试可用
- Boundary / error / permission states: 每个阶段边界取消、替换失败、renderer 失败
- Acceptance refs: acceptance.json#A6
### `utc-a7-architecture-boundaries` — React、Tauri、HTTP 与确定性核心保持单向依赖

- Actor: 维护 ThesisForge 的开发者
- User goal: 扩展 UI 而不复制或污染 Parser 到 Renderer 核心
- Preconditions: 当前源码和依赖图可静态检查
- Steps: 检查 React 组件到 WorkbenchTransport 再到 Python application 的依赖方向；扫描 Core/Parser/Validator/Compiler/Renderer 的禁止导入
- Expected results: 组件不直接调用 HTTP、Tauri 或 Python，核心不导入前端工具链；DTO 不泄露 pathlib、异常对象、python-docx、lxml 或 renderer 私有对象
- Boundary / error / permission states: 直接 transport 旁路、重复编译逻辑、原始异常泄露
- Acceptance refs: acceptance.json#A7
### `utc-a8-independent-core-distribution` — Python CLI、wheel 和 sdist 独立于前端桌面工具链

- Actor: 只需要命令行编译器的用户和发布维护者
- User goal: 在没有 Node、Rust、Tauri 或 HTTP server 时安装并运行核心
- Preconditions: 当前源码可构建 wheel 和 sdist
- Steps: 构建 wheel/sdist 并在隔离 prefix 安装；在 checkout 外运行 inspect、validate 和 build
- Expected results: 安装来源和依赖闭包均来自隔离 prefix；打包模板可用且离线生成有效 DOCX
- Boundary / error / permission states: checkout 泄漏、缺模板、缺依赖、网络连接
- Acceptance refs: acceptance.json#A8
### `utc-a9-archive-safe-prototype` — 归档后的批准原型仍可被唯一定位和验证

- Actor: 维护 OpenSpec 生命周期和视觉合同的开发者
- User goal: 归档核心 change 后继续稳定复用批准原型证据
- Preconditions: 存在唯一的归档 V1 原型目录
- Steps: 运行原型 locator、logic harness 和浏览器证据测试
- Expected results: locator 只选择归档目录且不修改归档证据；缺失或歧义匹配返回明确失败
- Boundary / error / permission states: 无归档、多个匹配、误选 active change
- Acceptance refs: acceptance.json#A9
### `utc-a10-headless-state-coverage` — 全部工作台状态可在无可见桌面会话下测试

- Actor: 维护跨运行时状态语义的开发者
- User goal: 在 CI 或本地无窗口环境中稳定回归状态机
- Preconditions: 可运行 Python 与 Vitest 单元测试
- Steps: 运行 controller/view model、TypeScript reducer 和 transport 测试
- Expected results: 覆盖 populated、loading、empty、error、disabled、permission、dirty、canceled 和 success；重复操作、stale result 和 recovery 均有行为断言
- Boundary / error / permission states: 迟到 callback、重复点击、恢复后 token 变化
- Acceptance refs: acceptance.json#A10
### `utc-a11-accessible-responsive-workbench` — 键盘、焦点、标签、对比度和响应式布局满足合同

- Actor: 使用键盘或窄窗口工作的论文作者
- User goal: 在桌面、最小桌面和移动宽度下完成主要操作
- Preconditions: 浏览器矩阵与原生截图可用
- Steps: 仅用键盘执行打开、编辑、保存和构建关键路径；检查 focus outline、ARIA label、contrast、resize、mobile panel 和 reduced motion
- Expected results: 焦点顺序可预测且可见，文本和状态不只依赖颜色；1024px、移动宽度和 Windows DPI 缩放下无水平溢出或关键路径丢失
- Boundary / error / permission states: 隐藏次要 toolbar、1028px WebView2 viewport、reduced-motion
- Acceptance refs: acceptance.json#A11
### `utc-a12-offline-runtime-boundaries` — 桌面离线确定性运行且 Web 只使用配置的 HTTP 适配器

- Actor: 重视本地数据边界的论文作者和维护者
- User goal: 确认桌面不会依赖外网、账号、AI 或隐藏遥测
- Preconditions: 桌面网络可断开，Web 可启动真实 Python HTTP adapter
- Steps: 清除代理和 API key/token，断开桌面外部网络并执行完整流程；通过真实 Web production build 调用同源 Python HTTP adapter
- Expected results: macOS/Windows sidecar 阻断 connect/connect_ex 且完整构建成功；Web 请求只进入显式配置的 ThesisForge endpoint，无数据库、账号或遥测
- Boundary / error / permission states: 外部 socket 尝试、凭据环境变量、Web 原生路径误用
- Acceptance refs: acceptance.json#A12


## User Signoff

Status: `approved`

On 2026-08-02, the user directed: “不用管git的流水线 你只要保证整个开发测试完整就好了。” The approved cases therefore require complete local development and testing, real Web/macOS/Windows runtime evidence, and no dependency on GitHub billing availability.

## Domain Mapping

Every approved case is mapped to facticity, static, unit, redteam, E2E, and sensory checks in `verify/domain-case-matrix.json`.

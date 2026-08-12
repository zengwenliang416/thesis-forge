# ThesisForge 模板规范 v0.3（P0）

模板只描述渲染规则，不保存论文正文、图片、BibTeX 或其他论文内容。模板使用
YAML 编写，加载后必须通过 `ThesisTemplate` 的 Pydantic 模型校验。所有模板模型
都禁止未知字段；字段名、单位、枚举值和互斥组合错误都会以字段路径报告。

模板配置的边界是：

```text
YAML -> ThesisTemplate -> Compiler / RenderPlan -> DOCX Renderer
```

Parser 和领域模型不读取 Word 实现细节。学校字体、尺寸、行距、边框和页码文本
必须来自模板；Renderer 不应为某一所学校硬编码这些值。

## 1. 模板选择与内置打包

模板有两个选择入口，优先级从高到低如下：

1. CLI 显式参数 `--template <path>`；
2. Markdown Front Matter 中的 `render.template_id`。

显式路径必须存在，扩展名必须是 `.yaml` 或 `.yml`。相对显式路径按进程当前
工作目录解析；解析后使用绝对路径加载。显式路径存在时，不再根据
`render.template_id` 查找其他模板。

按 ID 选择时，Resolver 使用以下顺序：

1. 从论文源文件所在目录开始，向上检查祖先目录中的 `templates/`；
2. 使用最近一个存在且包含 YAML 候选文件的 `templates/` 目录；
3. 若没有项目模板树，扫描安装包中的 `thesis_forge/template_data/`；
4. 源码 checkout 中没有安装包数据时，回退到仓库根目录的 `templates/`。

候选文件递归扫描 `*.yaml` 和 `*.yml`，忽略以 `._` 开头的文件，并按稳定路径
顺序检查顶层 `id`。同一搜索根中没有匹配项返回 `missing-template`；一个 ID
匹配多个文件返回 `ambiguous-template`。本地项目模板树一旦被选中，不会与内置
模板目录合并，也不会在同一选择层级内随机择一。

发布 wheel 使用 Hatch `force-include` 把仓库中的模板复制到安装包
`thesis_forge/template_data/`。当前打包配置声明的映射为：

```text
templates/base/bachelor.yaml
  -> thesis_forge/template_data/base/bachelor.yaml

templates/schools/example-university/2026.yaml
  -> thesis_forge/template_data/schools/example-university/2026.yaml

templates/schools/hunan-university-of-technology/master-2026.yaml
  -> thesis_forge/template_data/schools/hunan-university-of-technology/master-2026.yaml
```

映射只定义发布位置；源 YAML 必须同时存在并通过模板校验，才能在实际 wheel
中成为可用内置模板。源码分发包保留仓库的 `templates/` 目录。模板解析只读
本地文件，不访问网络、AI 服务或外部配置服务。

## 2. 顶层结构

```yaml
id: <非空字符串>
name: <非空字符串>
year: <整数或字符串>
page: <PageSpec>
cover: <CoverSpec，可省略>
list: <ListSpec，可省略>
body: <BodySpec>
heading: <HeadingSpec>
semantic_styles: <SemanticStylesSpec，可省略>
toc: <TocSpec，可省略>
bibliography: <BibliographySpec，可省略>
figure: <FigureSpec，可省略>
table: <TableSpec，可省略>
equation: <EquationSpec，可省略>
sections: <SectionsSpec，可省略>
citation: <CitationSpec，可省略>
```

顶层字段的必填和默认行为如下：

| 字段 | 类型 | 必填/默认 | 说明 |
| --- | --- | --- | --- |
| `id` | `str` | 必填，长度至少 1 | 模板选择使用的稳定 ID |
| `name` | `str` | 必填，长度至少 1 | 人类可读名称 |
| `year` | `int \| str` | 必填 | 可使用 `2026` 或 `base` |
| `page` | `PageSpec` | 必填 | 页面几何和文档网格 |
| `cover` | `CoverSpec` | 默认通用字段顺序 | 封面字段、静态文本、顺序和段落样式 |
| `list` | `ListSpec` | 默认兼容旧 Renderer 的 9 层策略 | 有序编号、项目符号、缩进和段落样式 |
| `body` | `BodySpec` | 必填 | 正文段落样式 |
| `heading` | `HeadingSpec` | 必填 | `level1` 必填，`level2/3` 可选 |
| `semantic_styles` | `SemanticStylesSpec` | 默认空对象 | 摘要、关键词和特殊角色样式 |
| `toc` | `TocSpec \| None` | 默认 `None` | TOC 标题和 1-3 级样式 |
| `bibliography` | `BibliographySpec \| None` | 默认 `None` | 参考文献标题和条目样式 |
| `figure` | `FigureSpec \| None` | 默认 `None` | 图编号和题注规则 |
| `table` | `TableSpec \| None` | 默认 `None` | 表格边框、编号和题注规则 |
| `equation` | `EquationSpec \| None` | 默认 `None` | 公式编号和对齐 |
| `sections` | `SectionsSpec` | 默认空对象 | `cover/front_matter/main` section 策略 |
| `citation` | `CitationSpec \| None` | 默认 `None` | 引文格式名和文内展示方式 |

省略 `figure`、`table`、`equation` 或 `citation` 并不为对应论文对象生成默认
学校样式。论文实际使用相应对象时，Validator 会报告
`missing-template-style`。

## 3. 单位、尺寸与通用校验

### 3.1 长度写法

所有 `LengthSpec` 都必须是带单位的字符串，支持：

```text
mm   cm   pt   em
```

合法示例：

```yaml
margin: 25mm
font_size: 12pt
first_line_indent: 2em
```

非法示例：

```yaml
margin: 25
margin: "12"
margin: 12px
margin: large
```

模型只接受非负十进制数字加上述单位；不接受负数、百分号或其他单位。数字
可写成 `10.50pt`，模型规范化后其字符串表示为 `10.5pt`。

### 3.2 相对单位与物理尺寸

`em` 是相对于目标段落样式有效字号的相对单位。它适合首行缩进、悬挂缩进、
左右缩进、段前段后、部分样式字号和 TOC 制表位。Renderer 在应用样式时使用
目标角色的字号；如果角色字号使用 `em`，则使用正文绝对字号作为基准。

以下字段是页面或 OOXML 物理尺寸，必须使用绝对单位 `mm`、`cm` 或 `pt`，不能
使用 `em`：

| 字段 | 额外约束 |
| --- | --- |
| `page.margin.top/bottom/left/right` | 必填；绝对单位 |
| `page.header_distance`、`page.footer_distance` | 可选；绝对单位 |
| `page.document_grid.line_pitch` | 非 `default` 网格时必填；绝对单位且大于 0 |
| `body.size` | 必填；绝对单位 |
| `list.ordered.levels[].left_indent/hanging_indent` | 必填或使用层级默认；绝对单位，悬挂不大于左缩进 |
| `list.unordered.levels[].left_indent/hanging_indent` | 必填或使用层级默认；绝对单位，悬挂不大于左缩进 |
| `sections.*.header/footer.*.bottom_border.width` | 可选；绝对单位且大于 0 |
| `sections.*.header/footer.*.bottom_border.space` | 可选；绝对单位 |

`toc.level*.page_number_tab` 需要大于 0，但模型允许它使用 `em`，此时按该
TOC 样式的有效字号解析。`figure.default_width`、题注字号以及通用段落样式
中的其他 `LengthSpec` 不受上述绝对单位限制，但仍必须带单位。

### 3.3 未知字段和互斥字段

所有模板模型均使用 `extra="forbid"`。例如 `body.magic_spacing`、未定义的
`toc.level4` 或任意 Word `style_id` 都会被拒绝。

`first_line_indent` 和 `hanging_indent` 不能同时为正值。零值可以显式写出，
用于表达“没有该缩进”：

```yaml
first_line_indent: 2em
hanging_indent: 0em
```

## 4. ParagraphStyleSpec：公共段落策略

`ParagraphStyleSpec` 是正文、标题、摘要、关键词、TOC、参考文献和页眉页脚
段落复用的公共模型。除特别说明外，下面字段的默认值都是 `null`，表示该
属性不在这个样式对象中覆盖，由目标 Word 基础样式或角色 fallback 提供。

| 字段 | 类型 | 默认/约束 | 作用 |
| --- | --- | --- | --- |
| `font` | `FontSpec \| None` | `null` | 中西文字体槽位 |
| `size` | `LengthSpec \| None` | `null` | 字号；可使用相对 `em`，但 `body.size` 除外 |
| `color` | `auto \| RRGGBB \| None` | `null`；6 位十六进制不带 `#` | 文字颜色；显式值会清除 Word 主题色覆盖 |
| `bold` | `bool \| None` | `null` | 是否加粗 |
| `italic` | `bool \| None` | `null` | 是否斜体 |
| `alignment` | `left \| center \| right \| justify` | `null` | 段落对齐 |
| `left_indent` | `LengthSpec \| None` | `null` | 左缩进 |
| `right_indent` | `LengthSpec \| None` | `null` | 右缩进 |
| `first_line_indent` | `LengthSpec \| None` | `null` | 首行缩进 |
| `hanging_indent` | `LengthSpec \| None` | `null` | 悬挂缩进 |
| `space_before` | `LengthSpec \| None` | `null` | 段前间距 |
| `space_after` | `LengthSpec \| None` | `null` | 段后间距 |
| `line_spacing` | `LineSpacingSpec \| None` | `null` | 行距类型和数值 |
| `widow_control` | `bool \| None` | `null` | 孤行控制 |
| `keep_together` | `bool \| None` | `null` | 段落保持同页 |
| `keep_with_next` | `bool \| None` | `null` | 与下段保持同页 |
| `page_break_before` | `bool \| None` | `null` | 段前分页 |
| `outline_level` | `int \| None` | `null`，范围 `0..9` | Word 大纲级别 |
| `snap_to_grid` | `bool \| None` | `null` | 是否对齐文档网格 |

`FontSpec` 的字段及默认值为：

| 字段 | 默认值 |
| --- | --- |
| `font.east_asia` | `宋体` |
| `font.latin` | `Times New Roman` |

因此，写出 `font: {east_asia: 黑体}` 时，未写出的 `latin` 仍使用
`Times New Roman`；不写 `font` 时，公共样式对象保持 `null`，由其基础样式或
角色 fallback 决定。

### 4.1 行距

`line_spacing.type` 的枚举和 `value` 规则如下：

| `type` | 默认 | `value` |
| --- | --- | --- |
| `fixed` | `fixed` | 必须是带单位的 `LengthSpec`，例如 `20pt` |
| `multiple` | 无 | 必须是大于 0 的 YAML 浮点数，例如 `1.15` |
| `single` | 无 | 必须省略 `value` |

`multiple` 使用 `1.0`、`1.15` 等浮点写法；整数 `1` 不作为该字段的合法
浮点值。`fixed` 的 `em` 会按目标样式字号解析，页面物理几何中的固定尺寸
仍按第 3 节的绝对单位规则校验。

### 4.2 BodySpec 与 HeadingLevelSpec 的默认和继承

`BodySpec` 继承 `ParagraphStyleSpec`，但保留正文入口的必填字段：

```yaml
body:
  font: {east_asia: 宋体, latin: Times New Roman}
  size: 12pt
  alignment: justify
  first_line_indent: 2em
  line_spacing:
    type: fixed
    value: 20pt
```

`BodySpec` 的具体默认/必填规则是：

- `font` 默认创建 `FontSpec`，即宋体和 Times New Roman；
- `size` 必填且必须是绝对单位；
- `alignment` 默认 `justify`；
- `first_line_indent` 必填；
- `line_spacing` 必填；
- 其他公共字段仍默认 `null`。

`HeadingLevelSpec` 的 `size` 必填，其他专属默认值为：

- `bold: false`；
- `italic: false`；
- `alignment: left`；
- `page_break_before: false`。

`HeadingSpec.level1` 必填，`level2` 和 `level3` 可选；模型不定义
`level4` 或更高层级的模板字段。标题样式没有单独配置字体时，DOCX 样式
翻译器使用正文字体作为标题字体 fallback；标题的 `em` 字号使用正文绝对
字号作为基准。

公共段落字段不会在 YAML 模型中自动复制成另一份正文配置。实际角色的 fallback
如下：

| 角色 | 未提供专用样式时的 fallback |
| --- | --- |
| `abstract.zh.title`、`abstract.en.title` | 对应标题级别样式，缺失时使用 `heading.level1` |
| `abstract.zh.body`、`abstract.en.body` | `body` |
| `keywords.zh`、`keywords.en` | `body` |
| `toc.title` | 对应标题级别样式，缺失时使用 `heading.level1` |
| `bibliography.title` | 对应标题级别样式，缺失时使用 `heading.level1` |
| `bibliography.entry` | `body` |
| `special.acknowledgements`、`special.achievements` | 对应标题级别样式，缺失时使用 `heading.level1` |

## 5. 页面、正文与标题

### 5.1 PageSpec

```yaml
page:
  size: A4
  orientation: portrait
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
  header_distance: 15mm
  footer_distance: 17.5mm
  document_grid:
    type: lines
    line_pitch: 20pt
    char_space: 100
```

`page.size` 支持 `A3`、`A4`、`A5`、`Letter`、`Legal`，默认 `A4`。
`page.orientation` 支持 `portrait`、`landscape`，默认 `portrait`。
`margin` 的四个字段必填。`header_distance`、`footer_distance` 和
`document_grid` 可省略。

`document_grid.type` 支持：

```text
default
lines
lines_and_chars
snap_to_chars
```

默认类型是 `lines`。当类型不是 `default` 时，必须提供绝对单位且大于 0 的
`line_pitch`。`char_space` 是可选整数；模型不为它添加额外的范围约束。

### 5.2 CoverSpec

封面内容来自 Markdown Front Matter，字段顺序、静态文字和排版来自模板：

```yaml
cover:
  items:
    - field: university.name
      style:
        font:
          east_asia: 黑体
          latin: Times New Roman
        size: 24pt
        bold: true
        alignment: center
        space_after: 18pt
    - text: 硕士学位论文
      style:
        alignment: center
        space_after: 36pt
    - field: thesis.title
      prefix: "题目："
      skip_if_empty: true
      style:
        alignment: center
```

每个 `CoverItemSpec` 必须且只能配置一个内容来源：

- `field`：从 `CoverInstruction` 读取受支持的 Front Matter 语义字段；
- `text`：由模板提供的非空静态文字。

公共字段为：

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `prefix` | `""` | 内容前缀 |
| `suffix` | `""` | 内容后缀 |
| `skip_if_empty` | `true` | metadata 为空时是否跳过整个段落 |
| `style` | 居中 `ParagraphStyleSpec` | 复用全部公共段落属性 |

支持的 `field` 为 `university.name`、`university.college`、`thesis.title`、
`thesis.title_en`、`thesis.major`、`thesis.degree`、`author.name`、
`author.student_id`、`advisor.name`、`advisor.title` 和 `dates.completed`。
同一 `CoverSpec` 中 metadata field 不允许重复，静态 `text` 可以重复。

省略 `cover` 时，模型按上述 metadata field 的通用顺序生成居中段落。模板应通过
`space_before` 和 `space_after` 控制垂直节奏，不使用 Renderer 固定空白段落。

### 5.3 ListSpec

Markdown 负责列表类型、文本、嵌套层级和有序列表起始值；模板只负责列表呈现：

```yaml
list:
  ordered:
    levels:
      - format: lower_roman
        prefix: "("
        suffix: ")"
        alignment: right
        left_indent: 36pt
        hanging_indent: 18pt
        style:
          font:
            east_asia: 宋体
            latin: Times New Roman
          size: 12pt
          color: "000000"
          space_before: 0pt
          space_after: 0pt
          line_spacing:
            type: fixed
            value: 20pt
  unordered:
    levels:
      - marker: "•"
        alignment: left
        left_indent: 36pt
        hanging_indent: 18pt
        style:
          size: 12pt
          line_spacing:
            type: fixed
            value: 20pt
```

`ordered.levels` 和 `unordered.levels` 都必须包含 1 至 9 个层级。Markdown 嵌套
深度超过模板声明层数时，Renderer 确定性复用最后一个层级策略，并把 Word
`ilvl` 限制在 `0..8`。模板不需要为了支持深层 Markdown 手工复制 9 份相同规则。

有序层级字段为：

| 字段 | 默认/约束 | 说明 |
| --- | --- | --- |
| `format` | `decimal` | 语义编号格式 |
| `prefix` | `""` | 编号占位符之前的文字 |
| `suffix` | `"."` | 编号占位符之后的文字 |
| `alignment` | `left` | marker 在编号区域内的对齐 |
| `left_indent` | `36pt` | 编号层级左缩进，必须是绝对单位 |
| `hanging_indent` | `18pt` | 悬挂缩进，必须是绝对单位且不能大于左缩进 |
| `style` | 空 `ParagraphStyleSpec` | 列表文本和段落属性 |

`format` 只接受以下 Renderer-neutral 枚举：

```text
decimal
lower_letter
upper_letter
lower_roman
upper_roman
```

模板不得使用 Word 的 `lowerLetter`、`upperRoman`、`w:numFmt` 或 `w:lvlText`。
这些实现值由 DOCX Renderer 统一翻译。

无序层级使用同一组 `alignment`、缩进和 `style` 字段，并以非空 `marker`
替代 `format/prefix/suffix`。marker 是普通 Unicode 文本，例如 `•`、`◦`、
`▪` 或 `◆`；模板不能注入图片项目符号或 raw OOXML。

省略整个 `list` 时，模型创建与旧 Renderer 等价的通用 9 层默认：

- 有序列表全部使用 `decimal`、空前缀和 `"."` 后缀；
- 无序列表按 `•`、`◦`、`▪` 循环；
- marker 全部左对齐；
- 左缩进依次为 `36pt`、`72pt` 至 `324pt`；
- 悬挂缩进全部为 `18pt`；
- 每层 `style` 为空，由 Word `Normal` 样式和 `body` fallback 提供正文格式。

Markdown 非 1 起始编号仍属于文档语义，不由模板覆盖。首层使用 Markdown
`start` 或首项 ordinal，深层 numbering level 从 1 开始。

### 5.4 正文与标题

正文使用 `body`，标题使用 `heading.level1`、`heading.level2` 和
`heading.level3`。标题级别缺失而论文实际使用时，Validator 报告
`missing-template-style`，目标为对应的 `heading.levelN`。

Renderer 将这些规则写入真实 Word paragraph style 和段落属性，包括字体槽位、
文字颜色、字号、对齐、缩进、段距、行距、孤行控制、同页控制、分页前、
大纲级别和文档网格对齐；模板本身不直接写 Word `style_id` 或 OOXML 标签。

## 6. semantic_styles 与特殊角色

`semantic_styles` 只能使用模型定义的角色：

```yaml
semantic_styles:
  abstract_zh:
    title: <ParagraphStyleSpec>
    body: <ParagraphStyleSpec>
    keywords: <ParagraphStyleSpec>
  abstract_en:
    title: <ParagraphStyleSpec>
    body: <ParagraphStyleSpec>
    keywords: <ParagraphStyleSpec>
  acknowledgements: <ParagraphStyleSpec>
  achievements: <ParagraphStyleSpec>
```

每个子项都可省略；省略后使用第 4.2 节的 fallback。模板不能新增任意角色名，
也不能要求用户配置 Word 样式名。

Compiler 使用稳定 heading ID 识别角色：

| heading ID | heading 角色 | 后续段落角色 |
| --- | --- | --- |
| `chap:abstract-zh` | `abstract.zh.title` | `abstract.zh.body` |
| `chap:abstract-en` | `abstract.en.title` | `abstract.en.body` |
| `chap:toc`、`chap:contents` | `toc.title` | 普通正文 |
| `chap:bibliography`、`chap:references`、`references` | `bibliography.title` | `bibliography.entry` |
| `chap:acknowledgements`、`acknowledgements` | `special.acknowledgements` | 普通正文 |
| `chap:achievements`、`achievements` | `special.achievements` | 普通正文 |

关键词只在匹配的摘要上下文中识别，且标签必须位于段落开头：

```text
关键词：模板；编译器；DOCX
Keywords: template; compiler; DOCX
```

中文标签支持 `关键词:` 和 `关键词：`，可带 Markdown 粗体标记；英文
`Keywords:` 大小写不敏感。摘要正文的原始文本和 inline runs 保持不变，只有
语义角色改变。

## 7. TOC

`toc` 提供真实 Word TOC 字段的标题和 1-3 级样式：

```yaml
toc:
  title:
    size: 16pt
    bold: true
    alignment: center
  level1:
    size: 12pt
    left_indent: 0em
    page_number_tab: 150mm
    leader: dots
  level2:
    size: 12pt
    left_indent: 1em
    page_number_tab: 150mm
    leader: dots
  level3:
    size: 12pt
    left_indent: 2em
    page_number_tab: 150mm
    leader: dots
```

`TocSpec` 的字段为 `title`、`level1`、`level2`、`level3`，均可省略。
`TocLevelSpec` 复用全部 `ParagraphStyleSpec` 字段，并增加：

| 字段 | 默认/约束 |
| --- | --- |
| `first_line_indent` | 默认 `0pt`，使目录条目默认顶格 |
| `page_number_tab` | 默认 `None`；提供时必须大于 0 |
| `leader` | 默认 `dots` |

`leader` 只支持：

```text
none
dots
dashes
line
heavy
middle_dot
```

Renderer 为 TOC 1、TOC 2、TOC 3 创建或更新真实 Word 样式，并在右侧写入页码
制表位和 leader。`page_number_tab` 省略时使用页面内容宽度；提供 `em` 时
按该级 TOC 样式的有效字号解析。

模板只控制“目录”标题和各级目录条目的样式，不保存目录条目、页码或静态目录
文本。Renderer 会先创建独立的 `toc.title` 标题段落，再在下一段创建真实、
可编辑且标记为 dirty 的 Word `TOC` complex field；文档设置
`w:updateFields=true`，因此没有可用 Office 布局引擎时，Word、WPS 或
LibreOffice 仍可在打开文档后手动更新目录。

默认构建服务会在 DOCX Renderer 完成后尝试使用本机 LibreOffice 计算目录条目
和页码，再执行 DOCX package validation 和原子替换。该步骤是可选增强：
LibreOffice 未安装、无法连接、刷新失败或超时时，构建服务恢复 Renderer 生成
的原始有效 DOCX，保留 dirty TOC field，不把失败或部分写入的文件替换为最终
输出。整个刷新流程只访问本地进程和文件，不访问网络或 AI 服务。

运行时环境变量如下：

| 环境变量 | 默认/作用 |
| --- | --- |
| `THESISFORGE_OFFICE_REFRESH` | 默认 `auto`；设为 `0`、`false`、`no`、`off` 或 `disabled` 可关闭自动刷新 |
| `THESISFORGE_LIBREOFFICE` | 可选；显式指定 `soffice` / `soffice.exe` 路径 |
| `THESISFORGE_LIBREOFFICE_PYTHON` | 可选；显式指定能够 import UNO 的 Python 解释器 |

macOS 默认发现 `/Applications/LibreOffice.app`。macOS、Linux 和 Windows
都使用 `--headless`、隔离 profile、私有 UNO pipe 和 hidden document load，
每次构建最多启动一个 LibreOffice 进程。CLI、Web 服务和 macOS/Windows 桌面端共用同一
`build_service`；是否能预填页码取决于实际执行构建的主机是否安装兼容的
LibreOffice 及 UNO Python。未安装时不会影响 DOCX 的可编辑性和后续手动更新。

## 8. bibliography 与 citation presentation

### 8.1 BibliographySpec

```yaml
bibliography:
  title:
    size: 16pt
    bold: true
    alignment: center
  entry:
    size: 10.5pt
    hanging_indent: 2em
    space_before: 0pt
    space_after: 0pt
    line_spacing:
      type: fixed
      value: 20pt
```

`BibliographySpec` 只有 `title` 和 `entry` 两个 `ParagraphStyleSpec` 字段。
`title` 缺失时 fallback 到标题样式，`entry` 缺失时 fallback 到 `body`。
`entry.hanging_indent: 2em` 表示两字符悬挂缩进。

参考文献文件路径和 BibTeX 数据不由模板配置；它们来自 Markdown Front Matter
的 `render.bibliography` 等文档渲染配置。模板只控制参考文献标题和条目的段落
呈现。参考文献条目的顺序和文本格式化由 bibliography subsystem 保持，模板不
复制或重排条目数据。

### 8.2 CitationSpec

```yaml
citation:
  style: GB-T-7714-2025
  presentation: superscript
```

`citation.style` 是模板中记录的非空 style 标识，当前示例使用
`GB-T-7714-2025`；当前模板模型不为它定义枚举，也不在模型层读取文献文件。
文献数据侧的格式化配置仍来自 Markdown Front Matter 的
`render.citation_style`。`presentation` 只能是：

```text
inline       # 默认
superscript
```

`inline` 保持普通文内 run；`superscript` 只把 citation run 设置为上标。该设置
不改变 bibliography formatter，也不把普通正文、脚注文字或参考文献条目整体
设置为上标。论文含有 citation 而模板省略 `citation` 时，Validator 报告
`missing-template-style`，目标为 `citation`。

## 9. figure、table 与 equation

### 9.1 FigureSpec

```yaml
figure:
  numbering:
    mode: chapter
    separator: "-"
  caption:
    position: bottom
    prefix: 图
    font:
      east_asia: 宋体
      latin: Times New Roman
    size: 10.5pt
    alignment: center
  default_width: 150mm
```

`FigureSpec` 的字段为：

- `numbering`，默认 `mode: chapter`、`separator: "-"`；
- `caption`，必填；
- `default_width`，可选 `LengthSpec`。

`caption.position` 只能是 `top` 或 `bottom`；`prefix` 必填；`font` 和 `size`
可省略；`alignment` 默认 `center`。

### 9.2 TableSpec

```yaml
table:
  style: three_line
  three_line:
    top_width: 1.5pt
    header_width: 0.75pt
    bottom_width: 1.5pt
  numbering: chapter
  caption:
    position: top
    prefix: 表
    alignment: center
```

`style` 支持 `three_line`、`grid`、`plain`，默认 `three_line`。
`numbering` 和 `caption` 的规则与图一致。`three_line` 用
`top_width`、`header_width`、`bottom_width` 分别控制顶线、栏目线和底线，
默认值依次为 `1.5pt`、`0.75pt`、`1.5pt`。三个字段必须是 `0.25pt` 到
`12pt` 范围内的绝对长度；Word 使用 `1/8pt` 整数保存表格线宽，其他绝对单位会
换算为磅并取最接近的 `1/8pt`。
`three_line`、`grid` 和 `plain` 只描述当前模型支持的表格边框策略；模型不包含
列宽、单元格边距、合并单元格、重复表头或跨页控制字段。

### 9.3 EquationSpec

```yaml
equation:
  numbering:
    mode: chapter
    separator: "-"
  alignment: center
```

`alignment` 支持 `left`、`center`、`right`，默认 `center`。
`numbering` 默认 `mode: chapter`、`separator: "-"`。公式的高级布局、公式
制表位和右端编号不属于当前模板模型。

### 9.4 编号短写

`NumberingSpec` 可以使用字符串短写：

```yaml
numbering: chapter
```

等价于：

```yaml
numbering:
  mode: chapter
  separator: "-"
```

`mode` 支持 `chapter`、`continuous`、`none`。图、表、公式的最终编号由
Compiler 统一计算，模板只提供编号策略和题注前缀。

## 10. section、页眉页脚与页面变体

### 10.1 SectionsSpec 与 SectionSpec

```yaml
sections:
  cover: <SectionSpec，可选>
  front_matter: <SectionSpec，可选>
  main: <SectionSpec，可选>
```

`SectionSpec` 的字段和默认值为：

| 字段 | 类型 | 默认 |
| --- | --- | --- |
| `start` | `continuous \| new_page \| odd_page \| even_page` | `new_page` |
| `header` | `HeaderFooterSpec` | 空对象 |
| `footer` | `HeaderFooterSpec` | 空对象 |
| `page_number` | `PageNumberSpec` | 默认页码配置 |

section 只支持 `cover`、`front_matter`、`main` 三个命名角色。它们可分别配置
页眉、页脚和页码格式；未声明的角色不产生该角色的 section policy。

### 10.2 default、first、even 变体

页眉和页脚都使用同一个 `HeaderFooterSpec` 结构：

```yaml
header:
  default: <HeaderFooterVariantSpec>
  first: <HeaderFooterVariantSpec，可选>
  even: <HeaderFooterVariantSpec，可选>
```

`HeaderFooterVariantSpec` 的字段如下：

| 字段 | 类型 | 默认/说明 |
| --- | --- | --- |
| `enabled` | `bool` | 默认 `true`；`false` 表示该变体不输出内容 |
| `text` | `str \| None` | 默认 `None`；文本可与页码同时出现 |
| `style` | `ParagraphStyleSpec \| None` | 默认 `None`；变体段落样式 |
| `bottom_border` | `ParagraphBorderSpec \| None` | 默认 `None`；只配置段落底边 |
| `page_number` | `PageNumberDisplaySpec \| None` | 默认 `None`；该变体的 PAGE/NUMPAGES 展示覆盖 section 默认值 |

`default` 表示普通/奇数页的默认变体，`first` 表示首页变体，`even` 表示
偶数页变体。声明任一 section 的 `first` 后，缺失的另一部分 `first` 会使用
该部分的 `default`；声明任一 section 的 `even` 后，缺失的另一部分 `even`
会使用该部分的 `default`。需要明确空白时，应显式写 `enabled: false`。
声明 `even` 变体会启用文档级奇偶页眉页脚设置。

`ParagraphBorderSpec` 的字段为：

| 字段 | 默认/约束 |
| --- | --- |
| `style` | `none`、`single`、`double`、`dotted`、`dashed`，默认 `single` |
| `width` | 可选，绝对单位且大于 0 |
| `color` | 默认 `auto`；或 6 位十六进制颜色，如 `336699` |
| `space` | 可选绝对单位，可为 `0pt` |

### 10.3 legacy 页眉页脚兼容

旧写法仍被 `HeaderFooterSpec` 接受：

```yaml
header:
  enabled: true
  text: 论文标题
  different_first_page: true
```

legacy 字段及兼容规则：

- `enabled` 默认 `false`；
- `text` 默认 `null`；
- `different_first_page` 默认 `false`；
- 未提供 `default` 时，模型把 legacy `enabled/text` 规范化为 `default` 变体；
- `different_first_page: true` 且未提供 `first` 时，模型生成
  `first.enabled: false`；
- 显式 `default` 不能同时写 legacy `enabled` 或 `text`；
- 显式 `first` 不能同时写 legacy `different_first_page`；
- 推荐新模板只使用 `default/first/even`，不要在同一个对象中混用两套写法。

上述冲突是字段级模型错误，而不是“后者覆盖前者”。legacy 页脚配置在没有
专用变体页码策略时，仍兼容旧的“第 X 页 / 共 Y 页”默认显示。

### 10.4 PageNumberSpec 与显示策略

```yaml
page_number:
  format: decimal
  restart: 1
  display:
    alignment: center
    page_prefix: ""
    page_suffix: ""
    include_total: false
    separator: " / "
    total_prefix: "共 "
    total_suffix: " 页"
```

`PageNumberSpec`：

| 字段 | 默认/约束 |
| --- | --- |
| `format` | `decimal`、`roman-lower`（i/ii/iii）、`roman-upper`（I/II/III）、`none`；默认 `decimal` |
| `restart` | 默认 `None`；提供时必须是大于等于 1 的整数 |
| `display` | `PageNumberDisplaySpec`，默认使用下表的 legacy 文本 |

`PageNumberDisplaySpec`：

| 字段 | 默认 |
| --- | --- |
| `alignment` | `center` |
| `page_prefix` | `第 ` |
| `page_suffix` | ` 页` |
| `include_total` | `true` |
| `separator` | ` / ` |
| `total_prefix` | `共 ` |
| `total_suffix` | ` 页` |

`format` 控制 Word `w:pgNumType` 中 PAGE 的数字格式；`restart` 控制
section 的起始页码。`display` 控制 PAGE/NUMPAGES 字段前后的文本、总页数
开关和对齐。变体的 `page_number` 存在时，优先于 section 级
`page_number.display`；否则启用的默认页脚变体沿用 section 级显示策略。

当 `format: none` 时：

- 不能配置 `restart`；
- 任何 `enabled: true` 的 header/footer 变体都不能配置 `page_number`；
- Renderer 不写 PAGE 或 NUMPAGES 字段。

`enabled: false` 的变体可以保留一个不会被输出的 `page_number` 配置，作为
后续启用该变体时的 dormant policy；这不等同于当前 section 输出页码。

## 11. 完整 HUT P0 YAML 示例

下面示例覆盖 task 007.1 要求的 P0 表面：正文和标题、中文/英文摘要及关键词、
三层 TOC、参考文献、文内上标引文、图表公式、页面几何、文档网格、首页/奇偶
页眉页脚和页码。所有键都来自当前 `model.py`；示例不包含模型之外的学校扩展
字段。

其中正文的宋体、Times New Roman、12pt、2em、20pt、零段距、孤行控制、
15mm/17.5mm 页眉页脚距离、三层点引导符、上标引文、两字符悬挂缩进和中心
PAGE 字段来自 P0 design target；其余值与当前 HUT P0 YAML 示例保持一致。
该示例是完整合同示例，不替代学校原始格式文件的审定值。

```yaml
id: hut-master-2026
name: 湖南工业大学硕士学位论文 P0 模板
year: 2026

page:
  size: A4
  orientation: portrait
  margin:
    top: 25mm
    bottom: 25mm
    left: 30mm
    right: 25mm
  header_distance: 15mm
  footer_distance: 17.5mm
  document_grid:
    type: lines
    line_pitch: 20pt

body:
  font:
    east_asia: 宋体
    latin: Times New Roman
  size: 12pt
  alignment: justify
  first_line_indent: 2em
  space_before: 0pt
  space_after: 0pt
  line_spacing:
    type: fixed
    value: 20pt
  widow_control: true
  snap_to_grid: true

heading:
  level1:
    font:
      east_asia: 黑体
      latin: Times New Roman
    size: 16pt
    color: "000000"
    bold: true
    alignment: left
    left_indent: 0pt
    right_indent: 0pt
    first_line_indent: 0pt
    space_before: 0pt
    space_after: 12pt
    line_spacing:
      type: fixed
      value: 20pt
    keep_with_next: true
    page_break_before: true
    outline_level: 0
    snap_to_grid: true
  level2:
    font:
      east_asia: 黑体
      latin: Times New Roman
    size: 14pt
    color: "000000"
    bold: true
    alignment: left
    left_indent: 0pt
    right_indent: 0pt
    first_line_indent: 0pt
    space_before: 6pt
    space_after: 6pt
    line_spacing:
      type: fixed
      value: 20pt
    keep_with_next: true
    outline_level: 1
    snap_to_grid: true
  level3:
    font:
      east_asia: 黑体
      latin: Times New Roman
    size: 12pt
    color: "000000"
    bold: true
    alignment: left
    left_indent: 0pt
    right_indent: 0pt
    first_line_indent: 0pt
    space_before: 3pt
    space_after: 3pt
    line_spacing:
      type: fixed
      value: 20pt
    keep_with_next: true
    outline_level: 2
    snap_to_grid: true

semantic_styles:
  abstract_zh:
    title:
      font:
        east_asia: 黑体
        latin: Times New Roman
      size: 16pt
      bold: true
      alignment: center
      space_before: 0pt
      space_after: 12pt
      line_spacing:
        type: fixed
        value: 20pt
      keep_with_next: true
      page_break_before: true
      snap_to_grid: true
    body:
      font:
        east_asia: 宋体
        latin: Times New Roman
      size: 12pt
      alignment: justify
      first_line_indent: 2em
      space_before: 0pt
      space_after: 0pt
      line_spacing:
        type: fixed
        value: 20pt
      widow_control: true
      snap_to_grid: true
    keywords:
      font:
        east_asia: 宋体
        latin: Times New Roman
      size: 12pt
      alignment: justify
      first_line_indent: 0pt
      space_before: 0pt
      space_after: 0pt
      line_spacing:
        type: fixed
        value: 20pt
      snap_to_grid: true
  abstract_en:
    title:
      font:
        east_asia: 黑体
        latin: Times New Roman
      size: 16pt
      bold: true
      alignment: center
      space_before: 0pt
      space_after: 12pt
      line_spacing:
        type: fixed
        value: 20pt
      keep_with_next: true
      page_break_before: true
      snap_to_grid: true
    body:
      font:
        east_asia: 宋体
        latin: Times New Roman
      size: 12pt
      alignment: justify
      first_line_indent: 2em
      space_before: 0pt
      space_after: 0pt
      line_spacing:
        type: fixed
        value: 20pt
      widow_control: true
      snap_to_grid: true
    keywords:
      font:
        east_asia: 宋体
        latin: Times New Roman
      size: 12pt
      alignment: justify
      first_line_indent: 0pt
      space_before: 0pt
      space_after: 0pt
      line_spacing:
        type: fixed
        value: 20pt
      snap_to_grid: true
  acknowledgements:
    font:
      east_asia: 黑体
      latin: Times New Roman
    size: 16pt
    bold: true
    alignment: center
    space_before: 0pt
    space_after: 12pt
    line_spacing:
      type: fixed
      value: 20pt
    keep_with_next: true
    page_break_before: true
    snap_to_grid: true
  achievements:
    font:
      east_asia: 黑体
      latin: Times New Roman
    size: 16pt
    bold: true
    alignment: center
    space_before: 0pt
    space_after: 12pt
    line_spacing:
      type: fixed
      value: 20pt
    keep_with_next: true
    page_break_before: true
    snap_to_grid: true

toc:
  title:
    font:
      east_asia: 黑体
      latin: Times New Roman
    size: 16pt
    bold: true
    alignment: center
    space_before: 0pt
    space_after: 12pt
    line_spacing:
      type: fixed
      value: 20pt
    keep_with_next: true
    snap_to_grid: true
  level1:
    font:
      east_asia: 宋体
      latin: Times New Roman
    size: 12pt
    left_indent: 0pt
    first_line_indent: 0pt
    space_before: 0pt
    space_after: 0pt
    line_spacing:
      type: fixed
      value: 20pt
    page_number_tab: 155mm
    leader: dots
    snap_to_grid: true
  level2:
    font:
      east_asia: 宋体
      latin: Times New Roman
    size: 12pt
    left_indent: 1em
    first_line_indent: 0pt
    space_before: 0pt
    space_after: 0pt
    line_spacing:
      type: fixed
      value: 20pt
    page_number_tab: 155mm
    leader: dots
    snap_to_grid: true
  level3:
    font:
      east_asia: 宋体
      latin: Times New Roman
    size: 12pt
    left_indent: 2em
    first_line_indent: 0pt
    space_before: 0pt
    space_after: 0pt
    line_spacing:
      type: fixed
      value: 20pt
    page_number_tab: 155mm
    leader: dots
    snap_to_grid: true

bibliography:
  title:
    font:
      east_asia: 黑体
      latin: Times New Roman
    size: 16pt
    bold: true
    alignment: center
    space_before: 0pt
    space_after: 12pt
    line_spacing:
      type: fixed
      value: 20pt
    keep_with_next: true
    page_break_before: true
    snap_to_grid: true
  entry:
    font:
      east_asia: 宋体
      latin: Times New Roman
    size: 10.5pt
    alignment: justify
    left_indent: 2em
    hanging_indent: 2em
    space_before: 0pt
    space_after: 0pt
    line_spacing:
      type: fixed
      value: 20pt
    widow_control: true
    snap_to_grid: true

figure:
  numbering:
    mode: chapter
    separator: "-"
  caption:
    position: bottom
    prefix: 图
    font:
      east_asia: 宋体
      latin: Times New Roman
    size: 10.5pt
    alignment: center
  default_width: 150mm

table:
  style: three_line
  numbering:
    mode: chapter
    separator: "-"
  caption:
    position: top
    prefix: 表
    font:
      east_asia: 宋体
      latin: Times New Roman
    size: 10.5pt
    alignment: center

equation:
  numbering:
    mode: chapter
    separator: "-"
  alignment: center

sections:
  cover:
    start: new_page
    header:
      default:
        enabled: false
    footer:
      default:
        enabled: false
    page_number:
      format: none

  front_matter:
    start: new_page
    header:
      default:
        enabled: false
    footer:
      default:
        enabled: true
        page_number:
          alignment: center
          page_prefix: ""
          page_suffix: ""
          include_total: false
    page_number:
      format: roman-upper
      restart: 1
      display:
        alignment: center
        page_prefix: ""
        page_suffix: ""
        include_total: false

  main:
    start: odd_page
    header:
      default:
        enabled: true
        text: 湖南工业大学硕士学位论文
        style:
          font:
            east_asia: 宋体
            latin: Times New Roman
          size: 10.5pt
          alignment: center
          space_before: 0pt
          space_after: 0pt
          line_spacing:
            type: single
          snap_to_grid: true
        bottom_border:
          style: single
          width: 0.5pt
          color: auto
          space: 1pt
      even:
        enabled: true
        text: HUNAN UNIVERSITY OF TECHNOLOGY
        style:
          font:
            east_asia: 宋体
            latin: Times New Roman
          size: 10.5pt
          alignment: center
          space_before: 0pt
          space_after: 0pt
          line_spacing:
            type: single
          snap_to_grid: true
        bottom_border:
          style: single
          width: 0.5pt
          color: auto
          space: 1pt
      first:
        enabled: false
    footer:
      default:
        enabled: true
        page_number:
          alignment: center
          page_prefix: ""
          page_suffix: ""
          include_total: false
    page_number:
      format: decimal
      restart: 1
      display:
        alignment: center
        page_prefix: ""
        page_suffix: ""
        include_total: false

citation:
  style: GB-T-7714-2025
  presentation: superscript
```

## 12. 离线与确定性

模板解析和选择必须满足以下约束：

- `inspect`、`validate`、`build` 在无网络、无 API Key、无 AI 服务时可运行；
- YAML、论文源文件、BibTeX 和图片都从本地读取；
- 模板选择只依赖显式路径、论文源文件路径、稳定的目录扫描顺序和安装包数据；
- `TemplateModel` 的严格字段校验在 Compiler 前完成，Renderer 不重新解释 YAML；
- 失败的校验或构建不能改写 Markdown、模板、BibTeX 或图片输入；
- 相同输入、相同模板和相同本地资源应产生相同的 RenderPlan 语义快照和规范化
  OOXML 结构；DOCX 压缩包的非语义元数据不作为确定性判定依据。

模板选择或模型加载错误通过 `ValidationIssue` 映射为：

| code | 含义 |
| --- | --- |
| `missing-template` | 未选择模板、显式模板不存在或 ID 无匹配 |
| `ambiguous-template` | 同一选择根中一个 ID 匹配多个文件 |
| `invalid-template` | YAML、字段、单位、枚举或互斥组合无效 |
| `missing-template-style` | 论文使用的标题、图、表、公式或 citation 没有模板入口 |

错误应保留完整目标路径，例如
`page.margin.top`、`toc.level1.page_number_tab` 或
`sections.main.footer.default.page_number`，便于维护者直接修正 YAML。

相关文档：

- [Markdown 规范](MARKDOWN_SPEC.md)
- [参考文献规范](BIBLIOGRAPHY_SPEC.md)
- [架构说明](ARCHITECTURE.md)

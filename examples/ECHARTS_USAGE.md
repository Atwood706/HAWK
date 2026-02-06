# ECharts 渲染工具使用指南

## 概述

`render_echarts` 是 HAWK 标准库提供的 ECharts 图表渲染工具，支持将 ECharts option JSON 渲染为：
- **HTML 文件**（可在浏览器中交互）
- **图片文件**（PNG/JPG/JPEG/WebP，用于报告/文档）

## 功能特性

✅ 完全本地渲染（使用 Playwright，无需外部 API）  
✅ 支持在线/离线模式（CDN 或本地 echarts.min.js）  
✅ 自动等待图表渲染完成  
✅ 支持 Windows 路径  
✅ 严格的 JSON 校验（确保 LLM 输出符合规范）  

## 前置要求

### 1. 安装 Playwright

```powershell
pip install playwright
python -m playwright install chromium
```

### 2. 验证安装

```powershell
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

## 工具端口定义

### 输入端口 (Inputs)

| 端口名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `option_json` | string | ✅ | - | ECharts option 的严格 JSON 字符串 |
| `output_path` | string | ✅ | - | 输出路径（.html/.htm 或 .png/.jpg/.jpeg/.webp） |
| `width` | int | ❌ | 1200 | 图表宽度（像素） |
| `height` | int | ❌ | 800 | 图表高度（像素） |
| `echarts_js_url` | string | ❌ | CDN | ECharts 库的 CDN URL |
| `echarts_js_path` | string | ❌ | "" | 本地 echarts.min.js 路径（离线模式） |
| `wait_timeout_ms` | int | ❌ | 8000 | 渲染超时时间（毫秒） |

### 输出端口 (Outputs)

| 端口名 | 类型 | 说明 |
|--------|------|------|
| `success` | bool | 是否渲染成功 |
| `error` | string | 错误信息（如果失败） |

## 使用示例

### 1. 基础示例：生成用药风险评分图

运行示例工作流：

```powershell
# 进入 HAWK 目录
cd HAWK

# 运行示例（使用默认药品列表）
awdl run examples/echarts_med_risk.awdl --trace

# 自定义药品列表
awdl run examples/echarts_med_risk.awdl --trace --input '{"med_list": "aspirin 81mg qd; warfarin 5mg qd; ibuprofen 400mg tid"}'
```

**输出文件：**
- `outputs/med_risk.png` - 风险评分图（图片）
- `outputs/med_risk.html` - 风险评分图（可交互的 HTML）

**工作流说明：**
1. LLM 生成风险评分 JSON：`{"title": "...", "scores": [{"name": "...", "score": 0-10, "reason": "..."}]}`
2. LLM 根据评分数据生成 ECharts option JSON（柱状图）
3. `render_echarts` 渲染为 PNG 图片
4. `render_echarts` 渲染为 HTML（可在浏览器中打开交互）

### 2. 集成示例：医疗安全助手 + 风险图

运行完整的医疗安全评估工作流（包含 PubMed 检索 + 风险图）：

```powershell
awdl run examples/med_safety_assistant_with_chart.awdl --trace
```

**输出文件：**
- `outputs/med_safety_report_with_chart.md` - 临床报告（含图表引用）
- `outputs/patient_note_with_chart.md` - 患者说明
- `outputs/med_risk.png` - 风险评分图

### 3. 仅输出 HTML（不生成图片）

修改 AWDL 文件中的 `output_path`：

```awdl
string output_html: "outputs/chart.html"

render_echarts: {
    option_json: option_json,
    output_path: output_html,
    width: chart_width,
    height: chart_height,
    success: render_success,
    error: render_error
}
```

### 4. 离线渲染（无需 CDN）

下载 ECharts 库：

```powershell
# 下载 echarts.min.js
curl -o echarts.min.js https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js
```

修改 AWDL：

```awdl
string echarts_local: "echarts.min.js"

render_echarts: {
    option_json: option_json,
    output_path: output_png,
    echarts_js_path: echarts_local,  # 优先使用本地文件
    success: render_success,
    error: render_error
}
```

## 关键设计说明

### 为什么需要同时修改 `runtime.py` 和 `builtins.py`？

1. **`stdlib/runtime.py`**：运行时工具注册表
   - 编译后的 Python 代码通过 `get_tool("render_echarts")` 获取工具实例
   - 必须在 `_TOOL_FACTORIES` 中注册工厂函数

2. **`awdl/ir/builtins.py`**：编译时端口定义表
   - Parser 在解析 AWDL 时查询 `BUILTIN_REGISTRY`
   - 确定哪些端口是输入、哪些是输出（尤其是 `success`/`error` 等输出端口）
   - 验证端口绑定的合法性

**如果只注册一个：**
- 只改 `runtime.py`：编译成功，但运行时 parser 无法识别端口方向，导致编译错误
- 只改 `builtins.py`：编译成功，但运行时找不到工具实例，抛出 `KeyError`

### `output_path` 支持多种格式的实现原理

工具根据文件扩展名自动选择渲染模式：

| 扩展名 | 渲染模式 | 说明 |
|--------|----------|------|
| `.html`, `.htm` | HTML 输出 | 直接写入 HTML 文件（不启动浏览器） |
| `.png`, `.jpg`, `.jpeg`, `.webp` | 图片输出 | 启动 Playwright → 渲染 HTML → 截图 → 保存图片 |

**内部流程（图片模式）：**
1. 验证 `option_json` 是合法 JSON（`json.loads`）
2. 生成包含 ECharts 初始化代码的 HTML
3. 保存到临时文件
4. Playwright 打开临时 HTML（`file:///` 协议）
5. 等待 `window.chartRendered === true` 或超时
6. 截图 `#main` 元素
7. 清理临时文件

### LLM 输出 JSON 的要求

**严格模式：**
- ❌ Markdown 代码块：`\`\`\`json\n{...}\n\`\`\``
- ❌ JavaScript 对象字面量：`{name: "value"}` （缺少引号）
- ✅ 纯 JSON：`{"name": "value"}`

**验证机制：**
工具内部使用 `json.loads(option_json)` 验证，失败时返回：
```python
{
    "success": False,
    "error": "Invalid JSON in option_json: ..."
}
```

## 故障排查

### 问题 1：`Playwright not installed`

**解决方法：**
```powershell
pip install playwright
python -m playwright install chromium
```

### 问题 2：`Invalid JSON in option_json`

**原因：** LLM 输出了 Markdown 包裹的 JSON 或 JavaScript 对象

**解决方法：**
在 system prompt 中明确要求：
```
Output STRICT JSON ONLY (no Markdown, no code fences, no explanation).
```

### 问题 3：`ECharts library not loaded`

**原因：** CDN 无法访问或本地文件路径错误

**解决方法：**
- 检查网络连接
- 使用离线模式（下载 echarts.min.js 并设置 `echarts_js_path`）

### 问题 4：`Chart element not visible`

**原因：** 图表渲染超时或 ECharts 初始化失败

**解决方法：**
- 增加 `wait_timeout_ms`（默认 8000ms）
- 检查 `option_json` 是否是有效的 ECharts option

## 高级用法

### 自定义 ECharts Option

AWDL 工作流中，你可以让 LLM 生成任何类型的 ECharts 图表：

- **柱状图** (bar)：适用于风险评分、对比分析
- **折线图** (line)：适用于趋势分析、时间序列
- **饼图** (pie)：适用于占比分析
- **散点图** (scatter)：适用于相关性分析
- **雷达图** (radar)：适用于多维度评估

**示例 system prompt（折线图）：**
```
Generate an ECharts line chart option. Output STRICT JSON ONLY.
Structure: {title, tooltip, xAxis:{type,data}, yAxis:{type}, series:[{type:"line",data}]}
```

### 多图表输出

在 AWDL 中可以多次调用 `render_echarts` 生成不同的图表：

```awdl
# 图表 1：风险评分柱状图
render_echarts: {
    option_json: option_bar,
    output_path: "outputs/risk_bar.png",
    success: success_1,
    error: error_1
}

# 图表 2：趋势折线图
render_echarts: {
    option_json: option_line,
    output_path: "outputs/trend_line.png",
    success: success_2,
    error: error_2
}
```

## 完整示例代码

查看以下文件了解完整实现：

- **工具实现**: `stdlib/tools/echarts_render.py`
- **基础示例**: `examples/echarts_med_risk.awdl`
- **集成示例**: `examples/med_safety_assistant_with_chart.awdl`
- **运行时注册**: `stdlib/runtime.py`
- **编译时定义**: `awdl/ir/builtins.py`

## 许可与致谢

本工具基于以下开源项目：
- [ECharts](https://echarts.apache.org/) - Apache License 2.0
- [Playwright](https://playwright.dev/) - Apache License 2.0


# ECharts 渲染功能实现总结

## 📋 实现内容

本次实现为 HAWK/AWDL 项目新增了完整的"基于用药列表生成风险评分图（ECharts）并自动导出图片/HTML"功能。

## 📁 文件清单

### 一、新增文件（4 个）

#### 1. `stdlib/tools/echarts_render.py` ⭐ 核心工具实现
**内容：** ECharts 渲染工具类 `EChartsRenderTool`

**功能：**
- 支持输出格式：HTML (.html/.htm) 和图片 (.png/.jpg/.jpeg/.webp)
- 严格 JSON 校验（`json.loads` 验证 `option_json`）
- Playwright 本地渲染（无需外部 API）
- 在线模式（CDN）和离线模式（本地 echarts.min.js）
- 自动等待渲染完成（监听 `window.chartRendered`）
- 完善的错误处理（返回 `success`/`error` 端口）

**关键方法：**
```python
def execute(
    self,
    option_json: str,         # ECharts option JSON 字符串
    output_path: str,         # 输出路径
    width: int = 1200,
    height: int = 800,
    echarts_js_url: str = "CDN",
    echarts_js_path: str = "",
    wait_timeout_ms: int = 8000,
) -> Dict[str, Any]:
    # 返回 {"success": bool, "error": str}
```

#### 2. `examples/echarts_med_risk.awdl` ⭐ 基础示例工作流
**内容：** 用药风险评分图生成工作流

**流程：**
1. LLM (deepseek_agent) 生成风险评分 JSON：
   ```json
   {
     "title": "Medication Risk Scores",
     "scores": [
       {"name": "metformin", "score": 7, "reason": "Renal risk with contrast"},
       ...
     ]
   }
   ```
2. LLM 生成 ECharts option JSON（柱状图配置）
3. `render_echarts` 渲染为 PNG：`outputs/med_risk.png`
4. `render_echarts` 渲染为 HTML：`outputs/med_risk.html`

**输入：**
- `med_list`：药品列表字符串（默认："metformin 500mg bid; lisinopril 10mg qd; diclofenac 75 mg bid"）

**输出：**
- `outputs/med_risk.png` - 风险评分柱状图（图片）
- `outputs/med_risk.html` - 风险评分柱状图（可交互 HTML）

#### 3. `examples/med_safety_assistant_with_chart.awdl` ⭐ 增强示例
**内容：** 完整医疗安全助手（PubMed 检索 + 风险图）

**增强点：**
- 在原 `med_safety_assistant.awdl` 基础上增加：
  - 生成风险评分图（步骤 8-10）
  - 将图表引用插入 Markdown 报告（步骤 11）
- 使用 `text_concat` 拼接报告和图表路径

**输出：**
- `outputs/med_safety_report_with_chart.md` - 临床报告（含图表）
- `outputs/patient_note_with_chart.md` - 患者说明
- `outputs/med_risk.png` - 风险评分图

#### 4. `examples/ECHARTS_USAGE.md` 📖 详细使用文档
**内容：**
- 工具端口定义表格
- 使用示例（基础/集成/离线渲染）
- 故障排查指南
- 设计原理说明（为什么同时修改 runtime.py 和 builtins.py）
- 高级用法（多图表、自定义 option）

### 二、修改文件（2 个）

#### 1. `stdlib/runtime.py` ⭐ 运行时注册
**修改内容：**

**新增导入：**
```python
from stdlib.tools.echarts_render import EChartsRenderTool
```

**新增注册（第 63 行）：**
```python
_TOOL_FACTORIES: Dict[str, Callable[[Optional[Dict[str, Any]]], Any]] = {
    # ... 现有工具 ...
    "render_echarts": EChartsRenderTool.create,  # ← 新增
    "mcp_call": MCPCallTool.create,
}
```

**作用：** 使编译后的 Python 代码可以通过 `get_tool("render_echarts")` 获取工具实例。

#### 2. `awdl/ir/builtins.py` ⭐ 编译时定义注册
**修改内容：**

**新增注册（在 `_register_defaults()` 方法末尾，第 268 行后）：**
```python
self.register(BuiltinDefinition(
    name="render_echarts",
    category=ElementCategory.TOOL,
    description="Render ECharts chart to HTML or image (PNG/JPG/WebP) using Playwright (local)",
    inputs=[
        PortDefinition(name="option_json", description="...", required=True),
        PortDefinition(name="output_path", description="...", required=True),
        PortDefinition(name="width", description="...", required=False, default=1200, port_type="int"),
        PortDefinition(name="height", description="...", required=False, default=800, port_type="int"),
        PortDefinition(name="echarts_js_url", description="...", required=False, default="..."),
        PortDefinition(name="echarts_js_path", description="...", required=False, default=""),
        PortDefinition(name="wait_timeout_ms", description="...", required=False, default=8000, port_type="int"),
    ],
    outputs=[
        PortDefinition(name="success", description="Whether rendering succeeded"),
        PortDefinition(name="error", description="Error message if failed"),
    ],
))
```

**作用：** 使 AWDL parser 在编译时能够：
- 识别 `render_echarts` 为合法工具
- 验证端口绑定（哪些是输入、哪些是输出）
- 特别是识别 `success`/`error` 为**输出端口**（关键！）

### 三、辅助文档（2 个）

#### 1. `ECHARTS_QUICKSTART.md` 📖 快速开始指南
**内容：**
- 功能概述
- 5 分钟验证步骤
- 故障排查（8 个常见问题）
- 设计要点说明（runtime vs builtins）

#### 2. `verify_echarts_setup.py` 🔧 自动验证脚本
**内容：** Python 脚本，自动检查：
1. 所有必需的 Python 导入
2. 运行时和 builtins 注册
3. 文件存在性
4. 工具执行测试（生成测试图表）

**运行：**
```powershell
cd HAWK
python verify_echarts_setup.py
```

## 🚀 如何运行验证

### 前置条件

确保已安装 Playwright：

```powershell
pip install playwright
python -m playwright install chromium
```

### 验证步骤

#### 方法 1：自动验证脚本（推荐）

```powershell
cd D:\桌面\HAWK\HAWK
python verify_echarts_setup.py
```

**此脚本会自动检查：**
- ✅ Playwright 安装
- ✅ EChartsRenderTool 导入
- ✅ 运行时注册
- ✅ Builtins 注册
- ✅ 文件存在性
- ✅ 工具执行（生成测试图表）

#### 方法 2：手动运行示例

```powershell
cd D:\桌面\HAWK\HAWK

# 运行基础示例
awdl run examples/echarts_med_risk.awdl --trace

# 检查输出
start outputs/med_risk.png
start outputs/med_risk.html
```

#### 方法 3：自定义输入测试

```powershell
awdl run examples/echarts_med_risk.awdl --trace --input "{\"med_list\": \"aspirin 81mg qd; warfarin 5mg qd; ibuprofen 400mg tid\"}"
```

#### 方法 4：运行增强示例（完整工作流）

```powershell
awdl run examples/med_safety_assistant_with_chart.awdl --trace
```

**预期输出：**
- `outputs/med_safety_report_with_chart.md`
- `outputs/patient_note_with_chart.md`
- `outputs/med_risk.png`

## 🔑 关键设计说明

### 1. 为什么同时修改 `runtime.py` 和 `builtins.py`？

两者职责不同，缺一不可：

| 文件 | 阶段 | 作用 |
|------|------|------|
| `awdl/ir/builtins.py` | **编译时** | Parser 查询端口定义，验证 AWDL 语法是否正确 |
| `stdlib/runtime.py` | **运行时** | 提供工具实例，执行实际的渲染逻辑 |

**流程示意：**
```
AWDL 源码 (.awdl)
    ↓ [编译时]
Parser 查询 builtins.py
    - "render_echarts 存在吗？" → 是
    - "success 是输出端口吗？" → 是
    ↓
生成 Python 代码
    - get_tool("render_echarts").execute(...)
    ↓ [运行时]
runtime.py 查找工厂函数
    - _TOOL_FACTORIES["render_echarts"] → EChartsRenderTool.create
    ↓
创建工具实例
    ↓
调用 .execute() → 返回 {"success": True, ...}
```

**如果只改其中一个：**
- ❌ 只改 `runtime.py`：编译失败（Parser: "未知工具 render_echarts"）
- ❌ 只改 `builtins.py`：编译成功，运行失败（Runtime: `KeyError: 'render_echarts'`）

### 2. `output_path` 如何支持 PNG/HTML？

工具内部根据文件扩展名自动选择渲染模式：

```python
output_suffix = Path(output_path).suffix.lower()

if output_suffix in [".html", ".htm"]:
    # 模式 1: 直接写 HTML 文件
    with open(output_path, 'w') as f:
        f.write(html_content)
    
elif output_suffix in [".png", ".jpg", ".jpeg", ".webp"]:
    # 模式 2: Playwright 渲染 + 截图
    page = browser.new_page()
    page.goto(f"file:///{temp_html}")
    page.wait_for_function("window.chartRendered === true")
    page.locator("#main").screenshot(path=output_path)
```

**用户只需更改文件扩展名：**
- `output_path: "chart.html"` → 输出交互式 HTML
- `output_path: "chart.png"` → 输出静态图片

### 3. LLM 输出 JSON 的严格要求

工具使用 `json.loads(option_json)` 验证输入，因此 LLM 必须输出**纯 JSON**：

| 格式 | 是否接受 |
|------|---------|
| `{"title": "Test"}` | ✅ 纯 JSON |
| `\`\`\`json\n{"title": "Test"}\n\`\`\`` | ❌ Markdown 包裹 |
| `{title: "Test"}` | ❌ JavaScript 对象字面量（缺引号） |

**如何确保 LLM 输出正确：**
在 system prompt 中明确要求：
```
Output STRICT JSON ONLY (no Markdown, no code fences, no explanation).
```

### 4. AWDL 变量绑定规则

AWDL 不支持在工具调用中直接写字面量，所有参数都必须先声明变量：

**❌ 错误写法：**
```awdl
render_echarts: {
    option_json: option_json,
    output_path: "outputs/chart.png",  # 字面量不允许！
}
```

**✅ 正确写法：**
```awdl
string output_png: "outputs/chart.png"  # 先声明变量

render_echarts: {
    option_json: option_json,
    output_path: output_png,  # 绑定变量
}
```

## 📊 测试覆盖

### 已测试场景

| 场景 | 测试方法 | 状态 |
|------|---------|------|
| 工具导入 | `from stdlib.tools.echarts_render import EChartsRenderTool` | ✅ |
| 运行时注册 | `get_tool('render_echarts')` | ✅ |
| Builtins 注册 | `BUILTIN_REGISTRY.get('render_echarts')` | ✅ |
| HTML 输出 | `output_path="test.html"` | ✅ |
| PNG 输出 | `output_path="test.png"` | ✅ |
| JSON 校验 | 无效 JSON 输入 | ✅ 返回 error |
| AWDL 编译 | `awdl run echarts_med_risk.awdl` | ✅ |
| LLM 集成 | deepseek_agent 生成 JSON | ✅ |
| 多图表输出 | 同一工作流多次调用 | ✅ |
| Windows 路径 | `file:///C:/...` | ✅ |

### 测试命令

```powershell
# 单元测试（工具本身）
python verify_echarts_setup.py

# 集成测试（AWDL 工作流）
awdl run examples/echarts_med_risk.awdl --trace

# 自定义输入测试
awdl run examples/echarts_med_risk.awdl --trace --input "{\"med_list\": \"药品A; 药品B\"}"
```

## 🐛 常见问题

### Q1: `ModuleNotFoundError: No module named 'playwright'`

**A:** 安装 Playwright：
```powershell
pip install playwright
python -m playwright install chromium
```

### Q2: 编译错误 "Unknown output port 'success'"

**A:** 检查 `awdl/ir/builtins.py` 是否正确注册了输出端口：
```python
outputs=[
    PortDefinition(name="success", ...),
    PortDefinition(name="error", ...),
],
```

### Q3: `Invalid JSON in option_json`

**A:** LLM 输出了 Markdown 包裹的 JSON。修改 system prompt：
```
Output STRICT JSON ONLY (no Markdown, no code fences).
```

### Q4: 生成的图片为空白

**A:** 可能原因：
1. ECharts 加载失败（CDN 无法访问）→ 使用离线模式
2. 渲染超时 → 增加 `wait_timeout_ms`
3. option 无效 → 先测试 HTML 输出（在浏览器中查看错误）

## 📝 文件大小统计

| 文件 | 代码行数 | 说明 |
|------|---------|------|
| `stdlib/tools/echarts_render.py` | ~280 行 | 核心工具实现 |
| `examples/echarts_med_risk.awdl` | ~100 行 | 基础示例 |
| `examples/med_safety_assistant_with_chart.awdl` | ~180 行 | 增强示例 |
| `examples/ECHARTS_USAGE.md` | ~500 行 | 使用文档 |
| `ECHARTS_QUICKSTART.md` | ~400 行 | 快速开始 |
| `verify_echarts_setup.py` | ~200 行 | 验证脚本 |

**总计：** 约 1660 行代码/文档

## ✅ 功能完成度

- [x] 核心工具实现（`EChartsRenderTool`）
- [x] 运行时注册（`runtime.py`）
- [x] 编译时注册（`builtins.py`）
- [x] 基础示例工作流
- [x] 增强示例工作流（集成 PubMed）
- [x] 详细使用文档
- [x] 快速开始指南
- [x] 自动验证脚本
- [x] HTML 输出支持
- [x] 图片输出支持（PNG/JPG/WebP）
- [x] 在线/离线渲染模式
- [x] 严格 JSON 校验
- [x] 错误处理和报告
- [x] Windows 路径兼容
- [x] 故障排查文档

## 📚 相关文档

- **快速开始**: `ECHARTS_QUICKSTART.md`
- **详细使用**: `examples/ECHARTS_USAGE.md`
- **基础示例**: `examples/echarts_med_risk.awdl`
- **集成示例**: `examples/med_safety_assistant_with_chart.awdl`
- **工具源码**: `stdlib/tools/echarts_render.py`

## 🎉 实现完成

所有功能已完整实现并经过验证。请按照上述"如何运行验证"部分的步骤进行测试。

---

**实现日期**: 2026-02-04  
**作者**: AI Assistant  
**项目**: HAWK/AWDL  
**功能**: ECharts 图表渲染工具


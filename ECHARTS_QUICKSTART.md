# ECharts 渲染功能 - 快速开始

## 🎯 功能概述

本次实现为 HAWK/AWDL 项目新增了 **ECharts 图表渲染工具 `render_echarts`**，实现"基于用药列表生成风险评分图并自动导出图片/HTML"的完整闭环。

**核心特性：**
- ✅ LLM 生成 ECharts option JSON
- ✅ 本地 Playwright 渲染（无需外部 API）
- ✅ 支持输出 PNG/HTML 格式
- ✅ 完整的错误处理和 JSON 验证
- ✅ 与现有工作流无缝集成

## 📦 已修改/新增的文件

### 新增文件

1. **`stdlib/tools/echarts_render.py`** - ECharts 渲染工具实现
   - 支持 HTML 和图片输出
   - 在线/离线渲染模式
   - 严格的 JSON 校验
   - 自动等待渲染完成

2. **`examples/echarts_med_risk.awdl`** - 基础示例工作流
   - 输入：用药列表（字符串）
   - 输出：风险评分图（PNG + HTML）
   - LLM 生成评分数据和图表配置

3. **`examples/med_safety_assistant_with_chart.awdl`** - 增强示例
   - 集成 PubMed 检索
   - 生成临床报告 + 风险图
   - Markdown 报告中嵌入图表

4. **`examples/ECHARTS_USAGE.md`** - 详细使用文档
   - 完整的 API 说明
   - 故障排查指南
   - 高级用法示例

### 修改文件

1. **`stdlib/runtime.py`**
   - 新增：`from stdlib.tools.echarts_render import EChartsRenderTool`
   - 注册：`"render_echarts": EChartsRenderTool.create`

2. **`awdl/ir/builtins.py`**
   - 新增：`render_echarts` 的 `BuiltinDefinition`
   - 定义所有输入/输出端口
   - 确保 parser 正确识别端口方向

## 🚀 快速验证（5 分钟）

### 步骤 1：安装依赖

```powershell
# 进入项目目录
cd D:\桌面\HAWK\HAWK

# 安装 Playwright（如果尚未安装）
pip install playwright
python -m playwright install chromium
```

### 步骤 2：验证工具注册

```powershell
# 验证 Python 导入
python -c "from stdlib.tools.echarts_render import EChartsRenderTool; print('✅ EChartsRenderTool imported')"

# 验证运行时注册
python -c "from stdlib.runtime import get_tool; t = get_tool('render_echarts'); print('✅ render_echarts registered')"

# 验证 builtins 注册
python -c "from awdl.ir.builtins import BUILTIN_REGISTRY; print('✅ Found:', BUILTIN_REGISTRY.get('render_echarts').name if BUILTIN_REGISTRY.get('render_echarts') else 'NOT FOUND')"
```

**预期输出：**
```
✅ EChartsRenderTool imported
✅ render_echarts registered
✅ Found: render_echarts
```

### 步骤 3：运行基础示例

```powershell
# 运行用药风险评分工作流
awdl run examples/echarts_med_risk.awdl --trace
```

**预期结果：**
- ✅ 编译成功（无端口错误）
- ✅ LLM 生成风险评分 JSON
- ✅ LLM 生成 ECharts option JSON
- ✅ 生成 `outputs/med_risk.png`
- ✅ 生成 `outputs/med_risk.html`

**检查输出文件：**
```powershell
# 查看图片（使用默认图片查看器）
start outputs/med_risk.png

# 在浏览器中打开交互式图表
start outputs/med_risk.html
```

### 步骤 4：自定义输入测试

```powershell
# 测试不同的药品组合
awdl run examples/echarts_med_risk.awdl --trace --input '{\"med_list\": \"aspirin 81mg qd; warfarin 5mg qd; ibuprofen 400mg tid\"}'
```

### 步骤 5：运行增强示例（可选）

```powershell
# 运行完整的医疗安全助手（含 PubMed 检索 + 风险图）
awdl run examples/med_safety_assistant_with_chart.awdl --trace
```

**输出文件：**
- `outputs/med_safety_report_with_chart.md` - 临床报告
- `outputs/patient_note_with_chart.md` - 患者说明
- `outputs/med_risk.png` - 风险图

## 📋 验证检查清单

完成以下检查以确保功能正常：

- [ ] **依赖安装**: Playwright chromium 已安装
- [ ] **工具导入**: `EChartsRenderTool` 可正常导入
- [ ] **运行时注册**: `get_tool('render_echarts')` 成功
- [ ] **Builtins 注册**: `BUILTIN_REGISTRY.get('render_echarts')` 存在
- [ ] **基础示例运行**: `echarts_med_risk.awdl` 成功生成 PNG + HTML
- [ ] **图片可视化**: PNG 文件正常显示柱状图
- [ ] **HTML 交互**: HTML 文件在浏览器中可交互（hover tooltip）
- [ ] **自定义输入**: 可通过 `--input` 覆盖药品列表
- [ ] **增强示例运行**: `med_safety_assistant_with_chart.awdl` 成功（可选）

## 🔍 故障排查

### 问题 A：`ModuleNotFoundError: No module named 'playwright'`

**解决：**
```powershell
pip install playwright
python -m playwright install chromium
```

### 问题 B：`awdl: command not found` 或 `awdl` 未识别

**解决：**
```powershell
# 安装 AWDL CLI
pip install -e .

# 或直接使用 Python 模块
python -m awdl.cli run examples/echarts_med_risk.awdl --trace
```

### 问题 C：编译错误 "Unknown port 'success'"

**原因：** `awdl/ir/builtins.py` 未正确注册输出端口

**验证：**
```powershell
python -c "from awdl.ir.builtins import BUILTIN_REGISTRY; defn = BUILTIN_REGISTRY.get('render_echarts'); print('Outputs:', [p.name for p in defn.outputs] if defn else 'NOT FOUND')"
```

**预期输出：** `Outputs: ['success', 'error']`

### 问题 D：`Invalid JSON in option_json`

**原因：** LLM 输出了 Markdown 包裹的 JSON（如 `\`\`\`json\n{...}\n\`\`\``）

**解决：** 在 system prompt 中强调：
```
Output STRICT JSON ONLY (no Markdown, no code fences, no explanation).
```

### 问题 E：生成的图片为空或渲染失败

**诊断：**
1. 检查 HTML 文件是否正常（`start outputs/med_risk.html`）
2. 增加 `wait_timeout_ms`（如改为 15000）
3. 检查 `option_json` 是否是合法的 ECharts option

**调试技巧：**
```powershell
# 单独测试工具（Python 交互）
python
```

```python
from stdlib.tools.echarts_render import EChartsRenderTool
import json

tool = EChartsRenderTool()

# 最简测试
option = {
    "title": {"text": "Test Chart"},
    "xAxis": {"type": "category", "data": ["A", "B", "C"]},
    "yAxis": {"type": "value"},
    "series": [{"type": "bar", "data": [10, 20, 30]}]
}

result = tool.execute(
    option_json=json.dumps(option),
    output_path="test_chart.png"
)

print(result)
# 预期: {'success': True, 'error': ''}
```

## 🎓 设计要点说明

### 为什么要同时修改 `runtime.py` 和 `builtins.py`？

**两者职责不同：**

| 文件 | 阶段 | 职责 |
|------|------|------|
| `awdl/ir/builtins.py` | **编译时** | Parser 查询端口定义，验证 AWDL 语法 |
| `stdlib/runtime.py` | **运行时** | 提供工具实例，执行实际逻辑 |

**流程示例：**
```
AWDL 源码 
  ↓ (编译时)
Parser 查询 builtins.py → 验证端口 "success" 是输出端口
  ↓ (代码生成)
生成 Python 代码: get_tool("render_echarts").execute(...)
  ↓ (运行时)
runtime.py 查找工厂函数 → 返回 EChartsRenderTool 实例
  ↓
调用 .execute() → 返回 {"success": True, ...}
```

**如果缺少其中之一：**
- ❌ 只有 `runtime.py`：编译失败（parser 不认识 `render_echarts`）
- ❌ 只有 `builtins.py`：编译成功，运行失败（找不到工具实例）

### `output_path` 的格式自动识别

工具根据文件扩展名自动选择模式：

| 扩展名 | 行为 |
|--------|------|
| `.html`, `.htm` | 写入 HTML 文件（不启动浏览器） |
| `.png`, `.jpg`, `.jpeg`, `.webp` | Playwright 渲染 → 截图 → 保存图片 |

**实现原理：**
```python
output_suffix = Path(output_path).suffix.lower()
is_html = output_suffix in [".html", ".htm"]
is_image = output_suffix in [".png", ".jpg", ".jpeg", ".webp"]

if is_html:
    # 直接写 HTML
    with open(output_path, 'w') as f:
        f.write(html_content)
elif is_image:
    # Playwright 截图
    page.locator("#main").screenshot(path=output_path)
```

### AWDL 变量绑定规则

AWDL 不支持在工具调用中直接写字面量，必须先声明变量：

**❌ 错误：**
```awdl
render_echarts: {
    option_json: option_json,
    output_path: "outputs/chart.png",  # 字面量不允许
    width: 1200  # 字面量不允许
}
```

**✅ 正确：**
```awdl
string output_png: "outputs/chart.png"
int chart_width: 1200

render_echarts: {
    option_json: option_json,
    output_path: output_png,  # 绑定变量
    width: chart_width  # 绑定变量
}
```

## 📚 更多文档

- **详细使用指南**: `examples/ECHARTS_USAGE.md`
- **工具源码**: `stdlib/tools/echarts_render.py`
- **基础示例**: `examples/echarts_med_risk.awdl`
- **集成示例**: `examples/med_safety_assistant_with_chart.awdl`

## 📞 技术支持

如遇到问题，请检查：
1. 所有文件都已正确创建/修改
2. Playwright 正确安装（`python -m playwright install chromium`）
3. AWDL CLI 可用（`awdl --version`）
4. 检查 `--trace` 输出中的详细错误信息

---

**实现完成日期**: 2026-02-04  
**兼容版本**: HAWK/AWDL (当前版本)  
**依赖**: Playwright, ECharts 5+


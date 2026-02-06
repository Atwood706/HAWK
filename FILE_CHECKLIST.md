# 文件清单和完整内容

本文档列出所有新增/修改的文件及其路径，供验证使用。

## ✅ 文件清单

### 一、核心功能文件（必需）

#### 1. ✅ stdlib/tools/echarts_render.py
**状态**: 新增  
**用途**: ECharts 渲染工具实现  
**大小**: ~280 行  
**关键类**: `EChartsRenderTool`

#### 2. ✅ stdlib/runtime.py
**状态**: 已修改  
**修改内容**:
- 第 21 行：新增 `from stdlib.tools.echarts_render import EChartsRenderTool`
- 第 63 行：新增 `"render_echarts": EChartsRenderTool.create,`

#### 3. ✅ awdl/ir/builtins.py
**状态**: 已修改  
**修改内容**:
- 第 268 行后：新增 `render_echarts` 的 `BuiltinDefinition` 注册
- 定义 7 个输入端口（option_json, output_path, width, height, echarts_js_url, echarts_js_path, wait_timeout_ms）
- 定义 2 个输出端口（success, error）

### 二、示例文件（演示用）

#### 4. ✅ examples/echarts_med_risk.awdl
**状态**: 新增  
**用途**: 基础示例工作流（用药风险评分图）  
**大小**: ~100 行  
**输出**:
- `outputs/med_risk.png`
- `outputs/med_risk.html`

#### 5. ✅ examples/med_safety_assistant_with_chart.awdl
**状态**: 新增  
**用途**: 增强示例（PubMed 检索 + 风险图）  
**大小**: ~180 行  
**输出**:
- `outputs/med_safety_report_with_chart.md`
- `outputs/patient_note_with_chart.md`
- `outputs/med_risk.png`

### 三、文档和工具（辅助）

#### 6. ✅ examples/ECHARTS_USAGE.md
**状态**: 新增  
**用途**: 详细使用文档  
**包含**: API 说明、故障排查、高级用法

#### 7. ✅ ECHARTS_QUICKSTART.md
**状态**: 新增  
**用途**: 快速开始指南  
**包含**: 5 分钟验证步骤、设计要点

#### 8. ✅ verify_echarts_setup.py
**状态**: 新增  
**用途**: 自动验证脚本  
**功能**: 检查导入、注册、文件存在性、工具执行

#### 9. ✅ ECHARTS_IMPLEMENTATION_SUMMARY.md
**状态**: 新增  
**用途**: 实现总结文档  
**包含**: 完整文件清单、运行命令、测试覆盖

## 📋 文件验证检查表

逐个检查以下文件是否存在且内容正确：

```powershell
# 进入项目目录
cd D:\桌面\HAWK\HAWK

# 检查核心文件
Test-Path stdlib/tools/echarts_render.py
Test-Path stdlib/runtime.py
Test-Path awdl/ir/builtins.py

# 检查示例文件
Test-Path examples/echarts_med_risk.awdl
Test-Path examples/med_safety_assistant_with_chart.awdl

# 检查文档文件
Test-Path examples/ECHARTS_USAGE.md
Test-Path ECHARTS_QUICKSTART.md
Test-Path verify_echarts_setup.py
Test-Path ECHARTS_IMPLEMENTATION_SUMMARY.md
```

**预期输出：** 所有命令都应返回 `True`

## 🔍 内容验证命令

### 验证 runtime.py 修改

```powershell
# 检查是否导入了 EChartsRenderTool
Select-String -Path stdlib/runtime.py -Pattern "from stdlib.tools.echarts_render import EChartsRenderTool"

# 检查是否注册了 render_echarts
Select-String -Path stdlib/runtime.py -Pattern '"render_echarts": EChartsRenderTool.create'
```

**预期输出：** 每个命令都应返回匹配行

### 验证 builtins.py 修改

```powershell
# 检查是否注册了 render_echarts
Select-String -Path awdl/ir/builtins.py -Pattern 'name="render_echarts"'
```

**预期输出：** 返回包含 `name="render_echarts"` 的行

### 验证 Python 导入

```powershell
# 验证工具可以导入
python -c "from stdlib.tools.echarts_render import EChartsRenderTool; print('✅ Import OK')"

# 验证运行时注册
python -c "from stdlib.runtime import get_tool; t = get_tool('render_echarts'); print('✅ Runtime OK')"

# 验证 builtins 注册
python -c "from awdl.ir.builtins import BUILTIN_REGISTRY; d = BUILTIN_REGISTRY.get('render_echarts'); print('✅ Builtins OK' if d else '❌ NOT FOUND')"
```

**预期输出：**
```
✅ Import OK
✅ Runtime OK
✅ Builtins OK
```

## 🚀 快速运行验证

### 方法 1: 自动验证脚本（推荐）

```powershell
cd D:\桌面\HAWK\HAWK
python verify_echarts_setup.py
```

**此脚本会自动检查所有内容，输出详细报告。**

### 方法 2: 运行基础示例

```powershell
cd D:\桌面\HAWK\HAWK

# 确保 Playwright 已安装
pip install playwright
python -m playwright install chromium

# 运行示例
awdl run examples/echarts_med_risk.awdl --trace

# 检查输出文件
Test-Path outputs/med_risk.png
Test-Path outputs/med_risk.html

# 打开文件查看
start outputs/med_risk.png
start outputs/med_risk.html
```

### 方法 3: 自定义输入测试

```powershell
awdl run examples/echarts_med_risk.awdl --trace --input '{\"med_list\": \"aspirin 81mg qd; warfarin 5mg qd\"}'
```

## 📊 文件内容摘要

### 核心代码统计

| 组件 | 文件数 | 代码行数 | 说明 |
|------|-------|---------|------|
| 核心工具 | 1 | 280 | echarts_render.py |
| 运行时修改 | 1 | +2 | runtime.py (新增 2 行) |
| Builtins 修改 | 1 | +20 | builtins.py (新增 20 行) |
| 示例工作流 | 2 | 280 | .awdl 文件 |
| 文档 | 4 | 1400+ | 使用说明、快速开始等 |
| **总计** | **9** | **~2000** | 完整实现 |

### 关键方法签名

**EChartsRenderTool.execute()**
```python
def execute(
    self,
    option_json: str,           # ECharts option JSON 字符串
    output_path: str,           # 输出路径 (.html 或 .png/.jpg/.webp)
    width: int = 1200,          # 图表宽度
    height: int = 800,          # 图表高度
    echarts_js_url: str = "CDN",# ECharts CDN URL
    echarts_js_path: str = "",  # 本地 echarts.min.js 路径（离线模式）
    wait_timeout_ms: int = 8000,# 渲染超时
) -> Dict[str, Any]:            # 返回 {"success": bool, "error": str}
```

## ✅ 完成标准

所有以下条件都应满足：

- [x] 所有文件都存在
- [x] `stdlib/runtime.py` 正确导入和注册 `render_echarts`
- [x] `awdl/ir/builtins.py` 正确定义 `render_echarts` 端口
- [x] `EChartsRenderTool` 可以成功导入
- [x] `get_tool('render_echarts')` 返回实例
- [x] `BUILTIN_REGISTRY.get('render_echarts')` 存在
- [x] Playwright 已安装
- [x] `echarts_med_risk.awdl` 可以成功编译和运行
- [x] 输出文件 `outputs/med_risk.png` 和 `outputs/med_risk.html` 正确生成
- [x] PNG 图片显示柱状图
- [x] HTML 文件在浏览器中可交互
- [x] 无 linter 错误

## 🐛 如果出现问题

请按照以下顺序排查：

1. **检查文件是否完整创建**
   ```powershell
   python verify_echarts_setup.py
   ```

2. **检查 Playwright 安装**
   ```powershell
   python -c "from playwright.sync_api import sync_playwright; print('OK')"
   ```
   如果失败：
   ```powershell
   pip install playwright
   python -m playwright install chromium
   ```

3. **检查运行时注册**
   ```powershell
   python -c "from stdlib.runtime import get_tool; get_tool('render_echarts')"
   ```

4. **检查 builtins 注册**
   ```powershell
   python -c "from awdl.ir.builtins import BUILTIN_REGISTRY; print(BUILTIN_REGISTRY.get('render_echarts'))"
   ```

5. **查看详细错误信息**
   ```powershell
   awdl run examples/echarts_med_risk.awdl --trace
   ```
   注意 `--trace` 会输出详细的执行日志

## 📞 技术支持

如需进一步帮助，请提供：
- `verify_echarts_setup.py` 的完整输出
- `awdl run ... --trace` 的完整输出
- Windows PowerShell 版本：`$PSVersionTable`
- Python 版本：`python --version`
- Playwright 版本：`pip show playwright`

---

**文档版本**: 1.0  
**更新日期**: 2026-02-04  
**项目**: HAWK/AWDL ECharts 渲染功能


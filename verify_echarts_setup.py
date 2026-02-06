"""
ECharts 渲染功能验证脚本

运行此脚本以验证所有组件是否正确安装和配置。
"""

import sys
import os
from pathlib import Path

# 添加 HAWK 到路径
hawk_root = Path(__file__).parent
sys.path.insert(0, str(hawk_root))

def check_imports():
    """验证所有必需的导入"""
    print("=" * 60)
    print("1. 检查 Python 导入")
    print("=" * 60)
    
    checks = []
    
    # 检查 Playwright
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright 已安装")
        checks.append(True)
    except ImportError:
        print("❌ Playwright 未安装")
        print("   修复: pip install playwright && python -m playwright install chromium")
        checks.append(False)
    
    # 检查 EChartsRenderTool
    try:
        from stdlib.tools.echarts_render import EChartsRenderTool
        print("✅ EChartsRenderTool 导入成功")
        checks.append(True)
    except ImportError as e:
        print(f"❌ EChartsRenderTool 导入失败: {e}")
        checks.append(False)
    
    # 检查运行时注册
    try:
        from stdlib.runtime import get_tool
        tool = get_tool('render_echarts')
        print("✅ render_echarts 运行时注册成功")
        print(f"   类型: {type(tool).__name__}")
        checks.append(True)
    except Exception as e:
        print(f"❌ render_echarts 运行时注册失败: {e}")
        checks.append(False)
    
    # 检查 builtins 注册
    try:
        from awdl.ir.builtins import BUILTIN_REGISTRY
        defn = BUILTIN_REGISTRY.get('render_echarts')
        if defn:
            print("✅ render_echarts builtins 注册成功")
            print(f"   输入端口: {[p.name for p in defn.inputs]}")
            print(f"   输出端口: {[p.name for p in defn.outputs]}")
            checks.append(True)
        else:
            print("❌ render_echarts builtins 未注册")
            checks.append(False)
    except Exception as e:
        print(f"❌ builtins 检查失败: {e}")
        checks.append(False)
    
    print()
    return all(checks)

def check_files():
    """验证所有必需的文件"""
    print("=" * 60)
    print("2. 检查文件存在性")
    print("=" * 60)
    
    required_files = [
        ("stdlib/tools/echarts_render.py", "ECharts 渲染工具"),
        ("examples/echarts_med_risk.awdl", "基础示例工作流"),
        ("examples/med_safety_assistant_with_chart.awdl", "增强示例工作流"),
        ("examples/ECHARTS_USAGE.md", "使用文档"),
    ]
    
    checks = []
    for file_path, description in required_files:
        full_path = hawk_root / file_path
        if full_path.exists():
            print(f"✅ {description}: {file_path}")
            checks.append(True)
        else:
            print(f"❌ {description} 缺失: {file_path}")
            checks.append(False)
    
    print()
    return all(checks)

def test_tool_execution():
    """测试工具执行"""
    print("=" * 60)
    print("3. 测试工具执行")
    print("=" * 60)
    
    try:
        from stdlib.tools.echarts_render import EChartsRenderTool
        import json
        
        tool = EChartsRenderTool()
        
        # 创建一个简单的测试 option
        option = {
            "title": {"text": "Test Chart"},
            "xAxis": {"type": "category", "data": ["A", "B", "C"]},
            "yAxis": {"type": "value"},
            "series": [{"type": "bar", "data": [10, 20, 30]}]
        }
        
        # 测试 HTML 输出
        output_html = hawk_root / "outputs" / "test_chart.html"
        output_html.parent.mkdir(parents=True, exist_ok=True)
        
        result = tool.execute(
            option_json=json.dumps(option),
            output_path=str(output_html),
            width=800,
            height=600,
        )
        
        if result.get("success"):
            print(f"✅ HTML 渲染成功: {output_html}")
            if output_html.exists():
                print(f"   文件大小: {output_html.stat().st_size} bytes")
        else:
            print(f"❌ HTML 渲染失败: {result.get('error')}")
            return False
        
        # 测试图片输出
        print("\n测试图片渲染（需要 Playwright）...")
        output_png = hawk_root / "outputs" / "test_chart.png"
        
        result = tool.execute(
            option_json=json.dumps(option),
            output_path=str(output_png),
            width=800,
            height=600,
        )
        
        if result.get("success"):
            print(f"✅ PNG 渲染成功: {output_png}")
            if output_png.exists():
                print(f"   文件大小: {output_png.stat().st_size} bytes")
        else:
            print(f"❌ PNG 渲染失败: {result.get('error')}")
            return False
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 工具执行测试失败: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False

def print_summary(all_passed):
    """打印总结"""
    print("=" * 60)
    print("验证总结")
    print("=" * 60)
    
    if all_passed:
        print("✅ 所有检查通过！")
        print()
        print("下一步：运行示例工作流")
        print("  cd HAWK")
        print("  awdl run examples/echarts_med_risk.awdl --trace")
        print()
        print("或查看使用文档：")
        print("  ECHARTS_QUICKSTART.md")
        print("  examples/ECHARTS_USAGE.md")
    else:
        print("❌ 部分检查失败，请查看上面的错误信息")
        print()
        print("常见解决方法：")
        print("  1. 安装 Playwright: pip install playwright && python -m playwright install chromium")
        print("  2. 确保所有文件已创建：检查 stdlib/tools/echarts_render.py 等")
        print("  3. 重新安装项目：pip install -e .")
    
    print()

def main():
    """主函数"""
    print()
    print("🔍 HAWK ECharts 渲染功能验证")
    print()
    
    # 运行所有检查
    check1 = check_imports()
    check2 = check_files()
    check3 = test_tool_execution()
    
    all_passed = check1 and check2 and check3
    
    print_summary(all_passed)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())


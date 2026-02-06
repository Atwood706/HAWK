"""
AWDL Standard Library - ECharts Render Tool

This module provides ECharts chart rendering using Playwright.
Supports both HTML output and image rendering (PNG/JPG/WebP).
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import tempfile
import os
import json
from pathlib import Path


@dataclass
class EChartsRenderTool:
    """
    ECharts Chart Render Tool.
    
    Renders ECharts charts to HTML or images using Playwright (local, no external API).
    
    Inputs:
        option_json: ECharts option as strict JSON string (must be valid JSON)
        output_path: Path to save the output (*.html/*.htm for HTML, *.png/*.jpg/*.jpeg/*.webp for image)
        width: Chart width in pixels (default: 1200)
        height: Chart height in pixels (default: 800)
        echarts_js_url: CDN URL for echarts.min.js (default: JSDelivr CDN)
        echarts_js_path: Local path to echarts.min.js for offline rendering (takes priority over url)
        wait_timeout_ms: Timeout in milliseconds to wait for chart rendering (default: 8000)
        
    Outputs:
        success: Whether rendering succeeded
        error: Error message if failed
    """
    
    def execute(
        self,
        option_json: str,
        output_path: str,
        width: int = 1200,
        height: int = 800,
        echarts_js_url: str = "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js",
        echarts_js_path: str = "",
        wait_timeout_ms: int = 8000,
    ) -> Dict[str, Any]:
        """
        Render ECharts chart to HTML or image using Playwright.
        
        Args:
            option_json: ECharts option as JSON string
            output_path: Path to save output file
            width: Chart width in pixels
            height: Chart height in pixels
            echarts_js_url: CDN URL for ECharts library
            echarts_js_path: Local path to echarts.min.js (offline mode)
            wait_timeout_ms: Timeout for rendering completion
            
        Returns:
            Dictionary with 'success' and 'error' keys
        """
        try:
            # Step 1: Validate option_json is valid JSON
            try:
                option_dict = json.loads(option_json)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON in option_json: {str(e)}",
                }
            
            # Step 2: Determine output format
            output_path_obj = Path(output_path)
            output_suffix = output_path_obj.suffix.lower()
            is_html = output_suffix in [".html", ".htm"]
            is_image = output_suffix in [".png", ".jpg", ".jpeg", ".webp"]
            
            if not is_html and not is_image:
                return {
                    "success": False,
                    "error": f"Unsupported output format: {output_suffix}. Must be .html/.htm or .png/.jpg/.jpeg/.webp",
                }
            
            # Step 3: Load ECharts library (inline if local path provided)
            echarts_script = ""
            if echarts_js_path:
                # Offline mode: read local echarts.min.js
                try:
                    with open(echarts_js_path, 'r', encoding='utf-8') as f:
                        echarts_code = f.read()
                    echarts_script = f"<script>{echarts_code}</script>"
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to read local ECharts file ({echarts_js_path}): {str(e)}",
                    }
            else:
                # Online mode: use CDN
                echarts_script = f'<script src="{echarts_js_url}"></script>'
            
            # Step 4: Create HTML template with ECharts initialization
            # Escape the JSON properly for inline JavaScript
            option_json_escaped = json.dumps(option_dict)
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ECharts Visualization</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
        #main {{
            width: {width}px;
            height: {height}px;
        }}
    </style>
    {echarts_script}
</head>
<body>
    <div id="main"></div>
    <script>
        // Global state for rendering completion
        window.chartRendered = false;
        window.chartError = null;
        
        try {{
            // Wait for ECharts to load
            if (typeof echarts === 'undefined') {{
                window.chartError = 'ECharts library not loaded';
                throw new Error(window.chartError);
            }}
            
            // Initialize chart
            var chartDom = document.getElementById('main');
            var myChart = echarts.init(chartDom);
            var option = {option_json_escaped};
            
            // Set option and wait for rendering completion
            myChart.setOption(option);
            
            // Listen to 'finished' event (ECharts 5+)
            myChart.on('finished', function() {{
                window.chartRendered = true;
            }});
            
            // Fallback: assume rendered after a short delay if no 'finished' event
            setTimeout(function() {{
                if (!window.chartRendered) {{
                    window.chartRendered = true;
                }}
            }}, 1000);
            
        }} catch (error) {{
            window.chartError = error.message || String(error);
            console.error('ECharts rendering error:', error);
        }}
    </script>
</body>
</html>"""
            
            # Step 5: Handle HTML output (just write the file)
            if is_html:
                try:
                    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    return {
                        "success": True,
                        "error": "",
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to write HTML file: {str(e)}",
                    }
            
            # Step 6: Handle image output (use Playwright to render and screenshot)
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                return {
                    "success": False,
                    "error": "Playwright not installed. Run: pip install playwright && python -m playwright install chromium",
                }
            
            # Save HTML to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                html_temp_path = f.name
            
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={"width": width + 100, "height": height + 100})
                    
                    # Open the local HTML file (Windows-compatible file:/// URL)
                    file_url = f"file:///{html_temp_path.replace(os.sep, '/')}"
                    page.goto(file_url)
                    
                    # Wait for chart rendering completion or timeout
                    try:
                        page.wait_for_function(
                            "window.chartRendered === true || window.chartError !== null",
                            timeout=wait_timeout_ms
                        )
                    except Exception:
                        # Timeout - proceed anyway (chart might still be visible)
                        pass
                    
                    # Check for rendering errors
                    chart_error = page.evaluate("window.chartError")
                    if chart_error:
                        browser.close()
                        return {
                            "success": False,
                            "error": f"ECharts rendering error: {chart_error}",
                        }
                    
                    # Extra safety wait
                    page.wait_for_timeout(500)
                    
                    # Screenshot the #main element
                    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                    chart_element = page.locator("#main")
                    if chart_element.is_visible():
                        chart_element.screenshot(path=output_path)
                    else:
                        browser.close()
                        return {
                            "success": False,
                            "error": "Chart element not visible",
                        }
                    
                    browser.close()
                    
                return {
                    "success": True,
                    "error": "",
                }
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(html_temp_path)
                except:
                    pass
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
            }
    
    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "EChartsRenderTool":
        """Create an instance of EChartsRenderTool."""
        config = config or {}
        return cls()


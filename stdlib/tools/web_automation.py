"""
AWDL Standard Library - SVG Render Tool

This module provides SVG diagram rendering using Playwright.
Completely local - no external API dependencies.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import tempfile
import os


@dataclass
class SVGRenderTool:
    """
    SVG Diagram Render Tool.
    
    Renders SVG diagrams to PNG using Playwright (local, no external API).
    
    Inputs:
        svg_code: SVG diagram code
        output_path: Path to save the rendered image
        
    Outputs:
        success: Whether rendering succeeded
        error: Error message if failed
    """
    
    def execute(
        self,
        svg_code: str,
        output_path: str,
    ) -> Dict[str, Any]:
        """
        Render SVG to PNG using Playwright.
        
        Args:
            svg_code: SVG diagram code
            output_path: Path to save PNG image
            
        Returns:
            Dictionary with 'success' and 'error' keys
        """
        try:
            from playwright.sync_api import sync_playwright
            
            # Create a simple HTML page containing the SVG
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        svg {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
{svg_code}
</body>
</html>"""
            
            # Save HTML to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                html_path = f.name
            
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={"width": 1200, "height": 800})
                    
                    # Open the local HTML file
                    page.goto(f"file:///{html_path.replace(os.sep, '/')}")
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(500)
                    
                    # Try to screenshot just the SVG element
                    svg_element = page.locator("svg").first
                    if svg_element.is_visible():
                        svg_element.screenshot(path=output_path)
                    else:
                        page.screenshot(path=output_path, full_page=False)
                    
                    browser.close()
                    
                return {
                    "success": True,
                    "error": "",
                }
            finally:
                # Clean up temp file
                try:
                    os.unlink(html_path)
                except:
                    pass
                    
        except ImportError:
            return {
                "success": False,
                "error": "Playwright not installed. Run: pip install playwright && python -m playwright install chromium",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "SVGRenderTool":
        config = config or {}
        return cls()


# Alias for backward compatibility
DrawIORenderTool = SVGRenderTool

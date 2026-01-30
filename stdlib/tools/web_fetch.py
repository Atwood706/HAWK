"""
AWDL Standard Library - Web Fetch Tool

抓取指定 URL 的网页内容，提取纯文本供后续 Agent 分析。
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class WebFetchTool:
    """
    Web Fetch Tool - 网页抓取工具
    
    抓取指定 URL 的网页内容，提取纯文本。
    
    Inputs:
        url: 要抓取的网页地址
        
    Outputs:
        content: 网页的纯文本内容
        error: 错误信息（如果有）
    """
    
    timeout: int = 30
    max_length: int = 50000  # 最大返回字符数，避免内容过长
    
    def _html_to_text(self, html: str) -> str:
        """将 HTML 转换为纯文本"""
        # 移除 script 和 style 标签及其内容
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除 HTML 注释
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        
        # 将常见块级元素转换为换行
        html = re.sub(r'<(br|hr|p|div|li|tr|h[1-6])[^>]*/?>', '\n', html, flags=re.IGNORECASE)
        
        # 移除所有其他 HTML 标签
        html = re.sub(r'<[^>]+>', '', html)
        
        # 解码常见 HTML 实体
        html = html.replace('&nbsp;', ' ')
        html = html.replace('&lt;', '<')
        html = html.replace('&gt;', '>')
        html = html.replace('&amp;', '&')
        html = html.replace('&quot;', '"')
        html = html.replace('&#39;', "'")
        
        # 清理多余空白
        lines = []
        for line in html.split('\n'):
            line = ' '.join(line.split())  # 合并多个空格
            if line:
                lines.append(line)
        
        return '\n'.join(lines)
    
    def execute(
        self,
        url: str,
    ) -> Dict[str, Any]:
        """
        抓取指定 URL 的网页内容。
        
        Args:
            url: 网页地址
            
        Returns:
            Dictionary with 'content' and 'error' keys
        """
        try:
            import urllib.request
            import urllib.error
            
            # 验证 URL 格式
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # 设置请求头，模拟浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                # 检测编码
                content_type = response.headers.get('Content-Type', '')
                encoding = 'utf-8'
                if 'charset=' in content_type:
                    encoding = content_type.split('charset=')[-1].split(';')[0].strip()
                
                html = response.read().decode(encoding, errors='ignore')
            
            # 转换为纯文本
            text = self._html_to_text(html)
            
            # 限制长度
            if len(text) > self.max_length:
                text = text[:self.max_length] + "\n\n... [内容已截断]"
            
            if not text.strip():
                return {
                    "content": "",
                    "error": "网页内容为空或无法解析",
                }
            
            return {
                "content": text,
                "error": "",
            }
            
        except urllib.error.HTTPError as e:
            return {
                "content": "",
                "error": f"HTTP 错误 {e.code}: {e.reason}",
            }
        except urllib.error.URLError as e:
            return {
                "content": "",
                "error": f"无法访问网页: {e.reason}",
            }
        except Exception as e:
            return {
                "content": "",
                "error": f"抓取失败: {str(e)}",
            }
    
    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "WebFetchTool":
        """Create a web fetch tool with configuration."""
        config = config or {}
        return cls(
            timeout=config.get("timeout", 30),
            max_length=config.get("max_length", 50000),
        )


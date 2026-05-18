"""
AWDL Standard Library - Web Search Tool

This module provides the Web Search Tool implementation for AWDL workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
from urllib.request import Request, urlopen
import re


@dataclass
class WebSearchTool:
    """
    Web Search Tool.

    This tool searches the web for information related to a query.

    Inputs:
        query: The search query
        max_results: Maximum number of results to return

    Outputs:
        results: Search results as a formatted string
    """

    max_results: int = 10
    timeout: int = 10

    def execute(
        self,
        query: str,
        max_results: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute the web search.

        Args:
            query: The search query
            max_results: Maximum results to return

        Returns:
            Dictionary with 'results' key containing search results
        """
        if max_results is not None:
            try:
                max_results = int(max_results)
            except (ValueError, TypeError):
                max_results = self.max_results
        else:
            max_results = self.max_results

        try:
            html_text = self._fetch_html(query)
            items = self._parse_results(html_text, max_results=max_results)

            if not items:
                results_text = (
                    f"[Web Search Results for '{query}']\n"
                    "No results parsed from provider response.\n"
                )
            else:
                results_text = self._format_results(query, items)

            return {"results": results_text}
        except Exception as exc:
            return {
                "results": "",
                "error": f"web_search failed: {exc}",
            }

    def _fetch_html(self, query: str) -> str:
        """Fetch raw HTML from the search provider (DuckDuckGo HTML endpoint)."""
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        req = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (AWDL WebSearchTool)",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urlopen(req, timeout=self.timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")

    def _parse_results(self, html_text: str, max_results: int) -> List[Dict[str, str]]:
        """Parse search results from provider HTML."""
        results: List[Dict[str, str]] = []

        title_pattern = re.compile(
            r'class="result__a".*?href="(?P<url>[^"]+)".*?>(?P<title>.*?)</a>',
            re.S,
        )
        snippet_pattern = re.compile(
            r'class="result__snippet".*?>(?P<snippet>.*?)</',
            re.S,
        )

        for match in title_pattern.finditer(html_text):
            title = self._strip_tags(match.group("title"))
            url = self._normalize_url(match.group("url"))

            snippet_match = snippet_pattern.search(
                html_text, match.end(), match.end() + 1500
            )
            snippet = ""
            if snippet_match:
                snippet = self._strip_tags(snippet_match.group("snippet"))

            if title:
                results.append(
                    {
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                    }
                )
            if len(results) >= max_results:
                break

        return results

    def _format_results(self, query: str, items: List[Dict[str, str]]) -> str:
        """Format parsed items into a human-readable string."""
        lines = [f"[Web Search Results for '{query}']"]
        for idx, item in enumerate(items, 1):
            lines.append(f"{idx}. {item['title']}")
            lines.append(f"   {item['url']}")
            if item.get("snippet"):
                lines.append(f"   {item['snippet']}")
        return "\n".join(lines) + "\n"

    def _normalize_url(self, raw_url: str) -> str:
        """
        Normalize provider URLs:
        - Handle protocol-relative URLs (//example.com)
        - Remove whitespace/newlines inside href
        - Unwrap DuckDuckGo redirect links (/l/?uddg=...)
        """
        url = unescape(raw_url or "")
        url = re.sub(r"\s+", "", url)
        if url.startswith("//"):
            url = "https:" + url

        try:
            parsed = urlparse(url)
            if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
                qs = parse_qs(parsed.query)
                uddg = qs.get("uddg", [None])[0]
                if uddg:
                    return unquote(uddg)
        except Exception:
            pass

        return url

    def _strip_tags(self, text: str) -> str:
        """Remove HTML tags and normalize whitespace."""
        text = re.sub(r"<[^>]+>", "", text)
        text = unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "WebSearchTool":
        """
        Create a web search tool with configuration.

        Args:
            config: Optional configuration dictionary

        Returns:
            Configured WebSearchTool instance
        """
        config = config or {}
        return cls(
            max_results=config.get("max_results", 10),
            timeout=config.get("timeout", 10),
        )


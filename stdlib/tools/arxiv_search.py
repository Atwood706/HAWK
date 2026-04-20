"""
AWDL Standard Library - arXiv Search Tool

Search arXiv for recent papers on a given topic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import arxiv


@dataclass
class ArxivSearchTool:
    """
    Search arXiv for the latest papers related to a query.

    Inputs:
        query: The search topic
        max_results: Maximum number of papers to return

    Outputs:
        results: Formatted search results string
        error: Optional error message
    """

    default_max_results: int = 10

    def execute(
        self,
        query: str,
        max_results: Optional[int] = None,
    ) -> Dict[str, Any]:
        max_results = max_results if max_results is not None else self.default_max_results
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )

            papers = []
            for result in client.results(search):
                papers.append(
                    {
                        "title": result.title,
                        "authors": [a.name for a in result.authors],
                        "published": str(result.published),
                        "pdf_url": result.pdf_url,
                        "summary": result.summary,
                        "entry_id": result.entry_id,
                        "primary_category": result.primary_category,
                    }
                )

            if not papers:
                return {
                    "results": f"[arXiv Search for '{query}']\nNo recent papers found.\n",
                }

            lines = [f"[arXiv Search for '{query}']"]
            for idx, paper in enumerate(papers, 1):
                lines.append(f"{idx}. {paper['title']}")
                lines.append(f"   Authors: {', '.join(paper['authors'])}")
                lines.append(f"   Published: {paper['published']}")
                lines.append(f"   PDF: {paper['pdf_url']}")
                lines.append(f"   Summary: {paper['summary'][:300]}...")
                lines.append("")

            return {"results": "\n".join(lines)}
        except Exception as exc:
            return {
                "results": "",
                "error": f"arxiv_search failed: {exc}",
            }

    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "ArxivSearchTool":
        config = config or {}
        return cls(default_max_results=config.get("max_results", 10))

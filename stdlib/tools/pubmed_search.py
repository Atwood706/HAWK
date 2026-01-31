"""
AWDL Standard Library - PubMed Search Tool

更可靠的医学检索：使用 NCBI E-utilities (PubMed)。

Features
- PubMed 关键词检索（ESearch）
- 获取条目元信息（ESummary：标题/期刊/年份/作者/DOI 等）
- 可选抓取摘要（EFetch：AbstractText）

Notes
- NCBI 有访问频率限制；可选设置环境变量提升配额：
  - NCBI_API_KEY
  - NCBI_EMAIL（建议设置，符合 NCBI best practice）
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


@dataclass
class PubMedSearchTool:
    """
    PubMed Search Tool.

    Inputs:
        query: Search query (PubMed syntax supported)
        max_results: Max number of results (default 10)
        sort: PubMed sort ("relevance", "date", etc.)
        include_abstracts: Whether to fetch abstracts via EFetch (default False)
        mindate/maxdate: Optional date range (YYYY or YYYY/MM/DD)

    Outputs:
        results: Human-readable formatted string
        pmids: List of PMIDs (strings)
        error: Error message if failed
    """

    max_results: int = 10
    timeout: int = 15
    api_key: Optional[str] = None
    email: Optional[str] = None
    tool_tag: str = "AWDL PubMedSearchTool"
    throttle_seconds: float = 0.34  # ~3 req/sec; keep conservative by default

    _last_request_ts: float = 0.0

    def execute(
        self,
        query: str,
        max_results: Optional[int] = None,
        sort: str = "relevance",
        include_abstracts: bool = False,
        mindate: Optional[str] = None,
        maxdate: Optional[str] = None,
    ) -> Dict[str, Any]:
        max_results = int(max_results or self.max_results)
        max_results = max(1, min(max_results, 50))  # keep reasonable

        try:
            pmids = self._esearch(
                query=query,
                retmax=max_results,
                sort=sort,
                mindate=mindate,
                maxdate=maxdate,
            )
            if not pmids:
                return {
                    "results": f"[PubMed Results for '{query}']\nNo results.\n",
                    "pmids": [],
                    "error": "",
                }

            summaries = self._esummary(pmids)
            abstracts: Dict[str, str] = {}
            if include_abstracts:
                abstracts = self._efetch_abstracts(pmids)

            results_text = self._format_results(query, pmids, summaries, abstracts)
            return {
                "results": results_text,
                "pmids": pmids,
                "error": "",
            }
        except Exception as exc:
            return {
                "results": "",
                "pmids": [],
                "error": f"pubmed_search failed: {exc}",
            }

    def _throttle(self) -> None:
        now = time.time()
        wait = self.throttle_seconds - (now - self._last_request_ts)
        if wait > 0:
            time.sleep(wait)
        self._last_request_ts = time.time()

    def _http_get(self, url: str) -> bytes:
        self._throttle()
        req = Request(
            url,
            headers={
                "User-Agent": self.tool_tag,
                "Accept": "application/json, text/xml;q=0.9, */*;q=0.8",
            },
        )
        with urlopen(req, timeout=self.timeout) as resp:
            return resp.read()

    def _base_params(self) -> Dict[str, str]:
        api_key = self.api_key or os.getenv("NCBI_API_KEY") or ""
        email = self.email or os.getenv("NCBI_EMAIL") or ""
        params: Dict[str, str] = {}
        if api_key:
            params["api_key"] = api_key
        if email:
            params["email"] = email
        return params

    def _esearch(
        self,
        query: str,
        retmax: int,
        sort: str,
        mindate: Optional[str],
        maxdate: Optional[str],
    ) -> List[str]:
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params: Dict[str, str] = {
            "db": "pubmed",
            "term": query,
            "retmax": str(retmax),
            "sort": sort,
            "retmode": "json",
        }
        if mindate or maxdate:
            params["datetype"] = "pdat"
            if mindate:
                params["mindate"] = mindate
            if maxdate:
                params["maxdate"] = maxdate
        params.update(self._base_params())

        url = base + "?" + urlencode(params)
        raw = self._http_get(url).decode("utf-8", errors="ignore")
        data = json.loads(raw)
        idlist = data.get("esearchresult", {}).get("idlist", []) or []
        return [str(x) for x in idlist]

    def _esummary(self, pmids: List[str]) -> Dict[str, Dict[str, Any]]:
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params: Dict[str, str] = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        }
        params.update(self._base_params())
        url = base + "?" + urlencode(params)
        raw = self._http_get(url).decode("utf-8", errors="ignore")
        data = json.loads(raw)
        result = data.get("result", {}) or {}

        out: Dict[str, Dict[str, Any]] = {}
        for pmid in pmids:
            item = result.get(str(pmid), {}) or {}
            out[str(pmid)] = item
        return out

    def _efetch_abstracts(self, pmids: List[str]) -> Dict[str, str]:
        # EFetch XML returns article records; we extract AbstractText.
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params: Dict[str, str] = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }
        params.update(self._base_params())
        url = base + "?" + urlencode(params)
        xml_bytes = self._http_get(url)

        root = ET.fromstring(xml_bytes)
        abstracts: Dict[str, str] = {}

        # PubmedArticleSet/PubmedArticle/MedlineCitation/PMID
        for article in root.findall(".//PubmedArticle"):
            pmid_el = article.find(".//MedlineCitation/PMID")
            if pmid_el is None or not (pmid_el.text or "").strip():
                continue
            pmid = pmid_el.text.strip()

            parts: List[str] = []
            for abs_el in article.findall(".//Article/Abstract/AbstractText"):
                label = abs_el.attrib.get("Label")
                text = "".join(abs_el.itertext()).strip()
                if not text:
                    continue
                if label:
                    parts.append(f"{label}: {text}")
                else:
                    parts.append(text)
            abstracts[pmid] = "\n".join(parts).strip()

        # Ensure keys exist for all requested pmids (even if empty)
        for pmid in pmids:
            abstracts.setdefault(pmid, "")
        return abstracts

    def _format_results(
        self,
        query: str,
        pmids: List[str],
        summaries: Dict[str, Dict[str, Any]],
        abstracts: Dict[str, str],
    ) -> str:
        lines: List[str] = [f"[PubMed Results for '{query}']"]

        for idx, pmid in enumerate(pmids, 1):
            s = summaries.get(pmid, {}) or {}
            title = (s.get("title") or "").strip().rstrip(".")
            source = (s.get("source") or "").strip()
            pubdate = (s.get("pubdate") or "").strip()

            doi = ""
            for aid in s.get("articleids", []) or []:
                if (aid.get("idtype") == "doi") and aid.get("value"):
                    doi = str(aid["value"]).strip()
                    break

            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            lines.append(f"{idx}. {title or '(no title)'}")
            meta_bits = [f"PMID: {pmid}"]
            if source:
                meta_bits.append(source)
            if pubdate:
                meta_bits.append(pubdate)
            if doi:
                meta_bits.append(f"DOI: {doi}")
            lines.append("   " + " | ".join(meta_bits))
            lines.append(f"   {url}")

            abs_text = (abstracts.get(pmid) or "").strip()
            if abs_text:
                # Keep abstracts readable but not too long.
                if len(abs_text) > 1200:
                    abs_text = abs_text[:1200].rstrip() + "\n... [abstract truncated]"
                lines.append("   Abstract:")
                for ln in abs_text.splitlines():
                    lines.append(f"     {ln}")

        return "\n".join(lines) + "\n"

    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "PubMedSearchTool":
        config = config or {}
        return cls(
            max_results=int(config.get("max_results", 10)),
            timeout=int(config.get("timeout", 15)),
            api_key=config.get("api_key") or os.getenv("NCBI_API_KEY"),
            email=config.get("email") or os.getenv("NCBI_EMAIL"),
            tool_tag=config.get("tool_tag", "AWDL PubMedSearchTool"),
            throttle_seconds=float(config.get("throttle_seconds", 0.34)),
        )



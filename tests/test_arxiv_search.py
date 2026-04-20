"""
Tests for the ArxivSearchTool implementation.
"""

from stdlib.tools.arxiv_search import ArxivSearchTool


class FakeResult:
    def __init__(self, title, authors, published, pdf_url, summary, entry_id, primary_category):
        self.title = title
        self.authors = [type("Author", (), {"name": name}) for name in authors]
        self.published = published
        self.pdf_url = pdf_url
        self.summary = summary
        self.entry_id = entry_id
        self.primary_category = primary_category


class FakeClient:
    def __init__(self, results):
        self._results = results

    def results(self, search):
        return iter(self._results)


def test_arxiv_search_formats_results(monkeypatch):
    tool = ArxivSearchTool()

    fake_results = [
        FakeResult(
            title="Agentic Workflow Patterns",
            authors=["Alice Smith", "Bob Jones"],
            published="2025-01-10 00:00:00+00:00",
            pdf_url="https://arxiv.org/pdf/2501.01234",
            summary="We propose patterns for building agentic workflows.",
            entry_id="http://arxiv.org/abs/2501.01234",
            primary_category="cs.AI",
        ),
        FakeResult(
            title="LLM Tool Use Survey",
            authors=["Carol White"],
            published="2025-02-15 00:00:00+00:00",
            pdf_url="https://arxiv.org/pdf/2502.05678",
            summary="A comprehensive survey of tool use in large language models.",
            entry_id="http://arxiv.org/abs/2502.05678",
            primary_category="cs.CL",
        ),
    ]

    def fake_client_init(*args, **kwargs):
        return FakeClient(fake_results)

    monkeypatch.setattr("stdlib.tools.arxiv_search.arxiv.Client", fake_client_init)

    out = tool.execute("agentic workflows", max_results=2)
    assert out.get("error") is None
    text = out["results"]
    assert "[arXiv Search for 'agentic workflows']" in text
    assert "Agentic Workflow Patterns" in text
    assert "Alice Smith, Bob Jones" in text
    assert "https://arxiv.org/pdf/2501.01234" in text
    assert "LLM Tool Use Survey" in text
    assert "Carol White" in text


def test_arxiv_search_no_results(monkeypatch):
    tool = ArxivSearchTool()

    def fake_client_init(*args, **kwargs):
        return FakeClient([])

    monkeypatch.setattr("stdlib.tools.arxiv_search.arxiv.Client", fake_client_init)

    out = tool.execute("xyznonexistent12345", max_results=10)
    assert out.get("error") is None
    assert "No recent papers found" in out["results"]


def test_run_tool_arxiv_search_registered(monkeypatch):
    from stdlib.runtime import run_tool

    fake_results = [
        FakeResult(
            title="Test Paper",
            authors=["Test Author"],
            published="2025-01-01 00:00:00+00:00",
            pdf_url="https://arxiv.org/pdf/2501.00001",
            summary="Test summary.",
            entry_id="http://arxiv.org/abs/2501.00001",
            primary_category="cs.AI",
        ),
    ]

    def fake_client_init(*args, **kwargs):
        return FakeClient(fake_results)

    monkeypatch.setattr("stdlib.tools.arxiv_search.arxiv.Client", fake_client_init)

    result = run_tool("arxiv_search", {"query": "test", "max_results": 1})
    assert "[arXiv Search for 'test']" in result["results"]

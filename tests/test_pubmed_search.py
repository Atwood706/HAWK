"""
Tests for the PubMedSearchTool implementation.
"""

from stdlib.tools.pubmed_search import PubMedSearchTool


def test_pubmed_search_formats_results(monkeypatch):
    tool = PubMedSearchTool()

    monkeypatch.setattr(tool, "_esearch", lambda **kwargs: ["12345678", "23456789"])

    monkeypatch.setattr(
        tool,
        "_esummary",
        lambda pmids: {
            "12345678": {
                "title": "Test Title One.",
                "source": "Test Journal",
                "pubdate": "2020",
                "articleids": [{"idtype": "doi", "value": "10.1000/test.doi.1"}],
            },
            "23456789": {
                "title": "Test Title Two.",
                "source": "Another Journal",
                "pubdate": "2021",
                "articleids": [],
            },
        },
    )

    monkeypatch.setattr(
        tool,
        "_efetch_abstracts",
        lambda pmids: {
            "12345678": "This is an abstract.",
            "23456789": "",
        },
    )

    out = tool.execute("test query", max_results=2, include_abstracts=True)
    assert out["error"] == ""
    assert out["pmids"] == ["12345678", "23456789"]

    text = out["results"]
    assert "PubMed Results" in text
    assert "PMID: 12345678" in text
    assert "https://pubmed.ncbi.nlm.nih.gov/12345678/" in text
    assert "DOI: 10.1000/test.doi.1" in text
    assert "Abstract:" in text



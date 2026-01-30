"""
Tests for the WebSearchTool implementation.
"""

from stdlib.tools.web_search import WebSearchTool


def test_web_search_parsing(monkeypatch):
    html = """
    <html>
      <body>
        <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.python.org%2F&rut=abc">Python.org</a>
        <a class="result__snippet">The official home of the Python Programming Language.</a>
        <a class="result__a" href="https://docs.python.org/">Python Docs</a>
        <div class="result__snippet">Documentation for Python.</div>
      </body>
    </html>
    """
    tool = WebSearchTool()
    monkeypatch.setattr(tool, "_fetch_html", lambda query: html)

    result = tool.execute("python", max_results=2)

    assert "Python.org" in result["results"]
    assert "https://www.python.org/" in result["results"]
    assert "Python Docs" in result["results"]
    assert "https://docs.python.org/" in result["results"]


def test_web_search_empty_results(monkeypatch):
    tool = WebSearchTool()
    monkeypatch.setattr(tool, "_fetch_html", lambda query: "<html></html>")

    result = tool.execute("python", max_results=2)

    assert "No results parsed" in result["results"]


"""
Tests for the AWDL LangGraph Compiler.
"""

import pytest

from awdl.language.parser import parse_string
from awdl.compiler.langgraph import LangGraphCompiler


def test_compile_simple_workflow():
    """Test compiling a simple workflow."""
    source = """
__start__

string user_query: "Hello world"
string response

llm_agent: {
    prompt: user_query,
    response: response
}

__end__
    """
    
    workflow = parse_string(source)
    compiler = LangGraphCompiler(workflow)
    
    code = compiler.compile()
    
    # Check that generated code contains expected elements
    assert "class WorkflowState(TypedDict):" in code
    assert "user_query: str" in code
    assert "response: str" in code
    assert "StateGraph(WorkflowState)" in code
    assert "def llm_agent" in code


def test_compile_with_multiple_elements():
    """Test compiling a workflow with multiple elements."""
    source = """
__start__

string query: "test"
string search_results
string answer

web_search: {
    query: query,
    results: search_results
}

llm_agent: {
    context: search_results,
    prompt: query,
    response: answer
}

__end__
    """
    
    workflow = parse_string(source)
    compiler = LangGraphCompiler(workflow)
    
    code = compiler.compile()
    
    # Check that both nodes are present
    assert "def web_search" in code
    assert "def llm_agent" in code
    
    # Check that edges are present
    assert "add_edge" in code


def test_compile_with_condition():
    """Test compiling a workflow with conditions."""
    source = """
__start__

string query: "test"
string answer: ""

llm_agent: {
    prompt: query,
    response: answer
}

if answer == "":
{
    fallback_agent: {
        input: query,
        output: answer
    }
}

__end__
    """
    
    workflow = parse_string(source)
    compiler = LangGraphCompiler(workflow)
    
    code = compiler.compile()
    
    # Check that condition function is generated
    assert "def should_condition" in code


def test_graph_builder():
    """Test the graph builder."""
    source = """
__start__

string a: "input"
string b
string c

tool1: {
    input: a,
    results: b
}

tool2: {
    input: b,
    results: c
}

__end__
    """
    
    workflow = parse_string(source)
    compiler = LangGraphCompiler(workflow)
    
    # Get edges
    edges = compiler.graph_builder.build_edges()
    
    # Should have one edge from tool1 to tool2
    assert len(edges) == 1
    assert edges[0].source.startswith("tool1")
    assert edges[0].target.startswith("tool2")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


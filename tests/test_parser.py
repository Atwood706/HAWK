"""
Tests for the AWDL Parser.
"""

import pytest

from awdl.language.parser import parse_string
from awdl.language.lexer import Lexer
from awdl.ir.workflow import Workflow
from awdl.ir.elements import Agent, Tool
from awdl.ir.conditions import Condition


def test_lexer_basic():
    """Test basic lexer functionality."""
    source = """
    __start__
    string x: "hello"
    __end__
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    assert len(tokens) > 0
    assert tokens[-1].type.name == "EOF"


def test_parse_simple_workflow():
    """Test parsing a simple workflow."""
    source = """
import hawk.agents.llm

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
    
    assert isinstance(workflow, Workflow)
    assert len(workflow.imports) == 1
    assert len(workflow.variables) == 2
    assert len(workflow.elements) == 1
    
    # Check variable
    var = workflow.get_variable("user_query")
    assert var is not None
    assert var.default_value == "Hello world"
    
    # Check element
    element = workflow.elements[0]
    assert isinstance(element, Agent)
    assert element.agent_type == "llm_agent"


def test_parse_tool_invocation():
    """Test parsing a tool invocation."""
    source = """
__start__

string query: "test"
string results

web_search: {
    query: query,
    results: results
}

__end__
    """
    
    workflow = parse_string(source)
    
    assert len(workflow.elements) == 1
    element = workflow.elements[0]
    assert isinstance(element, Tool)
    assert element.tool_type == "web_search"


def test_parse_condition():
    """Test parsing an if statement."""
    source = """
__start__

string answer: ""

if answer == "":
{
    fallback_agent: {
        input: answer,
        output: answer
    }
}

__end__
    """
    
    workflow = parse_string(source)
    
    assert len(workflow.elements) == 1
    element = workflow.elements[0]
    assert isinstance(element, Condition)
    assert len(element.then_branch) == 1


def test_dependency_analyzer():
    """Test the dependency analyzer."""
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
    analyzer = workflow.get_dependency_analyzer()
    
    # Get execution order
    order = analyzer.get_execution_order()
    
    assert len(order) == 2
    
    # web_search should come before llm_agent (because llm reads search_results)
    assert order.ordered_elements[0].element_id.startswith("web_search")
    assert order.ordered_elements[1].element_id.startswith("llm_agent")


def test_workflow_validation():
    """Test workflow validation."""
    source = """
__start__

string x: "hello"

llm_agent: {
    prompt: undefined_var,
    response: x
}

__end__
    """
    
    workflow = parse_string(source)
    errors = workflow.validate()
    
    # Should have an error for undefined_var
    assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


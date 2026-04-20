"""
Tests for the AWDL parser and rebuilt DSL.
"""

import pytest

from awdl.ir.conditions import Condition
from awdl.ir.elements import Agent, Tool
from awdl.ir.workflow import Workflow
from awdl.language.errors import AWDLParseError
from awdl.language.lexer import Lexer
from awdl.language.parser import parse_string


def test_lexer_basic():
    source = """
    __start__
    string x: "hello"
    __end__
    """

    lexer = Lexer(source)
    tokens = lexer.tokenize()

    assert len(tokens) > 0
    assert tokens[-1].type.name == "EOF"


def test_parse_profiles_agent_and_subflow():
    source = """
profile coder {
    model: "test-model"
    max_turns: 3
    tools: ["file_read", "file_write"]
    skills: ["brainstorming"]
}

function prepare_text(input_path; final_text) {
    string raw

    file_read: {
        path: input_path,
        content: raw
    }

    text_concat: {
        left: raw,
        right: raw,
        result: final_text
    }
}

__start__

string path: "input.txt"
string prompt: "Summarize this"
string prepared
string answer

prepare_text: {
    input_path: path,
    final_text: prepared
}

agent: {
    profile: "coder",
    context: prepared,
    prompt: prompt,
    response: answer
}

__end__
    """

    workflow = parse_string(source)

    assert isinstance(workflow, Workflow)
    assert "coder" in workflow.profiles
    assert "prepare_text" in workflow.functions
    assert len(workflow.elements) == 2

    prepare_call = workflow.elements[0]
    agent_call = workflow.elements[1]

    assert prepare_call.element_id.startswith("prepare_text")
    assert prepare_call.function_name == "prepare_text"
    assert isinstance(agent_call, Agent)
    assert agent_call.agent_type == "agent"
    assert agent_call.config["profile"] == "coder"


def test_parse_tool_invocation():
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
    source = """
profile fallbacker {
    model: "test-model"
}

__start__

string answer: ""

if answer == "":
{
    agent: {
        profile: "fallbacker",
        prompt: answer,
        response: answer
    }
}

__end__
    """

    workflow = parse_string(source)

    assert len(workflow.elements) == 1
    element = workflow.elements[0]
    assert isinstance(element, Condition)
    assert len(element.then_branch) == 1


def test_dependency_analyzer_with_subflow_and_agent():
    source = """
profile coder {
    model: "test-model"
}

function preprocess(query; prepared) {
    text_concat: {
        left: query,
        right: query,
        result: prepared
    }
}

__start__

string query: "test"
string prepared
string answer

preprocess: {
    query: query,
    prepared: prepared
}

agent: {
    profile: "coder",
    context: prepared,
    prompt: query,
    response: answer
}

__end__
    """

    workflow = parse_string(source)
    order = workflow.get_dependency_analyzer().get_execution_order()

    assert len(order) == 2
    assert order.ordered_elements[0].element_id.startswith("preprocess")
    assert order.ordered_elements[1].element_id.startswith("agent")


def test_workflow_validation_reports_unknown_profile():
    source = """
__start__

string prompt: "hello"
string answer

agent: {
    profile: "missing",
    prompt: prompt,
    response: answer
}

__end__
    """

    workflow = parse_string(source)
    errors = workflow.validate()

    assert any("Unknown profile" in error.message for error in errors)


def test_legacy_agent_names_are_rejected():
    source = """
__start__

string prompt: "hello"
string answer

llm_agent: {
    prompt: prompt,
    response: answer
}

__end__
    """

    with pytest.raises(AWDLParseError):
        parse_string(source)


"""
Tests for the rebuilt AWDL LangGraph compiler.
"""

from awdl.compiler.langgraph import LangGraphCompiler
from awdl.language.parser import parse_string


def test_compile_workflow_with_unified_agent():
    source = """
profile coder {
    model: "test-model"
    max_turns: 2
    tools: ["file_read"]
}

__start__

string prompt: "Hello world"
string response

agent: {
    profile: "coder",
    prompt: prompt,
    response: response
}

__end__
    """

    workflow = parse_string(source)
    code = LangGraphCompiler(workflow).compile()

    assert "class WorkflowState(TypedDict):" in code
    assert "StateGraph(WorkflowState)" in code
    assert "run_agent(" in code
    assert '"coder"' in code


def test_compile_with_subflow_call():
    source = """
profile coder {
    model: "test-model"
}

function prepare_text(input_path; prepared) {
    string raw

    file_read: {
        path: input_path,
        content: raw
    }

    text_concat: {
        left: raw,
        right: raw,
        result: prepared
    }
}

__start__

string path: "input.txt"
string prompt: "test"
string prepared
string answer

prepare_text: {
    input_path: path,
    prepared: prepared
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
    code = LangGraphCompiler(workflow).compile()

    assert "def prepare_text_impl" in code
    assert "prepare_text_" in code
    assert "_node(state: WorkflowState)" in code
    assert "run_agent(" in code


def test_compile_rejects_unknown_profile():
    source = """
__start__

string prompt: "Hello world"
string response

agent: {
    profile: "missing",
    prompt: prompt,
    response: response
}

__end__
    """

    workflow = parse_string(source)
    errors = LangGraphCompiler(workflow).validate()

    assert any("Unknown profile" in error for error in errors)

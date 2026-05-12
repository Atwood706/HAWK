"""
Auto-generated LangGraph workflow from rebuilt AWDL.

Workflow: main
Version: 1.0
"""

from typing import Any, TypedDict
from pathlib import Path
from langgraph.graph import END, StateGraph
from stdlib.runtime import run_agent, run_tool

class WorkflowState(TypedDict):
    """Auto-generated state class for the workflow."""
    user_query: str
    prepared_query: str
    final_answer: str

WORKFLOW_DIR = 'D:\\HAWK\\examples'
INLINE_PROFILES = {'coder': {'model': 'deepseek-chat', 'max_turns': 4, 'tools': ['web_search', 'web_fetch']}}

initial_state = {
    "user_query": 'What is the weather today?',
    "prepared_query": "",
    "final_answer": "",
}

def prepare_query_impl(call_inputs: dict[str, Any]) -> dict[str, Any]:
    local_state: dict[str, Any] = {}
    local_state["user_query"] = call_inputs.get("user_query", "")
    local_state.setdefault("prepared_query", "")
    _result = run_tool("text_concat", {
        "left": local_state.get("user_query", ""),
        "right": local_state.get("user_query", ""),
    })
    local_state["prepared_query"] = _result.get("result", "")
    return {
        "prepared_query": local_state.get("prepared_query", ""),
    }

def prepare_query_2_node(state: WorkflowState) -> dict:
    call_inputs = {
        "user_query": state["user_query"],
    }
    result = prepare_query_impl(call_inputs)
    return {
        "prepared_query": result.get("prepared_query", ""),
    }

def agent_3_node(state: WorkflowState) -> dict:
    call_inputs = {
        "prompt": state["user_query"],
        "context": state["prepared_query"],
    }
    result = run_agent("coder", call_inputs, INLINE_PROFILES, WORKFLOW_DIR)
    return {
        "final_answer": result.get("response", ""),
    }

workflow = StateGraph(WorkflowState)

# Add nodes
workflow.add_node("prepare_query_2", prepare_query_2_node)
workflow.add_node("agent_3", agent_3_node)

# Add edges
workflow.add_edge("prepare_query_2", "agent_3")

workflow.set_entry_point("prepare_query_2")

app = workflow.compile()
"""
Tests for the rebuilt runtime helpers.
"""

from pathlib import Path

from stdlib.runtime import load_profile, run_agent, run_tool


def test_load_profile_prefers_inline_profile():
    profile = load_profile(
        "coder",
        inline_profiles={"coder": {"model": "inline-model", "max_turns": 2}},
        workflow_dir="/tmp/does-not-matter",
    )

    assert profile["model"] == "inline-model"


def test_run_tool_text_concat():
    result = run_tool("text_concat", {"left": "a", "right": "b", "sep": ":"})

    assert result["result"] == "a:b"


def test_run_agent_without_api_key_returns_controlled_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = run_agent(
        "coder",
        {"prompt": "hello"},
        inline_profiles={"coder": {"model": "test-model", "max_turns": 1}},
    )

    assert result["response"] == "hello"
    assert result["error"] == "missing_api_key"

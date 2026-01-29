"""
AWDL Standard Library - Runtime Registry

为编译产物提供统一的 agent/tool 获取方式，避免 codegen 写死大量 import 逻辑。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Callable

from stdlib.agents.llm import LLMAgent
from stdlib.agents.router import RouterAgent

from stdlib.tools.web_search import WebSearchTool
from stdlib.tools.file_io import FileReadTool, FileWriteTool


class _FallbackAgent:
    """最小兜底 agent：把 input 原样返回到 output。"""

    def execute(self, input: str) -> Dict[str, Any]:
        return {"output": input}

    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "_FallbackAgent":
        _ = config
        return cls()


class _TextConcatTool:
    """把两段文本拼接，输出到 result（用 result 作为输出口，兼容当前 parser 的输出端口判定）。"""

    def execute(self, left: str, right: str, sep: str = "\n\n") -> Dict[str, Any]:
        return {"result": f"{left}{sep}{right}"}

    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "_TextConcatTool":
        _ = config
        return cls()


_AGENT_FACTORIES: Dict[str, Callable[[Optional[Dict[str, Any]]], Any]] = {
    "llm_agent": LLMAgent.create,
    "router_agent": RouterAgent.create,
    "fallback_agent": _FallbackAgent.create,
}

_TOOL_FACTORIES: Dict[str, Callable[[Optional[Dict[str, Any]]], Any]] = {
    "web_search": WebSearchTool.create,
    "file_read": FileReadTool.create,
    "file_write": FileWriteTool.create,
    "text_concat": _TextConcatTool.create,
}

_AGENT_SINGLETONS: Dict[str, Any] = {}
_TOOL_SINGLETONS: Dict[str, Any] = {}


def get_agent(name: str, config: Optional[Dict[str, Any]] = None) -> Any:
    """按名称获取（单例）agent 实例。"""
    if name in _AGENT_SINGLETONS:
        return _AGENT_SINGLETONS[name]
    factory = _AGENT_FACTORIES.get(name)
    if not factory:
        raise KeyError(f"未知 agent：{name}")
    inst = factory(config)
    _AGENT_SINGLETONS[name] = inst
    return inst


def get_tool(name: str, config: Optional[Dict[str, Any]] = None) -> Any:
    """按名称获取（单例）tool 实例。"""
    if name in _TOOL_SINGLETONS:
        return _TOOL_SINGLETONS[name]
    factory = _TOOL_FACTORIES.get(name)
    if not factory:
        raise KeyError(f"未知 tool：{name}")
    inst = factory(config)
    _TOOL_SINGLETONS[name] = inst
    return inst



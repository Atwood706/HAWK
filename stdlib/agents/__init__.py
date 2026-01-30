"""
AWDL Standard Library - Built-in Agents
"""

from stdlib.agents.llm import DeepSeekAgent, LLMAgent
from stdlib.agents.qwen import QwenAgent
from stdlib.agents.router import RouterAgent

__all__ = [
    "DeepSeekAgent",
    "LLMAgent",  # backward-compatible alias
    "QwenAgent",
    "RouterAgent",
]


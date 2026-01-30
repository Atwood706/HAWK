"""
AWDL Standard Library - Qwen Agent

This module provides the Qwen LLM Agent implementation for AWDL workflows.
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class QwenAgent:
    """
    Qwen LLM Agent.

    Inputs:
        prompt: The main prompt/query to send to the LLM
        context: Optional context to provide to the LLM
        system_prompt: Optional system prompt to set behavior

    Outputs:
        response: The LLM's text response
    """

    model: str = "qwen-plus"
    temperature: float = 0.7
    max_tokens: int = 1024
    base_url: Optional[str] = None
    api_key: Optional[str] = None

    _client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        """
        获取（并缓存）底层 OpenAI 兼容客户端（通义千问）。

        - Qwen: base_url=https://dashscope.aliyuncs.com/compatible-mode/v1
        - api_key: 优先 QWEN_API_KEY，其次 DASHSCOPE_API_KEY
        """
        if self._client is not None:
            return self._client

        api_key = self.api_key or os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "未找到 API Key：请设置环境变量 QWEN_API_KEY 或 DASHSCOPE_API_KEY"
            )

        base_url = (
            self.base_url
            or os.getenv("QWEN_BASE_URL")
            or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        return self._client

    def execute(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the Qwen agent."""
        messages: List[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if context:
            prompt = f"上下文：\n{context}\n\n任务：\n{prompt}"

        messages.append({"role": "user", "content": prompt})

        client = self._get_client()
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        response = (resp.choices[0].message.content or "").strip()

        return {
            "response": response,
        }

    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "QwenAgent":
        """Create a Qwen agent with configuration."""
        config = config or {}
        return cls(
            model=config.get("model") or os.getenv("QWEN_MODEL") or "qwen-plus",
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 1024),
            base_url=config.get("base_url") or os.getenv("QWEN_BASE_URL"),
            api_key=config.get("api_key") or os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY"),
        )


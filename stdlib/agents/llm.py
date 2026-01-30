"""
AWDL Standard Library - DeepSeek Agent

This module provides the DeepSeek LLM Agent implementation for AWDL workflows.
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from openai import OpenAI

@dataclass
class DeepSeekAgent:
    """
    DeepSeek LLM Agent.
    
    This agent processes text inputs using a language model and produces
    text outputs.
    
    Inputs:
        prompt: The main prompt/query to send to the LLM
        context: Optional context to provide to the LLM
        system_prompt: Optional system prompt to set behavior
        
    Outputs:
        response: The LLM's text response
    """
    
    # DeepSeek 提供 OpenAI 兼容接口，默认模型用 deepseek-chat
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 1024
    base_url: Optional[str] = None
    api_key: Optional[str] = None

    _client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        """
        获取（并缓存）底层 OpenAI 兼容客户端（DeepSeek）。

        - DeepSeek: base_url=https://api.deepseek.com/v1（推荐）
        - api_key: 优先 DEEPSEEK_API_KEY，其次 OPENAI_API_KEY
        """
        if self._client is not None:
            return self._client

        api_key = self.api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "未找到 API Key：请设置环境变量 DEEPSEEK_API_KEY（推荐）或 OPENAI_API_KEY"
            )

        base_url = (
            self.base_url
            or os.getenv("DEEPSEEK_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or "https://api.deepseek.com/v1"
        )

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        return self._client
    
    def execute(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the LLM agent.
        
        Args:
            prompt: The main prompt to process
            context: Optional context information
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary with 'response' key containing the LLM output
        """
        messages: List[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if context:
            # 把 context 当作额外信息塞进用户侧消息，便于三段式工作流传递中间产物
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
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "DeepSeekAgent":
        """
        Create an LLM agent with configuration.
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            Configured LLMAgent instance
        """
        config = config or {}
        return cls(
            model=config.get("model") or os.getenv("DEEPSEEK_MODEL") or os.getenv("AWDL_LLM_MODEL") or "deepseek-chat",
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 1024),
            base_url=config.get("base_url") or os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
            api_key=config.get("api_key") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
        )


# Backward-compatible alias
LLMAgent = DeepSeekAgent


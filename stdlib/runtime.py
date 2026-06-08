"""
Runtime support for rebuilt AWDL.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

from openai import OpenAI
import httpx

from awdl.ir.builtins import BUILTIN_REGISTRY
from stdlib.tools.arxiv_search import ArxivSearchTool
from stdlib.tools.file_io import FileReadTool, FileWriteTool
from stdlib.tools.mcp_call import MCPCallTool
from stdlib.tools.web_fetch import WebFetchTool
from stdlib.tools.pubmed_search import PubMedSearchTool
from stdlib.tools.web_search import WebSearchTool
from stdlib.tools.echarts_render import EChartsRenderTool


class TextConcatTool:
    def execute(self, left: str, right: str, sep: str = "\n\n") -> Dict[str, Any]:
        return {"result": f"{left}{sep}{right}"}


class CodeSearchTool:
    def execute(self, query: str, root: str = ".") -> Dict[str, Any]:
        try:
            completed = subprocess.run(
                ["rg", "-n", query, root or "."],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            return {"results": "", "error": "rg is not installed"}

        return {
            "results": completed.stdout.strip(),
            "error": completed.stderr.strip() or "",
        }


class ShellTool:
    def execute(self, command: str, cwd: str = ".") -> Dict[str, Any]:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=cwd or ".",
            check=False,
            capture_output=True,
            text=True,
        )
        return {
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "exit_code": completed.returncode,
        }


class SkillDiscoveryTool:
    def execute(self, query: str = "") -> Dict[str, Any]:
        query_lower = query.lower().strip()
        results = []
        for path in _iter_skill_dirs():
            if query_lower and query_lower not in path.name.lower():
                continue
            results.append(str(path))
        return {"results": "\n".join(sorted(results))}


class SkillLoadTool:
    def execute(self, name: str) -> Dict[str, Any]:
        skill_path = _find_skill_path(name)
        if skill_path is None:
            return {"content": "", "error": f"Unknown skill: {name}"}
        return {"content": skill_path.read_text(encoding="utf-8")}


_TOOL_FACTORIES: Dict[str, Callable[[], Any]] = {
    "arxiv_search": ArxivSearchTool,
    "file_read": FileReadTool,
    "file_write": FileWriteTool,
    "text_concat": TextConcatTool,
    "web_search": WebSearchTool,
    "web_fetch": WebFetchTool,
    "pubmed_search": PubMedSearchTool,
    "mcp_call": MCPCallTool,
    "code_search": CodeSearchTool,
    "shell": ShellTool,
    "skill_discovery": SkillDiscoveryTool,
    "skill_load": SkillLoadTool,
    "render_echarts": EChartsRenderTool,
    # "med_risk_chart_option": MedicationRiskChartOptionTool,
}


def run_tool(name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    factory = _TOOL_FACTORIES.get(name)
    if factory is None:
        raise KeyError(f"Unknown tool: {name}")
    tool = factory()
    return tool.execute(**inputs)


def load_profile(
    name: str,
    inline_profiles: Optional[Dict[str, Dict[str, Any]]] = None,
    workflow_dir: Optional[str] = None,
) -> Dict[str, Any]:
    if inline_profiles and name in inline_profiles:
        return dict(inline_profiles[name])

    search_paths = []
    if workflow_dir:
        search_paths.append(Path(workflow_dir) / "profiles" / f"{name}.toml")
    search_paths.append(Path.home() / ".awdl" / "profiles" / f"{name}.toml")

    for path in search_paths:
        if not path.exists():
            continue
        if tomllib is None:
            raise RuntimeError("tomllib is required to load external profiles")
        with path.open("rb") as handle:
            return tomllib.load(handle)

    raise KeyError(f"Unknown profile: {name}")


@dataclass
class AgentRuntime:
    profile: Dict[str, Any]
    skills: Optional[list[str]] = None
    tools: Optional[list[str]] = None

    def __post_init__(self) -> None:
        provider = str(self.profile.get("provider") or "").strip().lower()
        api_key = self.profile.get("api_key") or _provider_api_key(provider)
        if not api_key:
            self.client = None
            self.anthropic_api_key = None
            return

        self.anthropic_api_key = api_key if provider == "anthropic" else None
        if provider == "anthropic":
            self.client = None
            return

        base_url = self.profile.get("base_url") or _provider_base_url(provider)
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        prompt = str(inputs.get("prompt", ""))
        context = str(inputs.get("context", ""))
        invocation_system = str(inputs.get("system_prompt", "")).strip()

        system_sections = []
        if self.profile.get("system_prompt"):
            system_sections.append(str(self.profile["system_prompt"]))
        skill_names = self.skills if self.skills is not None else self.profile.get("skills", [])
        loaded_skills = _load_skill_contents(skill_names)
        system_sections.extend(loaded_skills)
        if invocation_system:
            system_sections.append(invocation_system)

        user_content = prompt if not context else f"Context:\n{context}\n\nTask:\n{prompt}"
        messages: list[dict[str, Any]] = []
        if system_sections:
            messages.append({"role": "system", "content": "\n\n".join(system_sections)})
        messages.append({"role": "user", "content": user_content})

        tool_names = list(self.tools if self.tools is not None else (self.profile.get("tools", []) or []))
        tool_specs = [_tool_schema(tool_name) for tool_name in tool_names]
        trace: list[dict[str, Any]] = [
            {
                "event": "agent.setup",
                "model": self.profile.get("model") or os.getenv("AWDL_AGENT_MODEL") or "deepseek-chat",
                "max_turns": int(self.profile.get("max_turns", 6)),
                "temperature": float(self.profile.get("temperature", 0.2)),
                "skill_count": len(loaded_skills),
                "tool_names": tool_names,
                "messages": messages,
            }
        ]

        if self.client is None:
            if self.anthropic_api_key:
                return self._execute_anthropic(messages, tool_names, trace)
            trace.append({"event": "agent.error", "reason": "missing_api_key"})
            return {"response": prompt if not context else context, "trace": trace, "error": "missing_api_key"}

        model = self.profile.get("model") or os.getenv("AWDL_AGENT_MODEL") or "deepseek-chat"
        max_turns = int(self.profile.get("max_turns", 6))
        temperature = float(self.profile.get("temperature", 0.2))
        last_text = ""

        for turn in range(max_turns):
            trace.append({"event": "agent.llm_request", "turn": turn + 1, "model": model, "message_count": len(messages)})
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tool_specs or None,
                    tool_choice="auto" if tool_specs else None,
                    temperature=temperature,
                    timeout=30,
                )
            except Exception as exc:
                trace.append({"event": "agent.llm_error", "turn": turn + 1, "error": str(exc)})
                return {"response": last_text, "trace": trace, "error": f"llm_error: {exc}"}

            message = response.choices[0].message
            last_text = (message.content or "").strip()
            trace.append({"event": "agent.llm_response", "turn": turn + 1, "content": last_text})

            assistant_message: dict[str, Any] = {"role": "assistant", "content": message.content or ""}
            raw_tool_calls = getattr(message, "tool_calls", None)
            if raw_tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in raw_tool_calls
                ]
            messages.append(assistant_message)

            if not raw_tool_calls:
                trace.append({"event": "agent.finish", "reason": "no_tool_calls"})
                return {"response": last_text, "trace": trace}

            for tool_call in raw_tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError as exc:
                    trace.append({"event": "agent.tool_error", "turn": turn + 1, "tool": tool_call.function.name, "error": f"invalid_json: {exc}"})
                    return {"response": last_text, "trace": trace, "error": f"tool_json_error: {exc}"}

                trace.append({"event": "agent.tool_call", "turn": turn + 1, "tool": tool_call.function.name, "arguments": arguments})
                try:
                    tool_result = run_tool(tool_call.function.name, arguments)
                except Exception as exc:
                    trace.append({"event": "agent.tool_error", "turn": turn + 1, "tool": tool_call.function.name, "error": str(exc)})
                    return {"response": last_text, "trace": trace, "error": f"tool_execution_error: {exc}"}

                trace.append({"event": "agent.tool_result", "turn": turn + 1, "tool": tool_call.function.name, "result": tool_result})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                    }
                )

        trace.append({"event": "agent.error", "reason": "max_turns_reached"})
        return {
            "response": last_text,
            "trace": trace,
            "error": "max_turns_reached",
        }

    def _execute_anthropic(
        self,
        messages: list[dict[str, Any]],
        tool_names: list[str],
        trace: list[dict[str, Any]],
    ) -> Dict[str, Any]:
        if tool_names:
            trace.append(
                {
                    "event": "agent.warning",
                    "reason": "anthropic_adapter_does_not_support_tools_yet",
                    "tool_names": tool_names,
                }
            )

        system_content = "\n\n".join(
            str(message.get("content", ""))
            for message in messages
            if message.get("role") == "system"
        ).strip()
        anthropic_messages = [
            {
                "role": "assistant" if message.get("role") == "assistant" else "user",
                "content": str(message.get("content", "")),
            }
            for message in messages
            if message.get("role") != "system"
        ]
        payload: dict[str, Any] = {
            "model": self.profile.get("model") or "claude-sonnet-4-5-20250929",
            "messages": anthropic_messages,
            "max_tokens": int(self.profile.get("max_tokens", 1024)),
            "temperature": float(self.profile.get("temperature", 0.2)),
        }
        if system_content:
            payload["system"] = system_content

        base_url = str(self.profile.get("base_url") or _provider_base_url("anthropic") or "https://api.anthropic.com").rstrip("/")
        trace.append(
            {
                "event": "agent.anthropic_request",
                "model": payload["model"],
                "message_count": len(anthropic_messages),
            }
        )
        try:
            response = httpx.post(
                f"{base_url}/v1/messages",
                headers={
                    "x-api-key": str(self.anthropic_api_key),
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            trace.append({"event": "agent.anthropic_error", "error": str(exc)})
            return {"response": "", "trace": trace, "error": f"anthropic_error: {exc}"}

        text_parts = [
            str(block.get("text", ""))
            for block in data.get("content", [])
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        response_text = "\n".join(part for part in text_parts if part).strip()
        trace.append({"event": "agent.anthropic_response", "content": response_text})
        return {"response": response_text, "trace": trace}


def run_agent(
    profile_name: str,
    inputs: Dict[str, Any],
    inline_profiles: Optional[Dict[str, Dict[str, Any]]] = None,
    workflow_dir: Optional[str] = None,
    skills: Optional[list[str]] = None,
    tools: Optional[list[str]] = None,
) -> Dict[str, Any]:
    profile = load_profile(profile_name, inline_profiles=inline_profiles, workflow_dir=workflow_dir)
    runtime = AgentRuntime(profile, skills=skills, tools=tools)
    return runtime.execute(inputs)


def _provider_api_key(provider: str) -> str | None:
    env_by_provider = {
        "openrouter": ("OPENROUTER_API_KEY",),
        "openai": ("OPENAI_API_KEY",),
        "deepseek": ("DEEPSEEK_API_KEY", "OPENAI_API_KEY"),
        "qwen": ("QWEN_API_KEY", "DASHSCOPE_API_KEY"),
        "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "anthropic": ("ANTHROPIC_API_KEY",),
        "xai": ("XAI_API_KEY",),
        "groq": ("GROQ_API_KEY",),
        "mistral": ("MISTRAL_API_KEY",),
        "perplexity": ("PERPLEXITY_API_KEY",),
        "moonshot": ("MOONSHOT_API_KEY", "KIMI_API_KEY"),
        "zhipu": ("ZHIPU_API_KEY", "BIGMODEL_API_KEY"),
        "siliconflow": ("SILICONFLOW_API_KEY",),
        "together": ("TOGETHER_API_KEY",),
    }
    env_names = env_by_provider.get(provider, ("OPENAI_API_KEY", "DEEPSEEK_API_KEY"))
    for env_name in env_names:
        value = os.getenv(env_name)
        if value:
            return value
    return None


def _provider_base_url(provider: str) -> str | None:
    base_url_by_provider = {
        "openrouter": os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
        "openai": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "deepseek": os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com",
        "qwen": os.getenv("QWEN_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "gemini": os.getenv("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/",
        "anthropic": os.getenv("ANTHROPIC_BASE_URL") or "https://api.anthropic.com",
        "xai": os.getenv("XAI_BASE_URL") or "https://api.x.ai/v1",
        "groq": os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1",
        "mistral": os.getenv("MISTRAL_BASE_URL") or "https://api.mistral.ai/v1",
        "perplexity": os.getenv("PERPLEXITY_BASE_URL") or "https://api.perplexity.ai",
        "moonshot": os.getenv("MOONSHOT_BASE_URL") or "https://api.moonshot.cn/v1",
        "zhipu": os.getenv("ZHIPU_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4",
        "siliconflow": os.getenv("SILICONFLOW_BASE_URL") or "https://api.siliconflow.cn/v1",
        "together": os.getenv("TOGETHER_BASE_URL") or "https://api.together.xyz/v1",
    }
    return base_url_by_provider.get(provider) or os.getenv("OPENAI_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL")


def _tool_schema(name: str) -> Dict[str, Any]:
    definition = BUILTIN_REGISTRY.get(name)
    if definition is None:
        raise KeyError(f"Unknown tool: {name}")

    properties: Dict[str, Any] = {}
    required: list[str] = []
    for port in definition.inputs:
        properties[port.name] = {
            "type": _json_type_for_port(port.port_type),
            "description": port.description or port.name,
        }
        if port.required:
            required.append(port.name)

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": definition.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def _json_type_for_port(port_type: str) -> str:
    return {
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "list": "array",
    }.get(port_type, "string")


def _iter_skill_dirs() -> list[Path]:
    roots = [
        Path.home() / ".codex" / "skills",
        Path.home() / ".codex" / "superpowers" / "skills",
        Path(__file__).resolve().parents[1] / "skills",
    ]
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for skill_file in root.glob("**/SKILL.md"):
            paths.append(skill_file)
    return paths


def _find_skill_path(name: str) -> Optional[Path]:
    normalized = name.strip().lower()
    for path in _iter_skill_dirs():
        if path.parent.name.lower() == normalized:
            return path
    return None


def _load_skill_contents(skill_names: list[str]) -> list[str]:
    contents: list[str] = []
    for skill_name in skill_names or []:
        path = _find_skill_path(skill_name)
        if path is None:
            continue
        contents.append(path.read_text(encoding="utf-8"))
    return contents

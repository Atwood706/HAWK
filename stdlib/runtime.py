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
        api_key = (
            self.profile.get("api_key")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
        )
        if not api_key:
            self.client = None
            return

        base_url = (
            self.profile.get("base_url")
            or os.getenv("OPENAI_BASE_URL")
            or os.getenv("DEEPSEEK_BASE_URL")
        )
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

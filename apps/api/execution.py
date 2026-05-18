from __future__ import annotations

import traceback
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

from apps.api.awdl_bridge import _order_nodes, graph_to_awdl
from apps.api.seed import ensure_seed_data
from apps.api.storage import FileStore
from apps.api.workflow_graph import WorkflowGraph
from stdlib import runtime


def _apply_medical_skill_to_agent_inputs(node_inputs: dict[str, Any], medical_skill: dict[str, str] | None) -> dict[str, Any]:
    if not medical_skill:
        return node_inputs

    prompt = str(node_inputs.get("prompt", ""))
    skill_context = "\n".join(
        [
            "Use the following OpenClaw medical skill as guidance for this agent task:",
            f"Skill: {medical_skill.get('name', '')}",
            f"Domain: {medical_skill.get('category', '')}",
            f"Description: {medical_skill.get('description', '')}",
        ]
    )
    return {**node_inputs, "prompt": f"{skill_context}\n\nTask:\n{prompt}".strip()}


def execute_workflow_graph(
    workflow_id: str,
    run_input: dict[str, Any],
    *,
    store: FileStore,
) -> tuple[str, str, dict[str, Any], list[dict[str, Any]]]:
    trace: list[dict[str, Any]] = [{"event": "run.started", "workflow_id": workflow_id}]
    try:
        ensure_seed_data(store)
        trace.append({"event": "seed_data.ensured"})

        graph_payload = store.load_workflow(workflow_id)
        trace.append({"event": "workflow.loaded", "workflow_id": workflow_id})

        graph = WorkflowGraph.model_validate(graph_payload)
        trace.append({"event": "graph.validated", "node_count": len(graph.nodes), "edge_count": len(graph.edges)})

        settings = store.load_settings()
        trace.append({"event": "settings.loaded"})

        inline_profiles = _load_inline_profiles(store)
        trace.append({"event": "profiles.loaded", "profile_names": list(inline_profiles.keys())})

        inline_profiles.update(graph.profiles)
        if graph.profiles:
            trace.append({"event": "profiles.merged", "inline_names": list(graph.profiles.keys())})

        _inject_provider_api_keys(inline_profiles, settings)
        trace.append({"event": "api_keys.injected"})

        variables: dict[str, Any] = {variable.name: variable.value for variable in graph.variables}
        variables.update(run_input)
        trace.append({"event": "variables.initialized", "names": list(variables.keys())})

        awdl = graph_to_awdl(graph_payload)
        trace.append({"event": "awdl.generated", "length": len(awdl)})

        status = "succeeded"
        result: dict[str, Any] = {}

        for node in _order_nodes(graph.nodes, graph.edges):
            node_inputs = {key: variables.get(value, value) for key, value in node.data.inputs.items()}
            profile_name = node.data.profile or ""
            tool_name = node.data.tool_name or ""

            if node.type == "tool":
                trace.append(
                    {
                        "event": "node.started",
                        "node_id": node.id,
                        "tool_name": tool_name,
                        "inputs": node_inputs,
                    }
                )
                tool_result = runtime.run_tool(tool_name, node_inputs)

                for output_name, variable_name in node.data.outputs.items():
                    variables[variable_name] = tool_result.get(output_name)
                    result[variable_name] = tool_result.get(output_name)

                if tool_result.get("error"):
                    status = "failed"

                trace.append(
                    {
                        "event": "node.completed",
                        "node_id": node.id,
                        "tool_name": tool_name,
                        "error": tool_result.get("error"),
                        "outputs": result.copy(),
                    }
                )
                trace.append(
                    {
                        "event": "tool.trace",
                        "node_id": node.id,
                        "data": tool_result,
                    }
                )
            else:
                node_inputs = _apply_medical_skill_to_agent_inputs(node_inputs, node.data.medical_skill)
                trace.append(
                    {
                        "event": "node.started",
                        "node_id": node.id,
                        "profile": profile_name,
                        "medical_skill": node.data.medical_skill,
                        "inputs": node_inputs,
                    }
                )
                agent_result = runtime.run_agent(
                    profile_name,
                    node_inputs,
                    inline_profiles=inline_profiles,
                )

                for output_name, variable_name in node.data.outputs.items():
                    variables[variable_name] = agent_result.get(output_name)
                    result[variable_name] = agent_result.get(output_name)

                if agent_result.get("error"):
                    status = "failed"

                trace.append(
                    {
                        "event": "node.completed",
                        "node_id": node.id,
                        "profile": profile_name,
                        "error": agent_result.get("error"),
                        "outputs": result.copy(),
                    }
                )
                for event in agent_result.get("trace", []):
                    trace.append({"event": "agent.trace", "node_id": node.id, "data": event})

        if status == "failed":
            result["error"] = "agent_execution_failed"
            trace.append({"event": "run.failed", "workflow_id": workflow_id})
        else:
            trace.append({"event": "run.succeeded", "workflow_id": workflow_id})

        return status, awdl, result, trace
    except Exception as exc:
        error_message = str(exc)
        stack_trace = traceback.format_exc()
        trace.append(
            {
                "event": "run.failed",
                "workflow_id": workflow_id,
                "error": error_message,
                "traceback": stack_trace,
            }
        )
        return "failed", "", {"error": error_message}, trace


def _load_inline_profiles(store: FileStore) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for profile_name in store.list_profiles():
        content = store.load_profile(profile_name)
        profiles[profile_name] = tomllib.loads(content)
    return profiles


def _inject_provider_api_keys(
    profiles: dict[str, dict[str, Any]],
    settings: dict[str, Any],
) -> None:
    keys_by_provider = {
        "openrouter": settings.get("openrouter_api_key"),
        "openai": settings.get("openai_api_key"),
        "deepseek": settings.get("deepseek_api_key"),
        "qwen": settings.get("qwen_api_key"),
        "gemini": settings.get("gemini_api_key"),
        "anthropic": settings.get("anthropic_api_key"),
        "xai": settings.get("xai_api_key"),
        "groq": settings.get("groq_api_key"),
        "mistral": settings.get("mistral_api_key"),
        "perplexity": settings.get("perplexity_api_key"),
        "moonshot": settings.get("moonshot_api_key"),
        "zhipu": settings.get("zhipu_api_key"),
        "siliconflow": settings.get("siliconflow_api_key"),
        "together": settings.get("together_api_key"),
    }
    provider_by_base_url = {
        "https://openrouter.ai/api/v1": "openrouter",
        "https://api.openai.com/v1": "openai",
        "https://api.deepseek.com": "deepseek",
        "https://dashscope.aliyuncs.com/compatible-mode/v1": "qwen",
        "https://generativelanguage.googleapis.com/v1beta/openai": "gemini",
        "https://api.anthropic.com": "anthropic",
        "https://api.x.ai/v1": "xai",
        "https://api.groq.com/openai/v1": "groq",
        "https://api.mistral.ai/v1": "mistral",
        "https://api.perplexity.ai": "perplexity",
        "https://api.moonshot.cn/v1": "moonshot",
        "https://open.bigmodel.cn/api/paas/v4": "zhipu",
        "https://api.siliconflow.cn/v1": "siliconflow",
        "https://api.together.xyz/v1": "together",
    }

    for profile in profiles.values():
        if profile.get("api_key"):
            continue

        provider = str(profile.get("provider") or "").strip().lower()
        if not provider:
            base_url = str(profile.get("base_url", "")).rstrip("/")
            provider = provider_by_base_url.get(base_url, "")

        api_key = keys_by_provider.get(provider)
        if api_key:
            profile["api_key"] = api_key

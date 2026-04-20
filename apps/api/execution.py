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

        _inject_openrouter_api_key(inline_profiles, settings.get("openrouter_api_key"))
        trace.append({"event": "api_key.injected"})

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
                trace.append(
                    {
                        "event": "node.started",
                        "node_id": node.id,
                        "profile": profile_name,
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


def _inject_openrouter_api_key(
    profiles: dict[str, dict[str, Any]],
    openrouter_api_key: str | None,
) -> None:
    if not openrouter_api_key:
        return

    for profile in profiles.values():
        if profile.get("api_key"):
            continue
        base_url = str(profile.get("base_url", "")).rstrip("/")
        if base_url == "https://openrouter.ai/api/v1":
            profile["api_key"] = openrouter_api_key

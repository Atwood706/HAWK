from __future__ import annotations

import json
from collections import defaultdict
from heapq import heapify, heappop, heappush
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from awdl.language.errors import AWDLError
from awdl.language.parser import parse_string

from apps.api.workflow_graph import WorkflowEdge, WorkflowGraph, WorkflowNode


SUPPORTED_NODE_TYPES = {"agent", "tool"}


def _render_scalar(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(_render_scalar(item) for item in value) + "]"
    return str(value)

def _render_profile(name: str, config: dict[str, Any]) -> list[str]:
    lines = [f"profile {name} {{"]
    for key, value in config.items():
        lines.append(f"    {key}: {_render_scalar(value)}")
    lines.append("}")
    return lines

def _render_node(node: WorkflowNode) -> list[str]:
    if node.type not in SUPPORTED_NODE_TYPES:
        raise ValueError(f"unsupported node type: {node.type}")

    block_name = node.type
    if node.type == "tool":
        block_name = node.data.tool_name or "tool"

    lines = [f"{block_name}: {{"]
    if node.type == "agent" and node.data.profile:
        lines.append(f'    profile: {_render_scalar(node.data.profile)}')
    for key, value in node.data.inputs.items():
        lines.append(f"    {key}: {value}")
    for key, value in node.data.outputs.items():
        lines.append(f"    {key}: {value}")
    lines.append("}")
    return lines


def _order_nodes(nodes: list[WorkflowNode], edges: list[WorkflowEdge]) -> list[WorkflowNode]:
    if not edges:
        return nodes

    nodes_by_id = {node.id: node for node in nodes}
    adjacency: dict[str, list[str]] = defaultdict(list)
    indegree = {node.id: 0 for node in nodes}
    node_positions = {node.id: index for index, node in enumerate(nodes)}

    for edge in edges:
        if edge.source not in nodes_by_id or edge.target not in nodes_by_id:
            raise ValueError("edge references unknown node")
        adjacency[edge.source].append(edge.target)
        indegree[edge.target] += 1

    ready = [(node_positions[node_id], node_id) for node_id, degree in indegree.items() if degree == 0]
    heapify(ready)
    ordered_ids: list[str] = []

    while ready:
        _, node_id = heappop(ready)
        ordered_ids.append(node_id)
        for target_id in adjacency[node_id]:
            indegree[target_id] -= 1
            if indegree[target_id] == 0:
                heappush(ready, (node_positions[target_id], target_id))

    if len(ordered_ids) != len(nodes):
        raise ValueError("graph edges do not produce a valid node order")

    return [nodes_by_id[node_id] for node_id in ordered_ids]

def graph_to_awdl(graph: dict[str, Any]) -> str:
    workflow_graph = WorkflowGraph.model_validate(graph)
    lines: list[str] = []

    for profile_name, profile_config in workflow_graph.profiles.items():
        lines.extend(_render_profile(profile_name, profile_config))
        lines.append("")

    lines.extend(["__start__", ""])

    for variable in workflow_graph.variables:
        line = f"{variable.type} {variable.name}"
        if variable.value is not None:
            line += f": {_render_scalar(variable.value)}"
        lines.append(line)

    if workflow_graph.variables:
        lines.append("")

    for node in _order_nodes(workflow_graph.nodes, workflow_graph.edges):
        lines.extend(_render_node(node))
        lines.append("")

    lines.append("__end__")
    return "\n".join(lines)

def validate_graph(graph: dict[str, Any]) -> list[str]:
    try:
        source = graph_to_awdl(graph)
        workflow = parse_string(source)
    except (AWDLError, PydanticValidationError, ValueError) as exc:
        return [str(exc)]

    return [error.message for error in workflow.validate()]

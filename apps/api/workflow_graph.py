from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WorkflowVariable(BaseModel):
    name: str
    type: str
    value: str | None = None


class WorkflowNodeData(BaseModel):
    label: str | None = None
    profile: str | None = None
    tool_name: str | None = None
    function_name: str | None = None
    medical_skill: dict[str, str] | None = None
    inputs: dict[str, str] = Field(default_factory=dict)
    outputs: dict[str, str] = Field(default_factory=dict)


class WorkflowNode(BaseModel):
    id: str
    type: str
    data: WorkflowNodeData


class WorkflowEdge(BaseModel):
    source: str
    target: str


class WorkflowGraph(BaseModel):
    id: str
    name: str
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    variables: list[WorkflowVariable] = Field(default_factory=list)
    profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.awdl_bridge import graph_to_awdl, validate_graph
from apps.api.main import app
from apps.api.routes import workflows as workflows_route
from apps.api.storage import FileStore


SIMPLE_AGENT_GRAPH = {
    "id": "demo",
    "name": "Demo",
    "nodes": [
        {
            "id": "node_1",
            "type": "agent",
            "data": {
                "profile": "coder",
                "inputs": {"prompt": "prompt_text"},
                "outputs": {"response": "final_answer"},
            },
        }
    ],
    "edges": [],
    "variables": [
        {"name": "prompt_text", "type": "string", "value": "hello"},
        {"name": "final_answer", "type": "string"},
    ],
    "profiles": {
        "coder": {
            "model": "test-model",
            "max_turns": 2,
        }
    },
}


def test_graph_to_awdl_renders_agent_workflow():
    awdl = graph_to_awdl(SIMPLE_AGENT_GRAPH)

    assert 'profile coder {' in awdl
    assert 'model: "test-model"' in awdl
    assert '__start__' in awdl
    assert 'string prompt_text: "hello"' in awdl
    assert 'string final_answer' in awdl
    assert 'agent: {' in awdl
    assert 'profile: "coder"' in awdl
    assert 'prompt: prompt_text' in awdl
    assert 'response: final_answer' in awdl
    assert awdl.strip().endswith('__end__')


def test_validate_graph_accepts_simple_agent_workflow():
    assert validate_graph(SIMPLE_AGENT_GRAPH) == []


def test_graph_to_awdl_orders_nodes_from_edges():
    graph = {
        **SIMPLE_AGENT_GRAPH,
        "nodes": [
            {
                "id": "node_2",
                "type": "agent",
                "data": {
                    "profile": "coder",
                    "inputs": {"prompt": "final_answer"},
                    "outputs": {"response": "second_answer"},
                },
            },
            SIMPLE_AGENT_GRAPH["nodes"][0],
        ],
        "edges": [{"source": "node_1", "target": "node_2"}],
        "variables": [
            {"name": "prompt_text", "type": "string", "value": "hello"},
            {"name": "final_answer", "type": "string"},
            {"name": "second_answer", "type": "string"},
        ],
    }

    awdl = graph_to_awdl(graph)

    assert awdl.index("prompt: prompt_text") < awdl.index("prompt: final_answer")


def test_graph_to_awdl_rejects_edges_with_unknown_nodes():
    graph = {
        **SIMPLE_AGENT_GRAPH,
        "edges": [{"source": "missing", "target": "node_1"}],
    }

    with pytest.raises(ValueError, match="unknown node"):
        graph_to_awdl(graph)


def test_graph_to_awdl_rejects_cyclic_edges():
    graph = {
        **SIMPLE_AGENT_GRAPH,
        "nodes": [
            SIMPLE_AGENT_GRAPH["nodes"][0],
            {
                "id": "node_2",
                "type": "agent",
                "data": {
                    "profile": "coder",
                    "inputs": {"prompt": "final_answer"},
                    "outputs": {"response": "second_answer"},
                },
            },
        ],
        "edges": [
            {"source": "node_1", "target": "node_2"},
            {"source": "node_2", "target": "node_1"},
        ],
        "variables": [
            {"name": "prompt_text", "type": "string", "value": "hello"},
            {"name": "final_answer", "type": "string"},
            {"name": "second_answer", "type": "string"},
        ],
    }

    with pytest.raises(ValueError, match="valid node order"):
        graph_to_awdl(graph)


def test_validate_route_reports_valid_graph(tmp_path: Path, monkeypatch):
    store = FileStore(tmp_path)
    store.save_workflow("demo", SIMPLE_AGENT_GRAPH)
    monkeypatch.setattr(workflows_route, "STORE", store)
    client = TestClient(app)

    response = client.post("/api/workflows/demo/validate")

    assert response.status_code == 200
    assert response.json() == {"valid": True, "errors": []}


def test_export_awdl_route_returns_rendered_source(tmp_path: Path, monkeypatch):
    store = FileStore(tmp_path)
    store.save_workflow("demo", SIMPLE_AGENT_GRAPH)
    monkeypatch.setattr(workflows_route, "STORE", store)
    client = TestClient(app)

    response = client.post("/api/workflows/demo/export-awdl")

    assert response.status_code == 200
    assert response.json() == {"awdl": graph_to_awdl(SIMPLE_AGENT_GRAPH)}


def test_export_awdl_route_rejects_unparseable_awdl(tmp_path: Path, monkeypatch):
    store = FileStore(tmp_path)
    invalid_graph = {
        **SIMPLE_AGENT_GRAPH,
        "profiles": {"bad-name": {"model": "test-model"}},
        "nodes": [
            {
                "id": "node_1",
                "type": "agent",
                "data": {
                    "profile": "bad-name",
                    "inputs": {"prompt": "prompt_text"},
                    "outputs": {"response": "final_answer"},
                },
            }
        ],
    }
    store.save_workflow("demo", invalid_graph)
    monkeypatch.setattr(workflows_route, "STORE", store)
    client = TestClient(app)

    response = client.post("/api/workflows/demo/export-awdl")

    assert response.status_code == 400
    assert "unexpected character" in response.json()["detail"].lower()


def test_export_awdl_route_rejects_semantically_invalid_awdl(tmp_path: Path, monkeypatch):
    store = FileStore(tmp_path)
    invalid_graph = {
        **SIMPLE_AGENT_GRAPH,
        "profiles": {},
        "nodes": [
            {
                "id": "node_1",
                "type": "agent",
                "data": {
                    "profile": "missing_profile",
                    "inputs": {"prompt": "prompt_text"},
                    "outputs": {"response": "final_answer"},
                },
            }
        ],
    }
    store.save_workflow("demo", invalid_graph)
    monkeypatch.setattr(workflows_route, "STORE", store)
    client = TestClient(app)

    response = client.post("/api/workflows/demo/export-awdl")

    assert response.status_code == 400
    assert "unknown profile" in response.json()["detail"].lower()

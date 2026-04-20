from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routes import workflows as workflows_route
from apps.api.run_manager import RunManager


def test_create_run_writes_meta(tmp_path: Path):
    manager = RunManager(tmp_path)

    record = manager.create_run("demo", {"message": "hi"})

    assert record["workflow_id"] == "demo"
    assert record["status"] == "queued"
    assert record["input"] == {"message": "hi"}
    assert record["finished_at"] is None
    assert (tmp_path / "demo" / record["run_id"] / "meta.json").exists()


def test_finish_run_persists_awdl_result_trace_and_finished_status(tmp_path: Path):
    manager = RunManager(tmp_path)
    record = manager.create_run("demo", {"message": "hi"})

    manager.finish_run(
        "demo",
        record["run_id"],
        status="succeeded",
        result={"output": "hello"},
        awdl='workflow demo {\n  string greeting: "hello"\n}',
        trace=[{"event": "run.started"}, {"event": "run.succeeded"}],
    )

    run_dir = tmp_path / "demo" / record["run_id"]
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))

    assert meta["status"] == "succeeded"
    assert meta["finished_at"] is not None
    assert json.loads((run_dir / "result.json").read_text(encoding="utf-8")) == {"output": "hello"}
    assert (run_dir / "generated.awdl").read_text(encoding="utf-8").startswith("workflow demo")
    assert (run_dir / "trace.jsonl").read_text(encoding="utf-8").splitlines() == [
        '{"event": "run.started"}',
        '{"event": "run.succeeded"}',
    ]


def test_finish_run_rejects_status_outside_v1_lifecycle(tmp_path: Path):
    manager = RunManager(tmp_path)
    record = manager.create_run("demo", {"message": "hi"})

    with pytest.raises(ValueError, match="invalid run status"):
        manager.finish_run(
            "demo",
            record["run_id"],
            status="completed",
            result={"output": "hello"},
            awdl='workflow demo {\n  string greeting: "hello"\n}',
            trace=[],
        )


def test_finish_run_does_not_write_artifacts_when_meta_is_missing(tmp_path: Path):
    manager = RunManager(tmp_path)
    record = manager.create_run("demo", {"message": "hi"})
    run_dir = tmp_path / "demo" / record["run_id"]
    (run_dir / "meta.json").unlink()

    with pytest.raises(FileNotFoundError):
        manager.finish_run(
            "demo",
            record["run_id"],
            status="succeeded",
            result={"output": "hello"},
            awdl='workflow demo {\n  string greeting: "hello"\n}',
            trace=[{"event": "run.started"}],
        )

    assert not (run_dir / "generated.awdl").exists()
    assert not (run_dir / "result.json").exists()
    assert not (run_dir / "trace.jsonl").exists()


def test_list_runs_returns_newest_first(tmp_path: Path):
    manager = RunManager(tmp_path)
    first = manager.create_run("demo", {"message": "first"})
    second = manager.create_run("demo", {"message": "second"})

    runs = manager.list_runs("demo")

    assert [run["run_id"] for run in runs] == [second["run_id"], first["run_id"]]


def test_get_run_returns_persisted_record(tmp_path: Path):
    manager = RunManager(tmp_path)
    record = manager.create_run("demo", {"message": "hi"})

    assert manager.get_run("demo", record["run_id"]) == record


def test_run_routes_start_and_list_runs(tmp_path: Path, monkeypatch):
    store = workflows_route.FileStore(tmp_path)
    store.save_workflow(
        "demo",
        {
            "id": "demo",
            "name": "Demo",
            "variables": [{"name": "user_query", "type": "string", "value": "Hello"}],
            "nodes": [
                {
                    "id": "agent_1",
                    "type": "agent",
                    "data": {
                        "profile": "openrouter_chat",
                        "inputs": {"prompt": "user_query"},
                        "outputs": {"response": "final_answer"},
                    },
                }
            ],
            "edges": [],
            "profiles": {},
        },
    )
    store.save_settings(
        {
            "theme": "light",
            "last_open_workflow_id": None,
            "openrouter_api_key": "sk-or-v1-test",
        }
    )
    monkeypatch.setattr(workflows_route, "STORE", store)
    monkeypatch.setattr(workflows_route, "RUNS", RunManager(tmp_path))
    run_agent_calls = []

    def fake_run_agent(profile_name, inputs, inline_profiles=None, workflow_dir=None):
        run_agent_calls.append(
            {
                "profile_name": profile_name,
                "inputs": inputs,
                "inline_profiles": inline_profiles,
                "workflow_dir": workflow_dir,
            }
        )
        return {"response": "hello from api", "trace": [{"tool": "none"}]}

    monkeypatch.setattr(workflows_route.runtime, "run_agent", fake_run_agent)
    client = TestClient(app)

    create_response = client.post("/api/workflows/demo/runs", json={"input": {"user_query": "hello"}})
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["workflow_id"] == "demo"
    assert created["status"] == "succeeded"
    assert created["input"] == {"user_query": "hello"}
    assert created["finished_at"] is not None
    assert run_agent_calls[0]["profile_name"] == "openrouter_chat"
    assert run_agent_calls[0]["inputs"] == {"prompt": "hello"}
    assert run_agent_calls[0]["inline_profiles"]["openrouter_chat"]["api_key"] == "sk-or-v1-test"

    list_response = client.get("/api/workflows/demo/runs")
    assert list_response.status_code == 200
    assert list_response.json() == [created]


def test_run_detail_route_returns_metadata_and_artifacts(tmp_path: Path, monkeypatch):
    store = workflows_route.FileStore(tmp_path)
    store.save_workflow("demo", {"id": "demo"})
    manager = RunManager(tmp_path)
    monkeypatch.setattr(workflows_route, "STORE", store)
    monkeypatch.setattr(workflows_route, "RUNS", manager)
    client = TestClient(app)

    created = manager.create_run("demo", {"message": "hello"})
    manager.finish_run(
        "demo",
        created["run_id"],
        status="succeeded",
        result={"output": "done"},
        awdl='workflow demo {\n  string greeting: "hello"\n}',
        trace=[{"event": "run.started"}, {"event": "run.succeeded"}],
    )

    response = client.get(f"/api/workflows/demo/runs/{created['run_id']}")

    assert response.status_code == 200
    assert response.json() == {
        **created,
        "status": "succeeded",
        "finished_at": response.json()["finished_at"],
        "awdl": 'workflow demo {\n  string greeting: "hello"\n}',
        "result": {"output": "done"},
        "trace": [{"event": "run.started"}, {"event": "run.succeeded"}],
    }


def test_run_detail_route_returns_empty_artifacts_for_queued_runs(tmp_path: Path, monkeypatch):
    store = workflows_route.FileStore(tmp_path)
    store.save_workflow("demo", {"id": "demo"})
    manager = RunManager(tmp_path)
    monkeypatch.setattr(workflows_route, "STORE", store)
    monkeypatch.setattr(workflows_route, "RUNS", manager)
    client = TestClient(app)

    created = manager.create_run("demo", {"message": "hello"})

    response = client.get(f"/api/workflows/demo/runs/{created['run_id']}")

    assert response.status_code == 200
    assert response.json() == {
        **created,
        "awdl": None,
        "result": None,
        "trace": [],
    }


def test_start_run_route_defaults_to_empty_input(tmp_path: Path, monkeypatch):
    store = workflows_route.FileStore(tmp_path)
    store.save_workflow(
        "demo",
        {
            "id": "demo",
            "name": "Demo",
            "variables": [{"name": "user_query", "type": "string", "value": "Hello"}],
            "nodes": [
                {
                    "id": "agent_1",
                    "type": "agent",
                    "data": {
                        "profile": "openrouter_chat",
                        "inputs": {"prompt": "user_query"},
                        "outputs": {"response": "final_answer"},
                    },
                }
            ],
            "edges": [],
            "profiles": {},
        },
    )
    monkeypatch.setattr(workflows_route, "STORE", store)
    monkeypatch.setattr(workflows_route, "RUNS", RunManager(tmp_path))
    monkeypatch.setattr(
        workflows_route.runtime,
        "run_agent",
        lambda *args, **kwargs: {"response": "default hello", "trace": []},
    )
    client = TestClient(app)

    response = client.post("/api/workflows/demo/runs")

    assert response.status_code == 200
    assert response.json()["input"] == {}


def test_start_run_route_stores_nested_input_payload(tmp_path: Path, monkeypatch):
    store = workflows_route.FileStore(tmp_path)
    store.save_workflow(
        "demo",
        {
            "id": "demo",
            "name": "Demo",
            "variables": [{"name": "user_query", "type": "string", "value": "Hello"}],
            "nodes": [
                {
                    "id": "agent_1",
                    "type": "agent",
                    "data": {
                        "profile": "openrouter_chat",
                        "inputs": {"prompt": "user_query"},
                        "outputs": {"response": "final_answer"},
                    },
                }
            ],
            "edges": [],
            "profiles": {},
        },
    )
    monkeypatch.setattr(workflows_route, "STORE", store)
    monkeypatch.setattr(workflows_route, "RUNS", RunManager(tmp_path))
    monkeypatch.setattr(
        workflows_route.runtime,
        "run_agent",
        lambda *args, **kwargs: {"response": "nested hello", "trace": []},
    )
    client = TestClient(app)

    response = client.post("/api/workflows/demo/runs", json={"input": {"message": "hello"}})

    assert response.status_code == 200
    assert response.json()["input"] == {"message": "hello"}


def test_start_run_route_persists_result_artifacts_after_execution(tmp_path: Path, monkeypatch):
    store = workflows_route.FileStore(tmp_path)
    store.save_workflow(
        "demo",
        {
            "id": "demo",
            "name": "Demo",
            "variables": [{"name": "user_query", "type": "string", "value": "Hello"}],
            "nodes": [
                {
                    "id": "agent_1",
                    "type": "agent",
                    "data": {
                        "profile": "openrouter_chat",
                        "inputs": {"prompt": "user_query"},
                        "outputs": {"response": "final_answer"},
                    },
                }
            ],
            "edges": [],
            "profiles": {},
        },
    )
    monkeypatch.setattr(workflows_route, "STORE", store)
    monkeypatch.setattr(workflows_route, "RUNS", RunManager(tmp_path))
    monkeypatch.setattr(
        workflows_route.runtime,
        "run_agent",
        lambda *args, **kwargs: {"response": "artifact hello", "trace": [{"event": "run.succeeded"}]},
    )
    client = TestClient(app)

    create_response = client.post("/api/workflows/demo/runs", json={"input": {"user_query": "hello"}})
    created = create_response.json()

    detail_response = client.get(f"/api/workflows/demo/runs/{created['run_id']}")

    assert detail_response.status_code == 200
    assert detail_response.json()["result"] == {"final_answer": "artifact hello"}
    assert detail_response.json()["trace"][-1]["event"] == "run.succeeded"
    assert 'profile: "openrouter_chat"' in detail_response.json()["awdl"]


def test_run_routes_return_404_for_missing_workflow(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(workflows_route, "STORE", workflows_route.FileStore(tmp_path))
    monkeypatch.setattr(workflows_route, "RUNS", RunManager(tmp_path / "runs"))
    client = TestClient(app)

    create_response = client.post("/api/workflows/missing/runs", json={"message": "hello"})
    assert create_response.status_code == 404
    assert create_response.json() == {"detail": "workflow not found"}

    list_response = client.get("/api/workflows/missing/runs")
    assert list_response.status_code == 404
    assert list_response.json() == {"detail": "workflow not found"}


def test_run_detail_route_returns_404_for_missing_run(tmp_path: Path, monkeypatch):
    store = workflows_route.FileStore(tmp_path)
    store.save_workflow("demo", {"id": "demo"})
    monkeypatch.setattr(workflows_route, "STORE", store)
    monkeypatch.setattr(workflows_route, "RUNS", RunManager(tmp_path / "runs"))
    client = TestClient(app)

    response = client.get("/api/workflows/demo/runs/missing-run")

    assert response.status_code == 404
    assert response.json() == {"detail": "run not found"}

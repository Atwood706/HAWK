from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routes import workflows as workflows_route
from apps.api.storage import FileStore


def test_health_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from apps.api.routes import settings as settings_route
    monkeypatch.setattr(settings_route, "STORE", FileStore(tmp_path))
    client = TestClient(app)

    response = client.get("/api/settings")

    assert response.status_code == 200
    assert response.json() == {
        "theme": "light",
        "last_open_workflow_id": None,
        "openrouter_api_key": None,
    }


def test_save_and_load_workflow(tmp_path: Path):
    store = FileStore(tmp_path)
    payload = {"id": "demo", "name": "Demo", "nodes": [], "edges": []}

    store.save_workflow("demo", payload)

    assert store.load_workflow("demo") == payload


def test_save_and_load_profile_text(tmp_path: Path):
    store = FileStore(tmp_path)
    profile_text = 'model = "test-model"\nmax_turns = 3\n'

    store.save_profile("coder", profile_text)

    assert store.load_profile("coder") == profile_text


def test_list_profiles_returns_profile_names(tmp_path: Path):
    store = FileStore(tmp_path)
    store.save_profile("coder", 'model = "test-model"\n')
    store.save_profile("writer", 'model = "gpt-4o-mini"\n')

    assert store.list_profiles() == ["coder", "writer"]


def test_save_and_load_settings(tmp_path: Path):
    store = FileStore(tmp_path)
    payload = {
        "theme": "dark",
        "last_open_workflow_id": "demo",
        "openrouter_api_key": "sk-or-v1-test",
    }

    store.save_settings(payload)

    assert store.load_settings() == payload


def test_list_templates(tmp_path: Path):
    store = FileStore(tmp_path)
    store.ensure_dirs()
    (tmp_path / "templates" / "starter.workflow.json").write_text(
        '{"id":"starter"}',
        encoding="utf-8",
    )

    assert store.list_templates() == ["starter.workflow.json"]


def test_save_workflow_rejects_unsafe_id(tmp_path: Path):
    store = FileStore(tmp_path)

    with pytest.raises(ValueError, match="invalid workflow id"):
        store.save_workflow("../escape", {"id": "../escape"})


def test_workflow_routes_list_seeded_demo_when_store_is_empty():
    client = TestClient(app)

    response = client.get("/api/workflows")

    assert response.status_code == 200
    assert any(item["id"] == "openrouter_demo" for item in response.json())


def test_workflow_routes_list_create_and_get(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(workflows_route, "STORE", FileStore(tmp_path))
    client = TestClient(app)
    payload = {"id": "demo", "name": "Demo", "nodes": [], "edges": []}

    create_response = client.post("/api/workflows", json=payload)
    assert create_response.status_code == 200
    assert create_response.json() == payload

    list_response = client.get("/api/workflows")
    assert list_response.status_code == 200
    items = list_response.json()
    assert payload in items
    assert any(item["id"] == "openrouter_demo" for item in items)

    get_response = client.get("/api/workflows/demo")
    assert get_response.status_code == 200
    assert get_response.json() == payload


def test_create_workflow_requires_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(workflows_route, "STORE", FileStore(tmp_path))
    client = TestClient(app)

    response = client.post("/api/workflows", json={"name": "Demo"})

    assert response.status_code == 400
    assert response.json()["detail"] == "workflow id is required"


@pytest.mark.parametrize("workflow_id", [123, {"x": 1}, ["demo"], ""])
def test_create_workflow_rejects_invalid_id_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    workflow_id: object,
):
    monkeypatch.setattr(workflows_route, "STORE", FileStore(tmp_path))
    client = TestClient(app)

    response = client.post("/api/workflows", json={"id": workflow_id, "name": "Demo"})

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid workflow id: expected a simple filename"


def test_get_workflow_missing_returns_404(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(workflows_route, "STORE", FileStore(tmp_path))
    client = TestClient(app)

    response = client.get("/api/workflows/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "workflow not found"

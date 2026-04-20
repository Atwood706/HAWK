from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routes import profiles as profiles_route
from apps.api.routes import settings as settings_route
from apps.api.routes import skills as skills_route
from apps.api.routes import tools as tools_route
from apps.api.storage import FileStore
from stdlib import runtime


def test_profiles_routes_list_read_and_save(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(profiles_route, "STORE", FileStore(tmp_path))
    client = TestClient(app)
    profile_text = 'model = "test-model"\nmax_turns = 3\ntools = ["web_search"]\n'

    save_response = client.put("/api/profiles/coder", json={"content": profile_text})
    assert save_response.status_code == 200
    assert save_response.json() == {"name": "coder", "content": profile_text}

    list_response = client.get("/api/profiles")
    assert list_response.status_code == 200
    assert {"name": "coder"} in list_response.json()
    assert {"name": "openrouter_chat"} in list_response.json()

    read_response = client.get("/api/profiles/coder")
    assert read_response.status_code == 200
    assert read_response.json() == {"name": "coder", "content": profile_text}


def test_tools_route_lists_builtin_registry():
    client = TestClient(app)

    response = client.get("/api/tools")

    assert response.status_code == 200
    tools = response.json()
    assert any(tool["name"] == "file_read" for tool in tools)
    web_search = next(tool for tool in tools if tool["name"] == "web_search")
    assert web_search["description"] == "Search the web"
    assert web_search["category"] == "TOOL"
    assert any(port["name"] == "query" for port in web_search["inputs"])


def test_skills_routes_list_and_read_discovered_docs(tmp_path: Path, monkeypatch):
    skill_dir = tmp_path / ".codex" / "superpowers" / "skills" / "brainstorming"
    skill_dir.mkdir(parents=True)
    skill_doc = skill_dir / "SKILL.md"
    skill_doc.write_text("# Brainstorming\n\nPlan before coding.\n", encoding="utf-8")
    monkeypatch.setattr(runtime.Path, "home", lambda: tmp_path)
    client = TestClient(app)

    list_response = client.get("/api/skills")
    assert list_response.status_code == 200
    skills = list_response.json()
    assert {"name": "brainstorming", "path": str(skill_doc)} in skills

    read_response = client.get("/api/skills/brainstorming")
    assert read_response.status_code == 200
    assert read_response.json() == {
        "name": "brainstorming",
        "path": str(skill_doc),
        "content": "# Brainstorming\n\nPlan before coding.\n",
    }


def test_settings_route_reads_persisted_values(tmp_path: Path, monkeypatch):
    store = FileStore(tmp_path)
    store.save_settings(
        {
            "theme": "dark",
            "last_open_workflow_id": "demo",
            "openrouter_api_key": "sk-or-v1-test",
        }
    )
    monkeypatch.setattr(settings_route, "STORE", store)
    client = TestClient(app)

    response = client.get("/api/settings")

    assert response.status_code == 200
    assert response.json() == {
        "theme": "dark",
        "last_open_workflow_id": "demo",
        "openrouter_api_key": "sk-or-v1-test",
    }


def test_settings_route_saves_valid_payload(tmp_path: Path, monkeypatch):
    store = FileStore(tmp_path)
    monkeypatch.setattr(settings_route, "STORE", store)
    client = TestClient(app)
    payload = {
        "theme": "dark",
        "last_open_workflow_id": "demo",
        "openrouter_api_key": "sk-or-v1-test",
    }

    response = client.put("/api/settings", json=payload)

    assert response.status_code == 200
    assert response.json() == payload
    assert store.load_settings() == payload


@pytest.mark.parametrize(
    "payload",
    [
        [],
        "dark",
        42,
        True,
        None,
        {"theme": "sepia", "last_open_workflow_id": "demo", "openrouter_api_key": None},
        {"theme": "", "last_open_workflow_id": "demo", "openrouter_api_key": None},
        {"theme": 123, "last_open_workflow_id": "demo", "openrouter_api_key": None},
        {"theme": "dark", "last_open_workflow_id": 1, "openrouter_api_key": None},
        {"theme": "dark", "last_open_workflow_id": "demo", "openrouter_api_key": 1},
        {"theme": "dark", "last_open_workflow_id": "demo", "openrouter_api_key": "x", "extra": "value"},
    ],
)
def test_settings_route_rejects_invalid_payloads_and_does_not_write_file(
    tmp_path: Path,
    monkeypatch,
    payload,
):
    store = FileStore(tmp_path)
    monkeypatch.setattr(settings_route, "STORE", store)
    client = TestClient(app)

    response = client.put("/api/settings", json=payload)

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid settings payload"}
    assert not (tmp_path / "settings" / "settings.json").exists()


@pytest.mark.parametrize("payload", [[], "dark", 42, True, None])
def test_settings_route_rejects_non_object_json_payload(
    tmp_path: Path,
    monkeypatch,
    payload,
):
    store = FileStore(tmp_path)
    store.ensure_dirs()
    (tmp_path / "settings" / "settings.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(settings_route, "STORE", store)
    client = TestClient(app)

    response = client.get("/api/settings")

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid settings file"}


def test_profiles_route_lists_seeded_profiles_when_store_is_empty(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(profiles_route, "STORE", FileStore(tmp_path))
    client = TestClient(app)

    response = client.get("/api/profiles")

    assert response.status_code == 200
    assert {"name": "openrouter_chat"} in response.json()


def test_save_profile_route_rejects_invalid_toml_and_does_not_write_file(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(profiles_route, "STORE", FileStore(tmp_path))
    client = TestClient(app)

    response = client.put("/api/profiles/coder", json={"content": "model = \"x\"\nmax_turns = \n"})

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid TOML profile"}
    assert not (tmp_path / "profiles" / "coder.toml").exists()

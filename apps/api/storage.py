from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]


class FileStore:
    def __init__(self, root: Path):
        self.root = root
        self.workflows_dir = root / "workflows"
        self.profiles_dir = root / "profiles"
        self.runs_dir = root / "runs"
        self.settings_dir = root / "settings"
        self.templates_dir = root / "templates"

    def ensure_dirs(self) -> None:
        for path in (
            self.workflows_dir,
            self.profiles_dir,
            self.runs_dir,
            self.settings_dir,
            self.templates_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def _validate_simple_name(self, value: object, kind: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"invalid {kind}: expected a simple filename")

        if not value or value in {".", ".."}:
            raise ValueError(f"invalid {kind}: expected a simple filename")

        candidate = Path(value)
        if candidate.name != value:
            raise ValueError(f"invalid {kind}: expected a simple filename")

        return value

    def _validate_workflow_id(self, workflow_id: object) -> str:
        return self._validate_simple_name(workflow_id, "workflow id")

    def _workflow_path(self, workflow_id: str) -> Path:
        return self.workflows_dir / f"{self._validate_workflow_id(workflow_id)}.json"

    def _profile_path(self, profile_name: str) -> Path:
        return self.profiles_dir / f"{self._validate_simple_name(profile_name, 'profile name')}.toml"

    def _settings_path(self) -> Path:
        return self.settings_dir / "settings.json"

    def save_workflow(self, workflow_id: str, payload: dict[str, Any]) -> None:
        self.ensure_dirs()
        path = self._workflow_path(workflow_id)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_workflow(self, workflow_id: str) -> dict[str, Any]:
        path = self._workflow_path(workflow_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def list_workflows(self) -> list[dict[str, Any]]:
        self.ensure_dirs()
        workflows: list[dict[str, Any]] = []
        for path in sorted(self.workflows_dir.glob("*.json")):
            workflows.append(json.loads(path.read_text(encoding="utf-8")))
        return workflows

    def save_profile(self, profile_name: str, content: str) -> None:
        self.ensure_dirs()
        path = self._profile_path(profile_name)
        try:
            tomllib.loads(content)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError("invalid TOML profile") from exc
        path.write_text(content, encoding="utf-8")

    def load_profile(self, profile_name: str) -> str:
        path = self._profile_path(profile_name)
        return path.read_text(encoding="utf-8")

    def list_profiles(self) -> list[str]:
        self.ensure_dirs()
        return sorted(path.stem for path in self.profiles_dir.glob("*.toml"))

    def delete_profile(self, profile_name: str) -> None:
        self.ensure_dirs()
        path = self._profile_path(profile_name)
        if path.exists():
            path.unlink()

    def save_settings(self, payload: dict[str, Any]) -> None:
        self.ensure_dirs()
        path = self._settings_path()
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_settings(self) -> dict[str, Any]:
        self.ensure_dirs()
        path = self._settings_path()
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def list_templates(self) -> list[str]:
        self.ensure_dirs()
        return sorted(path.name for path in self.templates_dir.glob("*.json"))

from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import Mock

import pytest

from scripts import dev_workbench


def test_repo_root_resolves_from_script_location():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "dev_workbench.py"

    assert dev_workbench.repo_root(script_path) == Path(__file__).resolve().parents[1]


def test_build_process_specs_uses_repo_local_commands():
    root = Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / "dev_workbench.py"

    specs = dev_workbench.build_process_specs(script_path)

    assert [spec.name for spec in specs] == ["api", "web"]
    assert specs[0].cmd == [
        sys.executable,
        "-m",
        "uvicorn",
        "apps.api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ]
    assert specs[0].cwd == root
    assert specs[1].cmd == ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5174"]
    assert specs[1].cwd == root / "apps/web"


def test_start_processes_terminates_already_started_processes_on_partial_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    first_process = Mock()
    started_specs: list[str] = []

    def fake_start_process(spec: dev_workbench.ProcessSpec):
        started_specs.append(spec.name)
        if spec.name == "web":
            raise OSError("npm missing")
        return first_process

    terminate_mock = Mock()
    monkeypatch.setattr(dev_workbench, "start_process", fake_start_process)
    monkeypatch.setattr(dev_workbench, "terminate_processes", terminate_mock)

    with pytest.raises(OSError, match="npm missing"):
        dev_workbench.start_processes(
            [
                dev_workbench.ProcessSpec("api", ["api"], Path("/tmp")),
                dev_workbench.ProcessSpec("web", ["web"], Path("/tmp")),
            ]
        )

    assert started_specs == ["api", "web"]
    terminate_mock.assert_called_once_with([first_process])


def test_vite_proxy_target_matches_launcher_api_origin():
    vite_config = (Path(__file__).resolve().parents[1] / "apps/web/vite.config.ts").read_text(
        encoding="utf-8"
    )

    assert f'target: "{dev_workbench.api_origin()}"' in vite_config

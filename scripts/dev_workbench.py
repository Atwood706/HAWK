from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


API_HOST = "127.0.0.1"
API_PORT = 8000
WEB_HOST = "127.0.0.1"
WEB_PORT = 5174


@dataclass(frozen=True)
class ProcessSpec:
    name: str
    cmd: list[str]
    cwd: Path


def api_origin() -> str:
    return f"http://{API_HOST}:{API_PORT}"


def repo_root(script_path: Path | None = None) -> Path:
    path = script_path or Path(__file__)
    return path.resolve().parents[1]


def build_process_specs(script_path: Path | None = None) -> list[ProcessSpec]:
    root = repo_root(script_path)
    return [
        ProcessSpec(
            name="api",
            cmd=[
                sys.executable,
                "-m",
                "uvicorn",
                "apps.api.main:app",
                "--host",
                API_HOST,
                "--port",
                str(API_PORT),
                "--reload",
            ],
            cwd=root,
        ),
        ProcessSpec(
            name="web",
            cmd=[
                "npm",
                "run",
                "dev",
                "--",
                "--host",
                WEB_HOST,
                "--port",
                str(WEB_PORT),
            ],
            cwd=root / "apps/web",
        ),
    ]


def _popen_kwargs() -> dict[str, object]:
    if os.name == "nt":
        return {
            "creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        }
    return {"start_new_session": True}


def start_process(spec: ProcessSpec) -> subprocess.Popen[str]:
    return subprocess.Popen(
        spec.cmd,
        cwd=spec.cwd,
        stdout=None,
        stderr=None,
        text=True,
        shell=True,
        **_popen_kwargs(),
    )


def start_processes(specs: Sequence[ProcessSpec]) -> list[subprocess.Popen[str]]:
    processes: list[subprocess.Popen[str]] = []
    try:
        for spec in specs:
            processes.append(start_process(spec))
    except Exception:
        terminate_processes(processes)
        raise
    return processes


def wait_for_processes(processes: Sequence[subprocess.Popen[str]]) -> int:
    try:
        while True:
            for process in processes:
                exit_code = process.poll()
                if exit_code is not None:
                    return exit_code
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 130


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        process.terminate()


def terminate_processes(processes: Sequence[subprocess.Popen[str]]) -> None:
    for process in processes:
        _terminate_process(process)

    for process in processes:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def main() -> int:
    specs = build_process_specs()
    print(f"Starting API on {api_origin()}")
    print(f"Starting web app on http://{WEB_HOST}:{WEB_PORT}")

    processes = start_processes(specs)
    try:
        exit_code = wait_for_processes(processes)
    finally:
        terminate_processes(processes)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

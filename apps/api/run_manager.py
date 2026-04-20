from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class RunManager:
    ALLOWED_STATUSES = {"queued", "running", "succeeded", "failed"}

    def __init__(self, runs_dir: Path):
        self.runs_dir = runs_dir

    def _validate_simple_name(self, value: object, *, label: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"invalid {label}: expected a simple filename")

        if not value or value in {".", ".."}:
            raise ValueError(f"invalid {label}: expected a simple filename")

        candidate = Path(value)
        if candidate.name != value:
            raise ValueError(f"invalid {label}: expected a simple filename")

        return value

    def _workflow_dir(self, workflow_id: str) -> Path:
        safe_workflow_id = self._validate_simple_name(workflow_id, label="workflow id")
        return self.runs_dir / safe_workflow_id

    def _run_dir(self, workflow_id: str, run_id: str) -> Path:
        safe_run_id = self._validate_simple_name(run_id, label="run id")
        return self._workflow_dir(workflow_id) / safe_run_id

    def _validate_status(self, status: object) -> str:
        if status not in self.ALLOWED_STATUSES:
            raise ValueError("invalid run status")
        return str(status)

    def create_run(self, workflow_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        run_id = uuid4().hex
        run_dir = self._run_dir(workflow_id, run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "status": self._validate_status("queued"),
            "input": payload,
            "started_at": datetime.now(UTC).isoformat(),
            "finished_at": None,
        }
        (run_dir / "meta.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record

    def finish_run(
        self,
        workflow_id: str,
        run_id: str,
        *,
        status: str,
        result: dict[str, Any],
        awdl: str,
        trace: list[dict[str, Any]],
    ) -> dict[str, Any]:
        run_dir = self._run_dir(workflow_id, run_id)
        safe_status = self._validate_status(status)
        meta_path = run_dir / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        final_meta = {
            **meta,
            "status": safe_status,
            "finished_at": datetime.now(UTC).isoformat(),
        }

        (run_dir / "generated.awdl").write_text(awdl, encoding="utf-8")
        (run_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        trace_lines = "\n".join(json.dumps(event, ensure_ascii=False) for event in trace)
        if trace_lines:
            trace_lines += "\n"
        (run_dir / "trace.jsonl").write_text(trace_lines, encoding="utf-8")
        meta_path.write_text(json.dumps(final_meta, indent=2), encoding="utf-8")
        return final_meta

    def get_run(self, workflow_id: str, run_id: str) -> dict[str, Any]:
        meta_path = self._run_dir(workflow_id, run_id) / "meta.json"
        return json.loads(meta_path.read_text(encoding="utf-8"))

    def get_run_detail(self, workflow_id: str, run_id: str) -> dict[str, Any]:
        run_dir = self._run_dir(workflow_id, run_id)
        meta_path = run_dir / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        awdl_path = run_dir / "generated.awdl"
        result_path = run_dir / "result.json"
        trace_path = run_dir / "trace.jsonl"

        awdl = awdl_path.read_text(encoding="utf-8") if awdl_path.exists() else None
        result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None

        trace: list[dict[str, Any]] = []
        if trace_path.exists():
            for line in trace_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                trace.append(json.loads(line))

        return {
            **meta,
            "awdl": awdl,
            "result": result,
            "trace": trace,
        }

    def list_runs(self, workflow_id: str) -> list[dict[str, Any]]:
        workflow_dir = self._workflow_dir(workflow_id)
        if not workflow_dir.exists():
            return []

        runs: list[dict[str, Any]] = []
        for meta_path in workflow_dir.glob("*/meta.json"):
            runs.append(json.loads(meta_path.read_text(encoding="utf-8")))
        runs.sort(key=lambda item: item["started_at"], reverse=True)
        return runs

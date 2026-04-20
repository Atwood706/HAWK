from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError as PydanticValidationError

from apps.api.awdl_bridge import graph_to_awdl, validate_graph
from apps.api.config import DATA_ROOT, RUNS_DIR
from apps.api.execution import execute_workflow_graph
from apps.api.run_manager import RunManager
from apps.api.seed import ensure_seed_data
from apps.api.storage import FileStore
from awdl.language.errors import AWDLError
from awdl.language.parser import parse_string
from stdlib import runtime


router = APIRouter(tags=["workflows"])

STORE = FileStore(DATA_ROOT)
RUNS = RunManager(RUNS_DIR)


def _require_workflow(workflow_id: str) -> None:
    try:
        STORE.load_workflow(workflow_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="workflow not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/workflows")
def list_workflows() -> list[dict[str, Any]]:
    ensure_seed_data(STORE)
    return STORE.list_workflows()


@router.post("/workflows")
def create_workflow(payload: dict[str, Any]) -> dict[str, Any]:
    workflow_id = payload.get("id")
    if workflow_id is None:
        raise HTTPException(status_code=400, detail="workflow id is required")

    try:
        STORE.save_workflow(workflow_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return payload


@router.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str) -> dict[str, Any]:
    ensure_seed_data(STORE)
    try:
        return STORE.load_workflow(workflow_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="workflow not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workflows/{workflow_id}/validate")
def validate_workflow(workflow_id: str) -> dict[str, Any]:
    ensure_seed_data(STORE)
    try:
        graph = STORE.load_workflow(workflow_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="workflow not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    errors = validate_graph(graph)
    return {"valid": not errors, "errors": errors}


@router.post("/workflows/{workflow_id}/export-awdl")
def export_awdl(workflow_id: str) -> dict[str, str]:
    ensure_seed_data(STORE)
    try:
        graph = STORE.load_workflow(workflow_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="workflow not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        awdl = graph_to_awdl(graph)
    except (PydanticValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        parse_string(awdl)
    except AWDLError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    errors = validate_graph(graph)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    return {"awdl": awdl}


@router.post("/workflows/{workflow_id}/runs")
def start_run(workflow_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_seed_data(STORE)
    _require_workflow(workflow_id)
    if payload is None:
        run_input: dict[str, Any] = {}
    elif "input" in payload and isinstance(payload["input"], dict):
        run_input = payload["input"]
    else:
        run_input = payload
    created = RUNS.create_run(workflow_id, run_input)
    try:
        status, awdl, result, trace = execute_workflow_graph(workflow_id, run_input, store=STORE)
    except Exception as exc:
        status = "failed"
        awdl = ""
        result = {"error": str(exc)}
        trace = [{"event": "run.failed", "workflow_id": workflow_id, "error": str(exc)}]
    try:
        return RUNS.finish_run(
            workflow_id,
            created["run_id"],
            status=status,
            result=result,
            awdl=awdl,
            trace=trace,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/runs")
def list_runs(workflow_id: str) -> list[dict[str, Any]]:
    _require_workflow(workflow_id)
    try:
        return RUNS.list_runs(workflow_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/workflows/{workflow_id}/runs/{run_id}")
def get_run_detail(workflow_id: str, run_id: str) -> dict[str, Any]:
    _require_workflow(workflow_id)
    try:
        return RUNS.get_run_detail(workflow_id, run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

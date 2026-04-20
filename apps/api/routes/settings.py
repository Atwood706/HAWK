import json
from typing import Any

from fastapi import APIRouter, Body, HTTPException
from pydantic import ValidationError

from apps.api.config import DATA_ROOT
from apps.api.models import AppSettings
from apps.api.storage import FileStore


router = APIRouter(tags=["settings"])
STORE = FileStore(DATA_ROOT)


def _load_settings_payload() -> dict[str, Any]:
    try:
        payload = STORE.load_settings()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid settings file") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid settings file")

    return payload


def _validate_settings(payload: dict[str, Any]) -> AppSettings:
    try:
        return AppSettings.model_validate(payload, strict=True)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="invalid settings payload") from exc


@router.get("/settings", response_model=AppSettings)
def get_settings() -> AppSettings:
    payload = _load_settings_payload()
    return _validate_settings(payload)


@router.put("/settings", response_model=AppSettings)
def save_settings(payload: Any | None = Body(default=None)) -> AppSettings:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid settings payload")

    settings = _validate_settings(payload)
    STORE.save_settings(settings.model_dump())
    return settings

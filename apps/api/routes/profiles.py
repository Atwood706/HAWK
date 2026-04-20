from fastapi import APIRouter, HTTPException

from apps.api.config import DATA_ROOT
from apps.api.models import ProfileContent, ProfileDetail, ProfileSummary
from apps.api.seed import ensure_seed_data
from apps.api.storage import FileStore


router = APIRouter(tags=["profiles"])
STORE = FileStore(DATA_ROOT)


@router.get("/profiles", response_model=list[ProfileSummary])
def list_profiles() -> list[ProfileSummary]:
    ensure_seed_data(STORE)
    return [ProfileSummary(name=name) for name in STORE.list_profiles()]


@router.get("/profiles/{profile_name}", response_model=ProfileDetail)
def get_profile(profile_name: str) -> ProfileDetail:
    ensure_seed_data(STORE)
    try:
        return ProfileDetail(name=profile_name, content=STORE.load_profile(profile_name))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="profile not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/profiles/{profile_name}", response_model=ProfileDetail)
def save_profile(profile_name: str, payload: ProfileContent) -> ProfileDetail:
    try:
        STORE.save_profile(profile_name, payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProfileDetail(name=profile_name, content=payload.content)


@router.delete("/profiles/{profile_name}", status_code=204)
def delete_profile(profile_name: str) -> None:
    ensure_seed_data(STORE)
    try:
        STORE.load_profile(profile_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="profile not found") from exc
    STORE.delete_profile(profile_name)

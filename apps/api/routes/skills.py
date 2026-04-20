from pathlib import Path

from fastapi import APIRouter, HTTPException

from apps.api.models import SkillDetail, SkillSummary
from stdlib.runtime import _find_skill_path, _iter_skill_dirs


router = APIRouter(tags=["skills"])


def _skill_name(path: Path) -> str:
    return path.parent.name


def _discover_skills() -> dict[str, Path]:
    skills: dict[str, Path] = {}
    for path in _iter_skill_dirs():
        skills.setdefault(_skill_name(path), path)
    return dict(sorted(skills.items()))


@router.get("/skills", response_model=list[SkillSummary])
def list_skills() -> list[SkillSummary]:
    return [SkillSummary(name=name, path=str(path)) for name, path in _discover_skills().items()]


@router.get("/skills/{skill_name}", response_model=SkillDetail)
def get_skill(skill_name: str) -> SkillDetail:
    skill_path = _find_skill_path(skill_name)
    if skill_path is None:
        raise HTTPException(status_code=404, detail="skill not found")
    return SkillDetail(name=_skill_name(skill_path), path=str(skill_path), content=skill_path.read_text(encoding="utf-8"))

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: Literal["light", "dark", "system"] = "light"
    last_open_workflow_id: str | None = None
    openrouter_api_key: str | None = None


class ProfileContent(BaseModel):
    content: str


class ProfileSummary(BaseModel):
    name: str


class ProfileDetail(BaseModel):
    name: str
    content: str


class ToolPort(BaseModel):
    name: str
    description: str = ""
    required: bool = True
    default: Any | None = None
    port_type: str = "any"


class BuiltinTool(BaseModel):
    name: str
    description: str = ""
    category: str
    inputs: list[ToolPort] = Field(default_factory=list)
    outputs: list[ToolPort] = Field(default_factory=list)


class SkillSummary(BaseModel):
    name: str
    path: str


class SkillDetail(BaseModel):
    name: str
    path: str
    content: str

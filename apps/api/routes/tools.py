from fastapi import APIRouter

from apps.api.models import BuiltinTool, ToolPort
from awdl.ir.builtins import BUILTIN_REGISTRY


router = APIRouter(tags=["tools"])


@router.get("/tools", response_model=list[BuiltinTool])
def list_tools() -> list[BuiltinTool]:
    tools: list[BuiltinTool] = []
    for definition in BUILTIN_REGISTRY.get_all_tools():
        tools.append(
            BuiltinTool(
                name=definition.name,
                description=definition.description,
                category=definition.category.name,
                inputs=[ToolPort(**port.__dict__) for port in definition.inputs],
                outputs=[ToolPort(**port.__dict__) for port in definition.outputs],
            )
        )
    return tools

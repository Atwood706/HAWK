"""
Builtin registry for rebuilt AWDL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class ElementCategory(Enum):
    TOOL = auto()


@dataclass
class PortDefinition:
    name: str
    description: str = ""
    required: bool = True
    default: Optional[Any] = None
    port_type: str = "any"


@dataclass
class BuiltinDefinition:
    name: str
    category: ElementCategory
    description: str = ""
    inputs: List[PortDefinition] = field(default_factory=list)
    outputs: List[PortDefinition] = field(default_factory=list)

    @property
    def input_names(self) -> List[str]:
        return [port.name for port in self.inputs]

    @property
    def output_names(self) -> List[str]:
        return [port.name for port in self.outputs]


class BuiltinRegistry:
    def __init__(self) -> None:
        self._definitions: Dict[str, BuiltinDefinition] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(
            BuiltinDefinition(
                name="arxiv_search",
                category=ElementCategory.TOOL,
                description="Search arXiv for recent papers",
                inputs=[
                    PortDefinition(name="query"),
                    PortDefinition(name="max_results", required=False, default=10),
                ],
                outputs=[
                    PortDefinition(name="results"),
                    PortDefinition(name="error", required=False),
                ],
            )
        )
        self.register(
            BuiltinDefinition(
                name="file_read",
                category=ElementCategory.TOOL,
                description="Read a file from disk",
                inputs=[PortDefinition(name="path")],
                outputs=[PortDefinition(name="content"), PortDefinition(name="error", required=False)],
            )
        )
        self.register(
            BuiltinDefinition(
                name="file_write",
                category=ElementCategory.TOOL,
                description="Write a file to disk",
                inputs=[PortDefinition(name="path"), PortDefinition(name="content")],
                outputs=[PortDefinition(name="success"), PortDefinition(name="error", required=False)],
            )
        )
        self.register(
            BuiltinDefinition(
                name="text_concat",
                category=ElementCategory.TOOL,
                description="Concatenate text",
                inputs=[
                    PortDefinition(name="left"),
                    PortDefinition(name="right"),
                    PortDefinition(name="sep", required=False, default="\n\n"),
                ],
                outputs=[PortDefinition(name="result")],
            )
        )
        self.register(
            BuiltinDefinition(
                name="web_search",
                category=ElementCategory.TOOL,
                description="Search the web",
                inputs=[PortDefinition(name="query"), PortDefinition(name="max_results", required=False, default=10)],
                outputs=[PortDefinition(name="results")],
            )
        )
        self.register(
            BuiltinDefinition(
                name="web_fetch",
                category=ElementCategory.TOOL,
                description="Fetch a URL",
                inputs=[PortDefinition(name="url")],
                outputs=[PortDefinition(name="content"), PortDefinition(name="error", required=False)],
            )
        )
        self.register(
            BuiltinDefinition(
                name="mcp_call",
                category=ElementCategory.TOOL,
                description="Call an MCP tool",
                inputs=[
                    PortDefinition(name="server"),
                    PortDefinition(name="tool"),
                    PortDefinition(name="args_json", required=False, default="{}"),
                ],
                outputs=[PortDefinition(name="result"), PortDefinition(name="error", required=False)],
            )
        )
        self.register(
            BuiltinDefinition(
                name="code_search",
                category=ElementCategory.TOOL,
                description="Search files in the workspace",
                inputs=[PortDefinition(name="query"), PortDefinition(name="root", required=False, default=".")],
                outputs=[PortDefinition(name="results"), PortDefinition(name="error", required=False)],
            )
        )
        self.register(
            BuiltinDefinition(
                name="shell",
                category=ElementCategory.TOOL,
                description="Run a shell command",
                inputs=[PortDefinition(name="command"), PortDefinition(name="cwd", required=False, default=".")],
                outputs=[
                    PortDefinition(name="stdout"),
                    PortDefinition(name="stderr", required=False),
                    PortDefinition(name="exit_code"),
                ],
            )
        )
        self.register(
            BuiltinDefinition(
                name="pubmed_search",
                category=ElementCategory.TOOL,
                description="Search PubMed for biomedical literature",
                inputs=[
                    PortDefinition(name="query"),
                    PortDefinition(name="max_results", required=False, default=10),
                    PortDefinition(name="sort", required=False, default="relevance"),
                    PortDefinition(name="include_abstracts", required=False, default=False),
                    PortDefinition(name="mindate", required=False, default=None),
                    PortDefinition(name="maxdate", required=False, default=None),
                ],
                outputs=[
                    PortDefinition(name="results"),
                    PortDefinition(name="pmids"),
                    PortDefinition(name="error", required=False),
                ],
            )
        )
        self.register(
            BuiltinDefinition(
                name="skill_discovery",
                category=ElementCategory.TOOL,
                description="List available skills",
                inputs=[PortDefinition(name="query", required=False, default="")],
                outputs=[PortDefinition(name="results")],
            )
        )
        self.register(
            BuiltinDefinition(
                name="skill_load",
                category=ElementCategory.TOOL,
                description="Load a skill document",
                inputs=[PortDefinition(name="name")],
                outputs=[PortDefinition(name="content"), PortDefinition(name="error", required=False)],
            )
        )

    def register(self, definition: BuiltinDefinition) -> None:
        self._definitions[definition.name] = definition

    def get(self, name: str) -> Optional[BuiltinDefinition]:
        return self._definitions.get(name)

    def exists(self, name: str) -> bool:
        return name in self._definitions

    def is_tool(self, name: str) -> bool:
        return name in self._definitions

    def get_all_tools(self) -> List[BuiltinDefinition]:
        return list(self._definitions.values())


BUILTIN_REGISTRY = BuiltinRegistry()

"""
AWDL element and definition types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


ConfigValue = str | int | float | bool | List[Any]


class Element(ABC):
    """Common interface for executable workflow elements."""

    @abstractmethod
    def get_read_vars(self) -> Set[str]:
        pass

    @abstractmethod
    def get_write_vars(self) -> Set[str]:
        pass

    @property
    @abstractmethod
    def element_id(self) -> str:
        pass


@dataclass
class Agent(Element):
    """Unified agent node driven by a profile."""

    id: str
    agent_type: str = "agent"
    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    line: int = 0
    column: int = 0

    @property
    def element_id(self) -> str:
        return self.id

    def get_read_vars(self) -> Set[str]:
        return set(self.inputs.values())

    def get_write_vars(self) -> Set[str]:
        return set(self.outputs.values())


@dataclass
class Tool(Element):
    """Builtin tool invocation."""

    id: str
    tool_type: str
    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    line: int = 0
    column: int = 0

    @property
    def element_id(self) -> str:
        return self.id

    def get_read_vars(self) -> Set[str]:
        return set(self.inputs.values())

    def get_write_vars(self) -> Set[str]:
        return set(self.outputs.values())


@dataclass
class FunctionCall(Element):
    """Invocation of a user-defined subflow/function."""

    id: str
    function_name: str
    inputs: Dict[str, str] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    line: int = 0
    column: int = 0

    @property
    def element_id(self) -> str:
        return self.id

    def get_read_vars(self) -> Set[str]:
        return set(self.inputs.values())

    def get_write_vars(self) -> Set[str]:
        return set(self.outputs.values())


@dataclass
class ProfileDefinition:
    """Reusable agent capability template."""

    name: str
    config: Dict[str, ConfigValue] = field(default_factory=dict)
    line: int = 0
    column: int = 0


@dataclass
class FunctionDefinition:
    """Reusable AWDL subflow with declared inputs and outputs."""

    name: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    variables: List[Any] = field(default_factory=list)
    elements: List[Any] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def get_variable_names(self) -> Set[str]:
        declared = {var.name for var in self.variables}
        return declared | set(self.inputs) | set(self.outputs)


ElementType = Agent | Tool | FunctionCall

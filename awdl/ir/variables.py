"""
AWDL Variable Definitions

This module defines the Variable class and related types for the AWDL IR.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional


class VariableType(Enum):
    """Enumeration of variable types in AWDL."""
    
    STRING = auto()
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    LIST = auto()
    FILE = auto()
    IMAGE = auto()
    ANY = auto()  # For untyped or dynamically typed variables
    
    @classmethod
    def from_string(cls, type_str: str) -> "VariableType":
        """Convert a string type name to VariableType."""
        mapping = {
            "string": cls.STRING,
            "int": cls.INT,
            "float": cls.FLOAT,
            "bool": cls.BOOL,
            "list": cls.LIST,
            "file": cls.FILE,
            "image": cls.IMAGE,
        }
        return mapping.get(type_str.lower(), cls.ANY)
    
    def to_python_type(self) -> str:
        """Convert to Python type annotation string."""
        mapping = {
            VariableType.STRING: "str",
            VariableType.INT: "int",
            VariableType.FLOAT: "float",
            VariableType.BOOL: "bool",
            VariableType.LIST: "list",
            VariableType.FILE: "str",  # File paths are strings
            VariableType.IMAGE: "str",  # Image paths are strings
            VariableType.ANY: "Any",
        }
        return mapping.get(self, "Any")


@dataclass
class Variable:
    """
    Represents a variable in an AWDL workflow.
    
    Variables are the data flow mechanism in AWDL. Elements (Agents, Tools)
    read from and write to variables to communicate.
    """
    
    name: str
    var_type: VariableType
    default_value: Optional[Any] = None
    line: int = 0
    column: int = 0
    
    def __hash__(self) -> int:
        return hash(self.name)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Variable):
            return self.name == other.name
        return False
    
    def has_default(self) -> bool:
        """Check if this variable has a default value."""
        return self.default_value is not None
    
    def __repr__(self) -> str:
        default_str = f" = {self.default_value!r}" if self.default_value is not None else ""
        return f"Variable({self.var_type.name} {self.name}{default_str})"


@dataclass
class Import:
    """
    Represents an import statement in an AWDL workflow.
    
    Imports bring in agent and tool definitions from the standard library
    or user-defined modules.
    """
    
    module_path: str
    line: int = 0
    column: int = 0
    
    @property
    def module_parts(self) -> list[str]:
        """Split the module path into parts."""
        return self.module_path.split('.')
    
    @property
    def module_name(self) -> str:
        """Get the final module name."""
        return self.module_parts[-1] if self.module_parts else ""
    
    def __repr__(self) -> str:
        return f"Import({self.module_path})"


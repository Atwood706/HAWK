"""
AWDL Element Definitions

This module defines Agent and Tool as first-class elements in the AWDL IR.
These are NOT nodes in a graph - they are independent function-like elements
whose execution order is derived from variable dependencies.
"""

from dataclasses import dataclass, field
from typing import Dict, Set, Optional, Any
from abc import ABC, abstractmethod


class Element(ABC):
    """
    Abstract base for elements in AWDL.
    
    Elements are function-like constructs that have inputs and outputs.
    They do NOT have explicit connections to other elements - the execution
    order is derived from variable dependencies.
    """
    
    @abstractmethod
    def get_read_vars(self) -> Set[str]:
        """Get the set of variable names this element reads from."""
        pass
    
    @abstractmethod
    def get_write_vars(self) -> Set[str]:
        """Get the set of variable names this element writes to."""
        pass
    
    @property
    @abstractmethod
    def element_id(self) -> str:
        """Get the unique identifier for this element."""
        pass


@dataclass
class Agent(Element):
    """
    An Agent element in AWDL.
    
    Agents are AI-powered elements that process inputs and produce outputs.
    They behave like functions with inputs and outputs.
    
    Attributes:
        id: Unique identifier for this agent instance
        agent_type: The type of agent (e.g., "llm", "router")
        inputs: Mapping of input port names to variable names
        outputs: Mapping of output port names to variable names
        config: Optional configuration for the agent
    """
    
    id: str
    agent_type: str
    inputs: Dict[str, str] = field(default_factory=dict)  # port_name -> variable_name
    outputs: Dict[str, str] = field(default_factory=dict)  # port_name -> variable_name
    config: Dict[str, Any] = field(default_factory=dict)
    line: int = 0
    column: int = 0
    
    @property
    def element_id(self) -> str:
        return self.id
    
    def get_read_vars(self) -> Set[str]:
        """Variables this agent reads from (its inputs)."""
        return set(self.inputs.values())
    
    def get_write_vars(self) -> Set[str]:
        """Variables this agent writes to (its outputs)."""
        return set(self.outputs.values())
    
    def get_input_port(self, port_name: str) -> Optional[str]:
        """Get the variable name for an input port."""
        return self.inputs.get(port_name)
    
    def get_output_port(self, port_name: str) -> Optional[str]:
        """Get the variable name for an output port."""
        return self.outputs.get(port_name)
    
    def __repr__(self) -> str:
        inputs_str = ", ".join(f"{k}={v}" for k, v in self.inputs.items())
        outputs_str = ", ".join(f"{k}={v}" for k, v in self.outputs.items())
        return f"Agent({self.id}: {self.agent_type}, in=[{inputs_str}], out=[{outputs_str}])"


@dataclass
class Tool(Element):
    """
    A Tool element in AWDL.
    
    Tools are deterministic operations that process inputs and produce outputs.
    They behave like functions with inputs and outputs.
    
    Attributes:
        id: Unique identifier for this tool instance
        tool_type: The type of tool (e.g., "web_search", "file_read")
        inputs: Mapping of input port names to variable names
        outputs: Mapping of output port names to variable names
        config: Optional configuration for the tool
    """
    
    id: str
    tool_type: str
    inputs: Dict[str, str] = field(default_factory=dict)  # port_name -> variable_name
    outputs: Dict[str, str] = field(default_factory=dict)  # port_name -> variable_name
    config: Dict[str, Any] = field(default_factory=dict)
    line: int = 0
    column: int = 0
    
    @property
    def element_id(self) -> str:
        return self.id
    
    def get_read_vars(self) -> Set[str]:
        """Variables this tool reads from (its inputs)."""
        return set(self.inputs.values())
    
    def get_write_vars(self) -> Set[str]:
        """Variables this tool writes to (its outputs)."""
        return set(self.outputs.values())
    
    def get_input_port(self, port_name: str) -> Optional[str]:
        """Get the variable name for an input port."""
        return self.inputs.get(port_name)
    
    def get_output_port(self, port_name: str) -> Optional[str]:
        """Get the variable name for an output port."""
        return self.outputs.get(port_name)
    
    def __repr__(self) -> str:
        inputs_str = ", ".join(f"{k}={v}" for k, v in self.inputs.items())
        outputs_str = ", ".join(f"{k}={v}" for k, v in self.outputs.items())
        return f"Tool({self.id}: {self.tool_type}, in=[{inputs_str}], out=[{outputs_str}])"


# Type alias for any element type
ElementType = Agent | Tool


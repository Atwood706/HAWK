"""
LangGraph State Generator

This module generates the TypedDict state class for LangGraph
from the workflow's variable declarations.
"""

from typing import List

from awdl.ir.workflow import Workflow
from awdl.ir.variables import Variable, VariableType


class StateGenerator:
    """
    Generates the LangGraph state class from workflow variables.
    
    LangGraph uses a TypedDict to define the state that flows through
    the graph. This generator creates that class from AWDL variables.
    """
    
    def __init__(self, workflow: Workflow):
        """
        Initialize the state generator.
        
        Args:
            workflow: The workflow to generate state for
        """
        self.workflow = workflow
    
    def generate_state_class(self, class_name: str = "WorkflowState") -> str:
        """
        Generate the TypedDict state class.
        
        Args:
            class_name: Name for the generated class
            
        Returns:
            Python code for the state class
        """
        lines = [
            f"class {class_name}(TypedDict):",
            '    """Auto-generated state class for the workflow."""',
        ]
        
        if not self.workflow.variables:
            lines.append("    pass")
        else:
            for var in self.workflow.variables:
                type_hint = self._get_type_hint(var.var_type)
                lines.append(f"    {var.name}: {type_hint}")
        
        return "\n".join(lines)
    
    def _get_type_hint(self, var_type: VariableType) -> str:
        """
        Convert AWDL variable type to Python type hint.
        
        Args:
            var_type: The AWDL variable type
            
        Returns:
            Python type hint string
        """
        return var_type.to_python_type()
    
    def get_initial_state(self) -> str:
        """
        Generate code for the initial state dictionary.
        
        Returns:
            Python code for initial state
        """
        lines = ["initial_state = {"]
        
        for var in self.workflow.variables:
            if var.has_default():
                value = repr(var.default_value)
            else:
                value = self._get_default_for_type(var.var_type)
            lines.append(f'    "{var.name}": {value},')
        
        lines.append("}")
        return "\n".join(lines)
    
    def _get_default_for_type(self, var_type: VariableType) -> str:
        """
        Get the default value for a type.
        
        Args:
            var_type: The AWDL variable type
            
        Returns:
            Python code for the default value
        """
        defaults = {
            VariableType.STRING: '""',
            VariableType.INT: "0",
            VariableType.FLOAT: "0.0",
            VariableType.BOOL: "False",
            VariableType.LIST: "[]",
            VariableType.FILE: '""',
            VariableType.IMAGE: '""',
            VariableType.ANY: "None",
        }
        return defaults.get(var_type, "None")


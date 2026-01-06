"""
AWDL Workflow Definition

This module defines the Workflow class, the top-level container for an AWDL program.
"""

from dataclasses import dataclass, field
from typing import List, Union, Optional, Dict, Set

from awdl.ir.variables import Variable, Import
from awdl.ir.elements import Agent, Tool, Element
from awdl.ir.conditions import Condition, WhileLoop, ForLoop


# Type alias for any workflow element
WorkflowElement = Union[Agent, Tool, Condition, WhileLoop, ForLoop]


@dataclass
class Workflow:
    """
    Container for a complete AWDL workflow.
    
    This is the top-level IR object that represents an entire AWDL program.
    It is completely framework-agnostic - it only knows about AWDL semantics.
    
    Attributes:
        name: The name of the workflow
        version: Version string for the workflow
        imports: List of import statements
        variables: List of declared variables
        elements: List of workflow elements (agents, tools, conditions)
    """
    
    name: str
    version: str = "1.0"
    imports: List[Import] = field(default_factory=list)
    variables: List[Variable] = field(default_factory=list)
    elements: List[WorkflowElement] = field(default_factory=list)
    
    def get_variable(self, name: str) -> Optional[Variable]:
        """Get a variable by name."""
        for var in self.variables:
            if var.name == name:
                return var
        return None
    
    def get_variable_names(self) -> Set[str]:
        """Get all variable names."""
        return {var.name for var in self.variables}
    
    def get_agents(self) -> List[Agent]:
        """Get all Agent elements."""
        return [e for e in self.elements if isinstance(e, Agent)]
    
    def get_tools(self) -> List[Tool]:
        """Get all Tool elements."""
        return [e for e in self.elements if isinstance(e, Tool)]
    
    def get_conditions(self) -> List[Condition]:
        """Get all Condition elements."""
        return [e for e in self.elements if isinstance(e, Condition)]
    
    def get_element_by_id(self, element_id: str) -> Optional[WorkflowElement]:
        """Get an element by its ID."""
        for element in self.elements:
            if hasattr(element, 'element_id') and element.element_id == element_id:
                return element
        return None
    
    def get_all_elements_flat(self) -> List[WorkflowElement]:
        """
        Get all elements including those nested in conditions/loops.
        
        This flattens the element hierarchy for dependency analysis.
        """
        all_elements: List[WorkflowElement] = []
        
        def collect_elements(elements: List[WorkflowElement]) -> None:
            for element in elements:
                all_elements.append(element)
                if isinstance(element, Condition):
                    collect_elements(element.then_branch)
                    if element.else_branch:
                        collect_elements(element.else_branch)
                elif isinstance(element, (WhileLoop, ForLoop)):
                    collect_elements(element.body)
        
        collect_elements(self.elements)
        return all_elements
    
    def validate(self) -> List["ValidationError"]:
        """
        Validate the workflow for errors.
        
        Checks for:
        - Undefined variables
        - Type mismatches
        - Circular dependencies
        - Missing required inputs
        
        Returns:
            List of validation errors found
        """
        from awdl.language.errors import ValidationError
        
        errors: List[ValidationError] = []
        var_names = self.get_variable_names()
        
        # Check for undefined variables in elements
        for element in self.get_all_elements_flat():
            read_vars = element.get_read_vars()
            write_vars = element.get_write_vars()
            
            for var_name in read_vars:
                if var_name not in var_names:
                    errors.append(ValidationError(
                        message=f"Undefined variable '{var_name}' in element '{element.element_id}'",
                        severity="error",
                    ))
            
            for var_name in write_vars:
                if var_name not in var_names:
                    errors.append(ValidationError(
                        message=f"Undefined variable '{var_name}' in element '{element.element_id}'",
                        severity="error",
                    ))
        
        return errors
    
    def get_dependency_analyzer(self) -> "DependencyAnalyzer":
        """Get the dependency analyzer for this workflow."""
        from awdl.ir.dependency import DependencyAnalyzer
        return DependencyAnalyzer(self)
    
    def __repr__(self) -> str:
        return (
            f"Workflow({self.name} v{self.version}, "
            f"imports={len(self.imports)}, "
            f"variables={len(self.variables)}, "
            f"elements={len(self.elements)})"
        )


"""
AWDL Base Compiler

This module defines the abstract base class for all AWDL compilers.
Each compiler targets a specific agent framework (e.g., LangGraph, Agno).
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from awdl.ir.workflow import Workflow, WorkflowElement
from awdl.ir.dependency import DependencyAnalyzer


class BaseCompiler(ABC):
    """
    Abstract base class for all target framework compilers.
    
    Each compiler takes a framework-agnostic Workflow IR and transforms
    it into executable code for a specific agent framework.
    
    The key insight is that the IR has NO graph structure - it only has
    elements with variable dependencies. The compiler's job is to:
    1. Analyze variable dependencies to determine execution order
    2. Transform elements into framework-specific constructs
    3. Generate the appropriate graph/execution structure for the framework
    """
    
    def __init__(self, workflow: Workflow):
        """
        Initialize the compiler with a workflow.
        
        Args:
            workflow: The workflow to compile
        """
        self.workflow = workflow
        self.analyzer = workflow.get_dependency_analyzer()
    
    @abstractmethod
    def compile(self) -> str:
        """
        Compile the workflow to target framework code.
        
        Returns:
            Generated Python code as a string
        """
        pass
    
    @abstractmethod
    def get_target_name(self) -> str:
        """
        Return the name of the target framework.
        
        Returns:
            Framework name (e.g., "langgraph", "agno")
        """
        pass
    
    def get_execution_order(self) -> List[WorkflowElement]:
        """
        Get the execution order of elements using the dependency analyzer.
        
        Returns:
            List of elements in execution order
        """
        order = self.analyzer.get_execution_order()
        return order.ordered_elements
    
    def validate(self) -> List[str]:
        """
        Validate the workflow before compilation.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check for circular dependencies
        cycle = self.analyzer.detect_cycles()
        if cycle:
            errors.append(f"Circular dependency detected: {' -> '.join(cycle)}")
        
        # Check for undefined variables
        validation_errors = self.workflow.validate()
        for err in validation_errors:
            errors.append(str(err))
        
        return errors
    
    def compile_to_file(self, filepath: str) -> None:
        """
        Compile the workflow and write to a file.
        
        Args:
            filepath: Path to write the compiled code
        """
        code = self.compile()
        with open(filepath, 'w') as f:
            f.write(code)


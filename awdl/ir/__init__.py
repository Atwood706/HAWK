"""
AWDL Intermediate Representation Module - Layer 2: IR (Framework Agnostic)

This module contains the framework-agnostic intermediate representation
for AWDL workflows.
"""

from awdl.ir.workflow import Workflow
from awdl.ir.elements import Agent, Tool
from awdl.ir.variables import Variable, VariableType
from awdl.ir.conditions import Condition, WhileLoop, Expression
from awdl.ir.dependency import DependencyAnalyzer

__all__ = [
    "Workflow",
    "Agent",
    "Tool",
    "Variable",
    "VariableType",
    "Condition",
    "WhileLoop",
    "Expression",
    "DependencyAnalyzer",
]


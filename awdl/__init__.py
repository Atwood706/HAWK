"""
AWDL - Agentic Workflow Description Language

A domain-specific language for defining agent workflows.
"""

__version__ = "0.1.0"

from awdl.language.lexer import Lexer
from awdl.language.parser import Parser
from awdl.ir.workflow import Workflow
from awdl.compiler.base import BaseCompiler

__all__ = [
    "Lexer",
    "Parser",
    "Workflow",
    "BaseCompiler",
    "__version__",
]


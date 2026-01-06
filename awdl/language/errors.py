"""
AWDL Error Definitions

This module defines all error types used by the AWDL lexer and parser.
"""

from dataclasses import dataclass
from typing import Optional

from awdl.language.tokens import SourceLocation


class AWDLError(Exception):
    """Base class for all AWDL errors."""
    
    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        self.message = message
        self.location = location
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        if self.location:
            return f"{self.location}: {self.message}"
        return self.message


class AWDLSyntaxError(AWDLError):
    """Raised when there is a syntax error in the AWDL source code."""
    pass


class AWDLParseError(AWDLError):
    """Raised when there is a parsing error in the AWDL source code."""
    pass


class AWDLSemanticError(AWDLError):
    """Raised when there is a semantic error in the AWDL source code."""
    pass


class AWDLValidationError(AWDLError):
    """Raised when there is a validation error in the workflow."""
    pass


@dataclass
class ValidationError:
    """Represents a validation error with details."""
    
    message: str
    location: Optional[SourceLocation] = None
    severity: str = "error"  # "error", "warning", "info"
    
    def __repr__(self) -> str:
        loc_str = f" at {self.location}" if self.location else ""
        return f"[{self.severity.upper()}]{loc_str}: {self.message}"


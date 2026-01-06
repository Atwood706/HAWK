"""
AWDL Token Definitions

This module defines all token types used by the AWDL lexer.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class TokenType(Enum):
    """Enumeration of all token types in AWDL."""
    
    # Keywords
    IMPORT = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    START = auto()      # __start__
    END = auto()        # __end__
    
    # Type keywords
    TYPE_STRING = auto()
    TYPE_INT = auto()
    TYPE_FLOAT = auto()
    TYPE_BOOL = auto()
    TYPE_LIST = auto()
    TYPE_FILE = auto()
    TYPE_IMAGE = auto()
    
    # Literals
    STRING_LITERAL = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    BOOL_LITERAL = auto()
    
    # Identifiers
    IDENTIFIER = auto()
    
    # Operators
    COLON = auto()          # :
    COMMA = auto()          # ,
    SEMICOLON = auto()      # ;
    DOT = auto()            # .
    
    # Comparison operators
    EQ = auto()             # ==
    NE = auto()             # !=
    LT = auto()             # <
    GT = auto()             # >
    LE = auto()             # <=
    GE = auto()             # >=
    
    # Assignment
    ASSIGN = auto()         # =
    
    # Delimiters
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    
    # Special
    NEWLINE = auto()
    EOF = auto()
    COMMENT = auto()


# Mapping of keyword strings to token types
KEYWORDS: dict[str, TokenType] = {
    "import": TokenType.IMPORT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "__start__": TokenType.START,
    "__end__": TokenType.END,
    # Type keywords
    "string": TokenType.TYPE_STRING,
    "int": TokenType.TYPE_INT,
    "float": TokenType.TYPE_FLOAT,
    "bool": TokenType.TYPE_BOOL,
    "list": TokenType.TYPE_LIST,
    "file": TokenType.TYPE_FILE,
    "image": TokenType.TYPE_IMAGE,
    # Boolean literals
    "true": TokenType.BOOL_LITERAL,
    "false": TokenType.BOOL_LITERAL,
}

# Type keywords set for quick lookup
TYPE_KEYWORDS: set[TokenType] = {
    TokenType.TYPE_STRING,
    TokenType.TYPE_INT,
    TokenType.TYPE_FLOAT,
    TokenType.TYPE_BOOL,
    TokenType.TYPE_LIST,
    TokenType.TYPE_FILE,
    TokenType.TYPE_IMAGE,
}


@dataclass
class Token:
    """Represents a single token in the AWDL source code."""
    
    type: TokenType
    value: Any
    line: int
    column: int
    
    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"
    
    def is_type_keyword(self) -> bool:
        """Check if this token is a type keyword."""
        return self.type in TYPE_KEYWORDS
    
    def is_comparison_operator(self) -> bool:
        """Check if this token is a comparison operator."""
        return self.type in {
            TokenType.EQ,
            TokenType.NE,
            TokenType.LT,
            TokenType.GT,
            TokenType.LE,
            TokenType.GE,
        }


@dataclass
class SourceLocation:
    """Represents a location in the source code."""
    
    file: Optional[str]
    line: int
    column: int
    length: int = 1
    
    def __repr__(self) -> str:
        if self.file:
            return f"{self.file}:{self.line}:{self.column}"
        return f"line {self.line}, column {self.column}"


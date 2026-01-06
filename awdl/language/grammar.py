"""
AWDL Grammar Specification

This module contains the formal grammar specification for AWDL.
It serves as documentation and can be used for validation.
"""

# AWDL Grammar in EBNF-like notation
GRAMMAR = """
# AWDL Grammar Specification
# ==========================

# A program consists of optional imports, followed by __start__, 
# statements, and __end__
program            := import_stmt* "__start__" statement* "__end__"

# Import statement brings in agent/tool definitions
import_stmt        := "import" module_path

# Module path is a dotted identifier (e.g., hawk.agents.llm)
module_path        := IDENTIFIER ("." IDENTIFIER)*

# A statement can be a variable declaration, element invocation,
# or control flow statement
statement          := variable_decl
                    | element_invocation
                    | if_statement
                    | while_statement
                    | for_statement

# Variable declaration with optional default value
variable_decl      := type IDENTIFIER (":" expression)?

# Type keywords
type               := "string" | "int" | "float" | "bool" | "list" | "file" | "image"

# Element invocation - calls an Agent or Tool with I/O bindings
element_invocation := IDENTIFIER ":" "{" binding_list "}"

# List of bindings (port to variable mappings)
binding_list       := binding ("," binding)* ";"?

# Single binding: maps a port name to a variable name
binding            := IDENTIFIER ":" IDENTIFIER

# If statement with optional else branch
if_statement       := "if" condition ":" "{" statement* "}"
                      ("else" "{" statement* "}")?

# While loop
while_statement    := "while" condition ":" "{" statement* "}"

# For loop
for_statement      := "for" IDENTIFIER "in" expression ":" "{" statement* "}"

# Condition is a comparison expression
condition          := expression comparator expression

# Comparison operators
comparator         := "==" | "!=" | "<" | ">" | "<=" | ">="

# Expression can be a literal, variable reference, or function call
expression         := literal | IDENTIFIER | function_call

# Literals
literal            := STRING_LITERAL | INT_LITERAL | FLOAT_LITERAL | BOOL_LITERAL

# Function call (for future extension)
function_call      := IDENTIFIER "(" argument_list? ")"
argument_list      := expression ("," expression)*

# Token definitions
STRING_LITERAL     := '"' [^"]* '"' | "'" [^']* "'"
INT_LITERAL        := [0-9]+
FLOAT_LITERAL      := [0-9]+ "." [0-9]+
BOOL_LITERAL       := "true" | "false"
IDENTIFIER         := [a-zA-Z_][a-zA-Z0-9_]*

# Comments (ignored by parser)
COMMENT            := "#" [^\n]*

# Whitespace (ignored except for statement separation)
WHITESPACE         := [ \t\r\n]+
"""

# Keywords recognized by the lexer
KEYWORDS = [
    "import",
    "if",
    "else",
    "while",
    "for",
    "in",
    "__start__",
    "__end__",
]

# Type keywords
TYPE_KEYWORDS = [
    "string",
    "int",
    "float",
    "bool",
    "list",
    "file",
    "image",
]

# Comparison operators
COMPARISON_OPERATORS = [
    "==",
    "!=",
    "<",
    ">",
    "<=",
    ">=",
]

# Delimiters
DELIMITERS = [
    "{",
    "}",
    "(",
    ")",
    "[",
    "]",
    ":",
    ",",
    ";",
    ".",
]


def get_grammar() -> str:
    """Return the AWDL grammar specification."""
    return GRAMMAR


def print_grammar() -> None:
    """Print the AWDL grammar specification."""
    print(GRAMMAR)


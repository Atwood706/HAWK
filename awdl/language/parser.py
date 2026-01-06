"""
AWDL Parser

This module implements a recursive descent parser for the AWDL language.
It transforms tokens into IR objects (Workflow, Agent, Tool, Condition, etc.).
"""

from typing import List, Optional, Union, Any
from dataclasses import dataclass

from awdl.language.tokens import Token, TokenType, TYPE_KEYWORDS, SourceLocation
from awdl.language.lexer import Lexer
from awdl.language.errors import AWDLParseError
from awdl.ir.workflow import Workflow
from awdl.ir.variables import Variable, VariableType, Import
from awdl.ir.elements import Agent, Tool
from awdl.ir.conditions import Condition, WhileLoop, ForLoop, Expression, ComparisonOp


class Parser:
    """
    Recursive descent parser for AWDL.
    
    Transforms a stream of tokens into IR objects. Each grammar rule
    has a corresponding parsing method.
    """
    
    def __init__(self, tokens: List[Token], filename: Optional[str] = None):
        """
        Initialize the parser with tokens.
        
        Args:
            tokens: List of tokens from the lexer
            filename: Optional filename for error messages
        """
        self.tokens = tokens
        self.filename = filename
        self.pos = 0
        self.element_counter = 0  # For generating unique element IDs
    
    @classmethod
    def from_source(cls, source: str, filename: Optional[str] = None) -> "Parser":
        """
        Create a parser from source code.
        
        Args:
            source: AWDL source code
            filename: Optional filename for error messages
            
        Returns:
            A new Parser instance
        """
        lexer = Lexer(source, filename)
        tokens = lexer.tokenize()
        return cls(tokens, filename)
    
    @property
    def current_token(self) -> Token:
        """Get the current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[self.pos]
    
    def peek(self, offset: int = 1) -> Token:
        """Look ahead by offset tokens."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[pos]
    
    def advance(self) -> Token:
        """Advance to the next token and return the current one."""
        token = self.current_token
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        """
        Expect the current token to be of a specific type.
        
        Args:
            token_type: The expected token type
            
        Returns:
            The current token
            
        Raises:
            AWDLParseError: If the token type doesn't match
        """
        if self.current_token.type != token_type:
            raise self.error(
                f"Expected {token_type.name}, got {self.current_token.type.name}"
            )
        return self.advance()
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if the current token matches any of the given types."""
        return self.current_token.type in token_types
    
    def error(self, message: str) -> AWDLParseError:
        """Create a parse error at the current position."""
        location = SourceLocation(
            file=self.filename,
            line=self.current_token.line,
            column=self.current_token.column,
        )
        return AWDLParseError(message, location)
    
    def generate_element_id(self, base_name: str) -> str:
        """Generate a unique element ID."""
        self.element_counter += 1
        return f"{base_name}_{self.element_counter}"
    
    # ==================== Grammar Rule Parsers ====================
    
    def parse(self) -> Workflow:
        """
        Parse the entire AWDL program.
        
        Grammar: program := import_stmt* "__start__" statement* "__end__"
        
        Returns:
            A Workflow object representing the parsed program
        """
        imports = []
        variables = []
        elements = []
        
        # Parse import statements
        while self.match(TokenType.IMPORT):
            imports.append(self.parse_import())
        
        # Expect __start__
        self.expect(TokenType.START)
        
        # Parse statements until __end__
        while not self.match(TokenType.END, TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                if isinstance(stmt, Variable):
                    variables.append(stmt)
                else:
                    elements.append(stmt)
        
        # Expect __end__
        self.expect(TokenType.END)
        
        # Create workflow with a default name
        workflow = Workflow(
            name="main",
            version="1.0",
            imports=imports,
            variables=variables,
            elements=elements,
        )
        
        return workflow
    
    def parse_import(self) -> Import:
        """
        Parse an import statement.
        
        Grammar: import_stmt := "import" module_path
        """
        self.expect(TokenType.IMPORT)
        
        # Parse module path (dotted identifier)
        parts = []
        token = self.expect(TokenType.IDENTIFIER)
        parts.append(token.value)
        
        while self.match(TokenType.DOT):
            self.advance()  # Skip dot
            token = self.expect(TokenType.IDENTIFIER)
            parts.append(token.value)
        
        module_path = ".".join(parts)
        return Import(module_path=module_path, line=token.line, column=token.column)
    
    def parse_statement(self) -> Optional[Union[Variable, Agent, Tool, Condition, WhileLoop, ForLoop]]:
        """
        Parse a statement.
        
        Grammar: statement := variable_decl | element_invocation | if_statement | loop_statement
        """
        # Check for type keyword (variable declaration)
        if self.current_token.is_type_keyword():
            return self.parse_variable_declaration()
        
        # Check for if statement
        if self.match(TokenType.IF):
            return self.parse_if_statement()
        
        # Check for while loop
        if self.match(TokenType.WHILE):
            return self.parse_while_loop()
        
        # Check for for loop
        if self.match(TokenType.FOR):
            return self.parse_for_loop()
        
        # Check for element invocation (identifier followed by colon and brace)
        if self.match(TokenType.IDENTIFIER):
            if self.peek().type == TokenType.COLON:
                return self.parse_element_invocation()
        
        # Unknown statement - skip
        raise self.error(f"Unexpected token: {self.current_token.type.name}")
    
    def parse_variable_declaration(self) -> Variable:
        """
        Parse a variable declaration.
        
        Grammar: variable_decl := type identifier (":" expression)?
        """
        # Parse type
        type_token = self.advance()
        var_type = VariableType.from_string(type_token.value)
        
        # Parse variable name
        name_token = self.expect(TokenType.IDENTIFIER)
        var_name = name_token.value
        
        # Check for default value
        default_value = None
        if self.match(TokenType.COLON):
            self.advance()  # Skip colon
            default_value = self.parse_literal_value()
        
        return Variable(
            name=var_name,
            var_type=var_type,
            default_value=default_value,
            line=name_token.line,
            column=name_token.column,
        )
    
    def parse_literal_value(self) -> Any:
        """Parse a literal value (string, number, bool)."""
        token = self.current_token
        
        if token.type == TokenType.STRING_LITERAL:
            self.advance()
            return token.value
        elif token.type == TokenType.INT_LITERAL:
            self.advance()
            return token.value
        elif token.type == TokenType.FLOAT_LITERAL:
            self.advance()
            return token.value
        elif token.type == TokenType.BOOL_LITERAL:
            self.advance()
            return token.value
        else:
            raise self.error(f"Expected literal value, got {token.type.name}")
    
    def parse_element_invocation(self) -> Union[Agent, Tool]:
        """
        Parse an element invocation (agent or tool call).
        
        Grammar: element_invocation := identifier ":" "{" binding_list "}"
        """
        # Get element type/name
        name_token = self.expect(TokenType.IDENTIFIER)
        element_type = name_token.value
        
        # Expect colon
        self.expect(TokenType.COLON)
        
        # Expect opening brace
        self.expect(TokenType.LBRACE)
        
        # Parse bindings
        inputs, outputs = self.parse_binding_list()
        
        # Expect closing brace
        self.expect(TokenType.RBRACE)
        
        # Generate unique ID
        element_id = self.generate_element_id(element_type)
        
        # Determine if this is an agent or tool based on the type name
        # For now, we'll use a simple heuristic: if it ends with "_agent" or contains "llm", it's an agent
        # Otherwise, it's a tool. This can be refined later with the builtins registry.
        if "agent" in element_type.lower() or "llm" in element_type.lower() or "router" in element_type.lower():
            return Agent(
                id=element_id,
                agent_type=element_type,
                inputs=inputs,
                outputs=outputs,
                line=name_token.line,
                column=name_token.column,
            )
        else:
            return Tool(
                id=element_id,
                tool_type=element_type,
                inputs=inputs,
                outputs=outputs,
                line=name_token.line,
                column=name_token.column,
            )
    
    def parse_binding_list(self) -> tuple[dict, dict]:
        """
        Parse a list of bindings.
        
        Grammar: binding_list := binding ("," binding)* ";"?
        
        Returns:
            Tuple of (inputs, outputs) dictionaries
        """
        inputs = {}
        outputs = {}
        
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            port_name, var_name, is_output = self.parse_binding()
            
            if is_output:
                outputs[port_name] = var_name
            else:
                inputs[port_name] = var_name
            
            # Check for comma or semicolon
            if self.match(TokenType.COMMA):
                self.advance()
            elif self.match(TokenType.SEMICOLON):
                self.advance()
                break
            elif not self.match(TokenType.RBRACE):
                # Allow bindings without explicit comma separator
                pass
        
        return inputs, outputs
    
    def parse_binding(self) -> tuple[str, str, bool]:
        """
        Parse a single binding.
        
        Grammar: binding := port_name ":" variable_name
        
        Returns:
            Tuple of (port_name, variable_name, is_output)
            
        Note: We determine input vs output by convention:
        - If the port name is "response", "output", "result", "results" -> output
        - Otherwise -> input
        """
        # Parse port name
        port_token = self.expect(TokenType.IDENTIFIER)
        port_name = port_token.value
        
        # Expect colon
        self.expect(TokenType.COLON)
        
        # Parse variable name
        var_token = self.expect(TokenType.IDENTIFIER)
        var_name = var_token.value
        
        # Determine if this is an output binding
        output_ports = {"response", "output", "result", "results", "answer", "final_answer"}
        is_output = port_name.lower() in output_ports
        
        return port_name, var_name, is_output
    
    def parse_if_statement(self) -> Condition:
        """
        Parse an if statement.
        
        Grammar: if_statement := "if" condition ":" "{" statement* "}" ("else" "{" statement* "}")?
        """
        start_token = self.expect(TokenType.IF)
        
        # Parse condition expression
        condition_expr = self.parse_condition_expression()
        
        # Expect colon (optional in some cases)
        if self.match(TokenType.COLON):
            self.advance()
        
        # Expect opening brace
        self.expect(TokenType.LBRACE)
        
        # Parse then branch
        then_branch = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None and not isinstance(stmt, Variable):
                then_branch.append(stmt)
        
        # Expect closing brace
        self.expect(TokenType.RBRACE)
        
        # Check for else branch
        else_branch = None
        if self.match(TokenType.ELSE):
            self.advance()  # Skip 'else'
            self.expect(TokenType.LBRACE)
            
            else_branch = []
            while not self.match(TokenType.RBRACE, TokenType.EOF):
                stmt = self.parse_statement()
                if stmt is not None and not isinstance(stmt, Variable):
                    else_branch.append(stmt)
            
            self.expect(TokenType.RBRACE)
        
        # Generate unique ID
        condition_id = self.generate_element_id("condition")
        
        return Condition(
            id=condition_id,
            expression=condition_expr,
            then_branch=then_branch,
            else_branch=else_branch,
            line=start_token.line,
            column=start_token.column,
        )
    
    def parse_condition_expression(self) -> Expression:
        """
        Parse a condition expression.
        
        Grammar: condition := expression comparator expression
        """
        # Parse left side
        left = self.parse_simple_expression()
        
        # Parse comparison operator
        if not self.current_token.is_comparison_operator():
            raise self.error(f"Expected comparison operator, got {self.current_token.type.name}")
        
        op_token = self.advance()
        op = ComparisonOp.from_string(op_token.value)
        
        # Parse right side
        right = self.parse_simple_expression()
        
        return Expression.from_comparison(left, op, right)
    
    def parse_simple_expression(self) -> Expression:
        """
        Parse a simple expression (literal or variable reference).
        
        Grammar: expression := literal | identifier
        """
        token = self.current_token
        
        if token.type == TokenType.STRING_LITERAL:
            self.advance()
            return Expression.from_literal(token.value)
        elif token.type == TokenType.INT_LITERAL:
            self.advance()
            return Expression.from_literal(token.value)
        elif token.type == TokenType.FLOAT_LITERAL:
            self.advance()
            return Expression.from_literal(token.value)
        elif token.type == TokenType.BOOL_LITERAL:
            self.advance()
            return Expression.from_literal(token.value)
        elif token.type == TokenType.IDENTIFIER:
            self.advance()
            return Expression.from_variable(token.value)
        else:
            raise self.error(f"Expected expression, got {token.type.name}")
    
    def parse_while_loop(self) -> WhileLoop:
        """
        Parse a while loop.
        
        Grammar: loop_statement := "while" condition ":" "{" statement* "}"
        """
        start_token = self.expect(TokenType.WHILE)
        
        # Parse condition
        condition_expr = self.parse_condition_expression()
        
        # Expect colon (optional)
        if self.match(TokenType.COLON):
            self.advance()
        
        # Expect opening brace
        self.expect(TokenType.LBRACE)
        
        # Parse body
        body = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None and not isinstance(stmt, Variable):
                body.append(stmt)
        
        # Expect closing brace
        self.expect(TokenType.RBRACE)
        
        # Generate unique ID
        loop_id = self.generate_element_id("while")
        
        return WhileLoop(
            id=loop_id,
            condition=condition_expr,
            body=body,
            line=start_token.line,
            column=start_token.column,
        )
    
    def parse_for_loop(self) -> ForLoop:
        """
        Parse a for loop.
        
        Grammar: loop_statement := "for" identifier "in" expression ":" "{" statement* "}"
        """
        start_token = self.expect(TokenType.FOR)
        
        # Parse iterator variable
        iter_token = self.expect(TokenType.IDENTIFIER)
        iterator_var = iter_token.value
        
        # Expect 'in'
        self.expect(TokenType.IN)
        
        # Parse iterable expression
        iterable = self.parse_simple_expression()
        
        # Expect colon (optional)
        if self.match(TokenType.COLON):
            self.advance()
        
        # Expect opening brace
        self.expect(TokenType.LBRACE)
        
        # Parse body
        body = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None and not isinstance(stmt, Variable):
                body.append(stmt)
        
        # Expect closing brace
        self.expect(TokenType.RBRACE)
        
        # Generate unique ID
        loop_id = self.generate_element_id("for")
        
        return ForLoop(
            id=loop_id,
            iterator_var=iterator_var,
            iterable=iterable,
            body=body,
            line=start_token.line,
            column=start_token.column,
        )


def parse_file(filepath: str) -> Workflow:
    """
    Parse an AWDL file.
    
    Args:
        filepath: Path to the .awdl file
        
    Returns:
        A Workflow object
    """
    with open(filepath, 'r') as f:
        source = f.read()
    
    parser = Parser.from_source(source, filepath)
    return parser.parse()


def parse_string(source: str, filename: Optional[str] = None) -> Workflow:
    """
    Parse AWDL source code from a string.
    
    Args:
        source: AWDL source code
        filename: Optional filename for error messages
        
    Returns:
        A Workflow object
    """
    parser = Parser.from_source(source, filename)
    return parser.parse()


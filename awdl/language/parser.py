"""
Parser for rebuilt AWDL.
"""

from __future__ import annotations

from typing import Any, List, Optional, Union

from awdl.ir.builtins import BUILTIN_REGISTRY
from awdl.ir.conditions import ComparisonOp, Condition, Expression, ForLoop, WhileLoop
from awdl.ir.elements import Agent, FunctionCall, FunctionDefinition, ProfileDefinition, Tool
from awdl.ir.variables import Import, Variable, VariableType
from awdl.ir.workflow import Workflow
from awdl.language.errors import AWDLParseError
from awdl.language.lexer import Lexer
from awdl.language.tokens import SourceLocation, Token, TokenType


LEGACY_AGENT_NAMES = {"llm_agent", "deepseek_agent", "qwen_agent", "router_agent", "fallback_agent"}


class Parser:
    def __init__(self, tokens: List[Token], filename: Optional[str] = None):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0
        self.element_counter = 0
        self.profile_defs: dict[str, ProfileDefinition] = {}
        self.function_defs: dict[str, FunctionDefinition] = {}

    @classmethod
    def from_source(cls, source: str, filename: Optional[str] = None) -> "Parser":
        return cls(Lexer(source, filename).tokenize(), filename)

    @property
    def current_token(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]

    def advance(self) -> Token:
        token = self.current_token
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        if self.current_token.type != token_type:
            raise self.error(f"Expected {token_type.name}, got {self.current_token.type.name}")
        return self.advance()

    def match(self, *token_types: TokenType) -> bool:
        return self.current_token.type in token_types

    def error(self, message: str) -> AWDLParseError:
        location = SourceLocation(
            file=self.filename,
            line=self.current_token.line,
            column=self.current_token.column,
        )
        return AWDLParseError(message, location)

    def generate_element_id(self, base_name: str) -> str:
        self.element_counter += 1
        return f"{base_name}_{self.element_counter}"

    def parse(self) -> Workflow:
        imports: list[Import] = []

        while self.match(TokenType.IMPORT):
            imports.append(self.parse_import())

        while self.match(TokenType.PROFILE, TokenType.FUNCTION):
            if self.match(TokenType.PROFILE):
                profile = self.parse_profile_definition()
                self.profile_defs[profile.name] = profile
            else:
                function = self.parse_function_definition()
                self.function_defs[function.name] = function

        self.expect(TokenType.START)

        variables: list[Variable] = []
        elements = []
        while not self.match(TokenType.END, TokenType.EOF):
            stmt = self.parse_statement()
            if isinstance(stmt, Variable):
                variables.append(stmt)
            else:
                elements.append(stmt)

        self.expect(TokenType.END)

        return Workflow(
            name="main",
            version="1.0",
            imports=imports,
            profiles=dict(self.profile_defs),
            functions=dict(self.function_defs),
            variables=variables,
            elements=elements,
            source_path=self.filename,
        )

    def parse_import(self) -> Import:
        self.expect(TokenType.IMPORT)
        parts = [self.expect(TokenType.IDENTIFIER).value]
        while self.match(TokenType.DOT):
            self.advance()
            parts.append(self.expect(TokenType.IDENTIFIER).value)
        return Import(module_path=".".join(parts))

    def parse_profile_definition(self) -> ProfileDefinition:
        start = self.expect(TokenType.PROFILE)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LBRACE)

        config: dict[str, Any] = {}
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            key = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.COLON)
            config[key] = self.parse_config_value()
            if self.match(TokenType.COMMA):
                self.advance()

        self.expect(TokenType.RBRACE)
        return ProfileDefinition(name=name, config=config, line=start.line, column=start.column)

    def parse_function_definition(self) -> FunctionDefinition:
        start = self.expect(TokenType.FUNCTION)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LPAREN)
        inputs = self.parse_name_list(until=TokenType.SEMICOLON)
        outputs: list[str] = []
        if self.match(TokenType.SEMICOLON):
            self.advance()
            outputs = self.parse_name_list(until=TokenType.RPAREN)
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)

        variables: list[Variable] = []
        elements: list[Any] = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            stmt = self.parse_statement()
            if isinstance(stmt, Variable):
                variables.append(stmt)
            else:
                elements.append(stmt)

        self.expect(TokenType.RBRACE)
        return FunctionDefinition(
            name=name,
            inputs=inputs,
            outputs=outputs,
            variables=variables,
            elements=elements,
            line=start.line,
            column=start.column,
        )

    def parse_name_list(self, until: TokenType) -> list[str]:
        names: list[str] = []
        while not self.match(until, TokenType.EOF):
            names.append(self.expect_name_token().value)
            if self.match(TokenType.COMMA):
                self.advance()
            else:
                break
        return names

    def expect_name_token(self) -> Token:
        if self.match(TokenType.IDENTIFIER, TokenType.PROFILE, TokenType.FUNCTION):
            return self.advance()
        raise self.error(f"Expected IDENTIFIER, got {self.current_token.type.name}")

    def parse_statement(self) -> Union[Variable, Agent, Tool, FunctionCall, Condition, WhileLoop, ForLoop]:
        if self.current_token.is_type_keyword():
            return self.parse_variable_declaration()
        if self.match(TokenType.IF):
            return self.parse_if_statement()
        if self.match(TokenType.WHILE):
            return self.parse_while_loop()
        if self.match(TokenType.FOR):
            return self.parse_for_loop()
        if self.match(TokenType.IDENTIFIER) and self.peek().type == TokenType.COLON:
            return self.parse_element_invocation()
        raise self.error(f"Unexpected token: {self.current_token.type.name}")

    def parse_variable_declaration(self) -> Variable:
        type_token = self.advance()
        name_token = self.expect(TokenType.IDENTIFIER)
        default_value = None
        if self.match(TokenType.COLON):
            self.advance()
            default_value = self.parse_literal_value()
        return Variable(
            name=name_token.value,
            var_type=VariableType.from_string(type_token.value),
            default_value=default_value,
            line=name_token.line,
            column=name_token.column,
        )

    def parse_literal_value(self) -> Any:
        token = self.current_token
        if token.type in (
            TokenType.STRING_LITERAL,
            TokenType.INT_LITERAL,
            TokenType.FLOAT_LITERAL,
            TokenType.BOOL_LITERAL,
        ):
            self.advance()
            return token.value
        raise self.error(f"Expected literal value, got {token.type.name}")

    def parse_config_value(self) -> Any:
        if self.match(
            TokenType.STRING_LITERAL,
            TokenType.INT_LITERAL,
            TokenType.FLOAT_LITERAL,
            TokenType.BOOL_LITERAL,
        ):
            return self.parse_literal_value()
        if self.match(TokenType.IDENTIFIER):
            return self.advance().value
        if self.match(TokenType.LBRACKET):
            return self.parse_list_literal()
        raise self.error(f"Expected config value, got {self.current_token.type.name}")

    def parse_list_literal(self) -> list[Any]:
        values: list[Any] = []
        self.expect(TokenType.LBRACKET)
        while not self.match(TokenType.RBRACKET, TokenType.EOF):
            values.append(self.parse_config_value())
            if self.match(TokenType.COMMA):
                self.advance()
            else:
                break
        self.expect(TokenType.RBRACKET)
        return values

    def parse_element_invocation(self) -> Union[Agent, Tool, FunctionCall]:
        token = self.expect(TokenType.IDENTIFIER)
        element_name = token.value

        if element_name in LEGACY_AGENT_NAMES:
            raise self.error(f"Legacy agent '{element_name}' is no longer supported; use 'agent' with a profile")

        self.expect(TokenType.COLON)
        self.expect(TokenType.LBRACE)

        if element_name == "agent":
            element = self.parse_agent_invocation(token)
        elif element_name in self.function_defs:
            element = self.parse_function_call(token, element_name)
        elif BUILTIN_REGISTRY.exists(element_name):
            element = self.parse_tool_invocation(token, element_name)
        else:
            raise self.error(f"Unknown callable '{element_name}'")

        self.expect(TokenType.RBRACE)
        return element

    def parse_agent_invocation(self, token: Token) -> Agent:
        inputs: dict[str, str] = {}
        outputs: dict[str, str] = {}
        config: dict[str, Any] = {}

        while not self.match(TokenType.RBRACE, TokenType.EOF):
            port_name = self.expect_name_token().value
            self.expect(TokenType.COLON)
            if port_name == "profile":
                config["profile"] = self.parse_config_value()
            elif port_name == "skills":
                config["skills"] = self.parse_list_literal()
            elif port_name == "tools":
                config["tools"] = self.parse_list_literal()
            else:
                value = self.expect(TokenType.IDENTIFIER).value
                if port_name in {"response", "output", "answer", "final_answer"}:
                    outputs[port_name] = value
                else:
                    inputs[port_name] = value
            if self.match(TokenType.COMMA):
                self.advance()

        return Agent(
            id=self.generate_element_id("agent"),
            inputs=inputs,
            outputs=outputs,
            config=config,
            line=token.line,
            column=token.column,
        )

    def parse_function_call(self, token: Token, function_name: str) -> FunctionCall:
        definition = self.function_defs[function_name]
        inputs, outputs = self.parse_bindings(definition.outputs)
        return FunctionCall(
            id=self.generate_element_id(function_name),
            function_name=function_name,
            inputs=inputs,
            outputs=outputs,
            line=token.line,
            column=token.column,
        )

    def parse_tool_invocation(self, token: Token, tool_name: str) -> Tool:
        output_names = set(BUILTIN_REGISTRY.get(tool_name).output_names)
        inputs, outputs = self.parse_bindings(output_names)
        return Tool(
            id=self.generate_element_id(tool_name),
            tool_type=tool_name,
            inputs=inputs,
            outputs=outputs,
            line=token.line,
            column=token.column,
        )

    def parse_bindings(self, output_names: set[str]) -> tuple[dict[str, str], dict[str, str]]:
        inputs: dict[str, str] = {}
        outputs: dict[str, str] = {}
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            port_name = self.expect_name_token().value
            self.expect(TokenType.COLON)
            var_name = self.expect(TokenType.IDENTIFIER).value
            if port_name in output_names:
                outputs[port_name] = var_name
            else:
                inputs[port_name] = var_name
            if self.match(TokenType.COMMA):
                self.advance()
        return inputs, outputs

    def parse_if_statement(self) -> Condition:
        start_token = self.expect(TokenType.IF)
        condition_expr = self.parse_condition_expression()
        if self.match(TokenType.COLON):
            self.advance()
        self.expect(TokenType.LBRACE)
        then_branch = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            stmt = self.parse_statement()
            if not isinstance(stmt, Variable):
                then_branch.append(stmt)
        self.expect(TokenType.RBRACE)

        else_branch = None
        if self.match(TokenType.ELSE):
            self.advance()
            self.expect(TokenType.LBRACE)
            else_branch = []
            while not self.match(TokenType.RBRACE, TokenType.EOF):
                stmt = self.parse_statement()
                if not isinstance(stmt, Variable):
                    else_branch.append(stmt)
            self.expect(TokenType.RBRACE)

        return Condition(
            id=self.generate_element_id("condition"),
            expression=condition_expr,
            then_branch=then_branch,
            else_branch=else_branch,
            line=start_token.line,
            column=start_token.column,
        )

    def parse_condition_expression(self) -> Expression:
        left = self.parse_simple_expression()
        if not self.current_token.is_comparison_operator():
            raise self.error(f"Expected comparison operator, got {self.current_token.type.name}")
        op = ComparisonOp.from_string(self.advance().value)
        right = self.parse_simple_expression()
        return Expression.from_comparison(left, op, right)

    def parse_simple_expression(self) -> Expression:
        token = self.current_token
        if token.type in (
            TokenType.STRING_LITERAL,
            TokenType.INT_LITERAL,
            TokenType.FLOAT_LITERAL,
            TokenType.BOOL_LITERAL,
        ):
            self.advance()
            return Expression.from_literal(token.value)
        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return Expression.from_variable(token.value)
        raise self.error(f"Expected expression, got {token.type.name}")

    def parse_while_loop(self) -> WhileLoop:
        start_token = self.expect(TokenType.WHILE)
        condition_expr = self.parse_condition_expression()
        if self.match(TokenType.COLON):
            self.advance()
        self.expect(TokenType.LBRACE)
        body = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            stmt = self.parse_statement()
            if not isinstance(stmt, Variable):
                body.append(stmt)
        self.expect(TokenType.RBRACE)
        return WhileLoop(
            id=self.generate_element_id("while"),
            condition=condition_expr,
            body=body,
            line=start_token.line,
            column=start_token.column,
        )

    def parse_for_loop(self) -> ForLoop:
        start_token = self.expect(TokenType.FOR)
        iterator_var = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.IN)
        iterable = self.parse_simple_expression()
        if self.match(TokenType.COLON):
            self.advance()
        self.expect(TokenType.LBRACE)
        body = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            stmt = self.parse_statement()
            if not isinstance(stmt, Variable):
                body.append(stmt)
        self.expect(TokenType.RBRACE)
        return ForLoop(
            id=self.generate_element_id("for"),
            iterator_var=iterator_var,
            iterable=iterable,
            body=body,
            line=start_token.line,
            column=start_token.column,
        )


def parse_file(filepath: str) -> Workflow:
    with open(filepath, "r", encoding="utf-8") as handle:
        parser = Parser.from_source(handle.read(), filepath)
    return parser.parse()


def parse_string(source: str, filename: Optional[str] = None) -> Workflow:
    return Parser.from_source(source, filename).parse()

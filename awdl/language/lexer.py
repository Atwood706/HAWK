"""
AWDL Lexer (Tokenizer)

This module implements a hand-written lexer for the AWDL language.
It provides better error messages and control compared to generated lexers.
"""

from typing import Iterator, Optional

from awdl.language.tokens import Token, TokenType, KEYWORDS, SourceLocation, SINGLE_CHAR_TOKENS, TWO_CHAR_TOKENS
from awdl.language.errors import AWDLSyntaxError


class Lexer:
    """
    Hand-written lexer for AWDL source code.
    
    Performs character-by-character scanning with lookahead to produce tokens.
    """
    
    def __init__(self, source: str, filename: Optional[str] = None):
        """
        Initialize the lexer with source code.
        
        Args:
            source: The AWDL source code to tokenize
            filename: Optional filename for error messages
        """
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
    
    @property
    def current_char(self) -> Optional[str]:
        """Get the current character, or None if at end."""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek(self, offset: int = 1) -> Optional[str]:
        """Look ahead by offset characters."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> Optional[str]:
        """Advance to the next character and return it."""
        char = self.current_char
        if char is not None:
            self.pos += 1
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return char
    
    def skip_whitespace(self) -> None:
        """Skip whitespace characters (except newlines which are tokens)."""
        while self.current_char is not None and self.current_char in ' \t\r':
            self.advance()
    
    def skip_comment(self) -> None:
        """Skip a comment until end of line."""
        while self.current_char is not None and self.current_char != '\n':
            self.advance()
    
    def make_token(self, token_type: TokenType, value: any = None) -> Token:
        """Create a token at the current position."""
        return Token(
            type=token_type,
            value=value,
            line=self.line,
            column=self.column,
        )
    
    def error(self, message: str) -> AWDLSyntaxError:
        """Create a syntax error at the current position."""
        location = SourceLocation(
            file=self.filename,
            line=self.line,
            column=self.column,
        )
        return AWDLSyntaxError(message, location)
    
    def read_string(self, quote_char: str) -> Token:
        """Read a string literal."""
        start_line = self.line
        start_column = self.column
        self.advance()  # Skip opening quote
        
        value = []
        while self.current_char is not None and self.current_char != quote_char:
            if self.current_char == '\\':
                self.advance()
                escape_char = self.current_char
                if escape_char is None:
                    raise self.error("Unterminated string literal")
                # Handle escape sequences
                escape_map = {
                    'n': '\n',
                    't': '\t',
                    'r': '\r',
                    '\\': '\\',
                    "'": "'",
                    '"': '"',
                }
                if escape_char in escape_map:
                    value.append(escape_map[escape_char])
                else:
                    value.append(escape_char)
                self.advance()
            elif self.current_char == '\n':
                raise self.error("Unterminated string literal (newline in string)")
            else:
                value.append(self.current_char)
                self.advance()
        
        if self.current_char is None:
            raise self.error("Unterminated string literal")
        
        self.advance()  # Skip closing quote
        
        return Token(
            type=TokenType.STRING_LITERAL,
            value=''.join(value),
            line=start_line,
            column=start_column,
        )
    
    def read_number(self) -> Token:
        """Read a number literal (int or float)."""
        start_line = self.line
        start_column = self.column
        
        value = []
        has_dot = False
        
        while self.current_char is not None:
            if self.current_char.isdigit():
                value.append(self.current_char)
                self.advance()
            elif self.current_char == '.' and not has_dot:
                # Check if next char is a digit (to distinguish from method calls)
                if self.peek() is not None and self.peek().isdigit():
                    has_dot = True
                    value.append(self.current_char)
                    self.advance()
                else:
                    break
            else:
                break
        
        value_str = ''.join(value)
        if has_dot:
            return Token(
                type=TokenType.FLOAT_LITERAL,
                value=float(value_str),
                line=start_line,
                column=start_column,
            )
        else:
            return Token(
                type=TokenType.INT_LITERAL,
                value=int(value_str),
                line=start_line,
                column=start_column,
            )
    
    def read_identifier_or_keyword(self) -> Token:
        """Read an identifier or keyword."""
        start_line = self.line
        start_column = self.column
        
        value = []
        while self.current_char is not None and (
            self.current_char.isalnum() or self.current_char == '_'
        ):
            value.append(self.current_char)
            self.advance()
        
        value_str = ''.join(value)
        
        # Check if it's a keyword
        if value_str in KEYWORDS:
            token_type = KEYWORDS[value_str]
            # For boolean literals, convert to actual bool
            if token_type == TokenType.BOOL_LITERAL:
                return Token(
                    type=token_type,
                    value=value_str == "true",
                    line=start_line,
                    column=start_column,
                )
            return Token(
                type=token_type,
                value=value_str,
                line=start_line,
                column=start_column,
            )
        
        return Token(
            type=TokenType.IDENTIFIER,
            value=value_str,
            line=start_line,
            column=start_column,
        )
    
    def next_token(self) -> Token:
        """Get the next token from the source."""
        self.skip_whitespace()
        
        if self.current_char is None:
            return self.make_token(TokenType.EOF)
        
        # Handle comments
        if self.current_char == '#':
            self.skip_comment()
            return self.next_token()
        
        # Handle newlines
        if self.current_char == '\n':
            token = self.make_token(TokenType.NEWLINE, '\n')
            self.advance()
            return token
        
        # Handle string literals
        if self.current_char in '"\'':
            return self.read_string(self.current_char)
        
        # Handle numbers
        if self.current_char.isdigit():
            return self.read_number()
        
        # Handle identifiers and keywords
        if self.current_char.isalpha() or self.current_char == '_':
            return self.read_identifier_or_keyword()
        
        # Handle operators and delimiters
        char = self.current_char
        start_column = self.column
        
        # Two-character operators (check first to avoid partial match)
        two_char = char + (self.peek() or '')
        if two_char in TWO_CHAR_TOKENS:
            self.advance()
            self.advance()
            return Token(TWO_CHAR_TOKENS[two_char], two_char, self.line, start_column)
        
        # Single-character operators and delimiters
        if char in SINGLE_CHAR_TOKENS:
            token = Token(SINGLE_CHAR_TOKENS[char], char, self.line, start_column)
            self.advance()
            return token
        
        raise self.error(f"Unexpected character: {char!r}")
    
    def tokenize(self) -> list[Token]:
        """
        Tokenize the entire source code.
        
        Returns:
            A list of tokens, ending with an EOF token.
        """
        tokens = []
        while True:
            token = self.next_token()
            # Skip newlines for now (can be used for statement termination later)
            if token.type != TokenType.NEWLINE:
                tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens
    
    def __iter__(self) -> Iterator[Token]:
        """Iterate over tokens in the source."""
        while True:
            token = self.next_token()
            yield token
            if token.type == TokenType.EOF:
                break


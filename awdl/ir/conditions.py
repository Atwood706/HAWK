"""
AWDL Condition Definitions

This module defines Condition and loop elements for control flow in AWDL.
"""

from dataclasses import dataclass, field
from typing import List, Set, Optional, Union, Any
from enum import Enum, auto

from awdl.ir.elements import Element, Agent, Tool


class ComparisonOp(Enum):
    """Comparison operators for conditions."""
    
    EQ = auto()   # ==
    NE = auto()   # !=
    LT = auto()   # <
    GT = auto()   # >
    LE = auto()   # <=
    GE = auto()   # >=
    
    def to_python(self) -> str:
        """Convert to Python operator string."""
        return {
            ComparisonOp.EQ: "==",
            ComparisonOp.NE: "!=",
            ComparisonOp.LT: "<",
            ComparisonOp.GT: ">",
            ComparisonOp.LE: "<=",
            ComparisonOp.GE: ">=",
        }[self]
    
    @classmethod
    def from_string(cls, op_str: str) -> "ComparisonOp":
        """Convert from string to ComparisonOp."""
        mapping = {
            "==": cls.EQ,
            "!=": cls.NE,
            "<": cls.LT,
            ">": cls.GT,
            "<=": cls.LE,
            ">=": cls.GE,
        }
        return mapping[op_str]


@dataclass
class Expression:
    """
    Represents an expression in AWDL.
    
    Expressions can be literals, variable references, or comparisons.
    """
    
    # For simple expressions (literals or variable references)
    value: Optional[Any] = None
    is_variable: bool = False
    variable_name: Optional[str] = None
    
    # For comparison expressions
    left: Optional["Expression"] = None
    operator: Optional[ComparisonOp] = None
    right: Optional["Expression"] = None
    
    def is_comparison(self) -> bool:
        """Check if this is a comparison expression."""
        return self.operator is not None
    
    def is_literal(self) -> bool:
        """Check if this is a literal value."""
        return not self.is_variable and not self.is_comparison()
    
    def get_referenced_vars(self) -> Set[str]:
        """Get all variable names referenced in this expression."""
        vars_set: Set[str] = set()
        
        if self.is_variable and self.variable_name:
            vars_set.add(self.variable_name)
        
        if self.left:
            vars_set.update(self.left.get_referenced_vars())
        if self.right:
            vars_set.update(self.right.get_referenced_vars())
        
        return vars_set
    
    def to_python(self) -> str:
        """Convert this expression to Python code."""
        if self.is_comparison():
            left_str = self.left.to_python() if self.left else ""
            right_str = self.right.to_python() if self.right else ""
            op_str = self.operator.to_python() if self.operator else ""
            return f"{left_str} {op_str} {right_str}"
        elif self.is_variable:
            return f'state["{self.variable_name}"]'
        else:
            # Literal value
            if isinstance(self.value, str):
                return f'"{self.value}"'
            return str(self.value)
    
    @classmethod
    def from_literal(cls, value: Any) -> "Expression":
        """Create an expression from a literal value."""
        return cls(value=value, is_variable=False)
    
    @classmethod
    def from_variable(cls, var_name: str) -> "Expression":
        """Create an expression from a variable reference."""
        return cls(is_variable=True, variable_name=var_name)
    
    @classmethod
    def from_comparison(
        cls, left: "Expression", op: ComparisonOp, right: "Expression"
    ) -> "Expression":
        """Create a comparison expression."""
        return cls(left=left, operator=op, right=right)
    
    def __repr__(self) -> str:
        if self.is_comparison():
            return f"({self.left} {self.operator.to_python()} {self.right})"
        elif self.is_variable:
            return f"${self.variable_name}"
        else:
            return repr(self.value)


@dataclass
class Condition(Element):
    """
    A Condition element in AWDL.
    
    Conditions control the flow of execution based on variable values.
    They have a then_branch and an optional else_branch.
    
    Attributes:
        id: Unique identifier for this condition
        expression: The condition expression to evaluate
        then_branch: Elements to execute if condition is true
        else_branch: Optional elements to execute if condition is false
    """
    
    id: str
    expression: Expression
    then_branch: List[Union[Agent, Tool, "Condition"]] = field(default_factory=list)
    else_branch: Optional[List[Union[Agent, Tool, "Condition"]]] = None
    line: int = 0
    column: int = 0
    
    @property
    def element_id(self) -> str:
        return self.id
    
    def get_read_vars(self) -> Set[str]:
        """Variables read by the condition expression."""
        return self.expression.get_referenced_vars()
    
    def get_write_vars(self) -> Set[str]:
        """Conditions don't write to variables directly."""
        return set()
    
    def get_all_branch_elements(self) -> List[Union[Agent, Tool, "Condition"]]:
        """Get all elements from both branches."""
        elements = list(self.then_branch)
        if self.else_branch:
            elements.extend(self.else_branch)
        return elements
    
    def __repr__(self) -> str:
        then_count = len(self.then_branch)
        else_count = len(self.else_branch) if self.else_branch else 0
        return f"Condition({self.id}: if {self.expression}, then={then_count}, else={else_count})"


@dataclass
class WhileLoop(Element):
    """
    A WhileLoop element in AWDL.
    
    While loops repeat their body until the condition becomes false.
    
    Attributes:
        id: Unique identifier for this loop
        condition: The condition expression to evaluate
        body: Elements to execute in each iteration
    """
    
    id: str
    condition: Expression
    body: List[Union[Agent, Tool, Condition]] = field(default_factory=list)
    line: int = 0
    column: int = 0
    
    @property
    def element_id(self) -> str:
        return self.id
    
    def get_read_vars(self) -> Set[str]:
        """Variables read by the loop condition."""
        return self.condition.get_referenced_vars()
    
    def get_write_vars(self) -> Set[str]:
        """Loops don't write to variables directly."""
        return set()
    
    def __repr__(self) -> str:
        return f"WhileLoop({self.id}: while {self.condition}, body={len(self.body)})"


@dataclass
class ForLoop(Element):
    """
    A ForLoop element in AWDL.
    
    For loops iterate over a collection.
    
    Attributes:
        id: Unique identifier for this loop
        iterator_var: The variable name for the iterator
        iterable: Expression for the collection to iterate over
        body: Elements to execute in each iteration
    """
    
    id: str
    iterator_var: str
    iterable: Expression
    body: List[Union[Agent, Tool, Condition]] = field(default_factory=list)
    line: int = 0
    column: int = 0
    
    @property
    def element_id(self) -> str:
        return self.id
    
    def get_read_vars(self) -> Set[str]:
        """Variables read by the loop."""
        return self.iterable.get_referenced_vars()
    
    def get_write_vars(self) -> Set[str]:
        """The iterator variable is written by the loop."""
        return {self.iterator_var}
    
    def __repr__(self) -> str:
        return f"ForLoop({self.id}: for {self.iterator_var} in {self.iterable}, body={len(self.body)})"


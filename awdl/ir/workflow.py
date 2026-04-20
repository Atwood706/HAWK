"""
Workflow IR for rebuilt AWDL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Union

from awdl.ir.conditions import Condition, ForLoop, WhileLoop
from awdl.ir.elements import Agent, FunctionCall, FunctionDefinition, ProfileDefinition, Tool
from awdl.ir.variables import Import, Variable


WorkflowElement = Union[Agent, Tool, FunctionCall, Condition, WhileLoop, ForLoop]


@dataclass
class Workflow:
    name: str
    version: str = "1.0"
    imports: List[Import] = field(default_factory=list)
    profiles: Dict[str, ProfileDefinition] = field(default_factory=dict)
    functions: Dict[str, FunctionDefinition] = field(default_factory=dict)
    variables: List[Variable] = field(default_factory=list)
    elements: List[WorkflowElement] = field(default_factory=list)
    source_path: Optional[str] = None

    def get_variable(self, name: str) -> Optional[Variable]:
        for var in self.variables:
            if var.name == name:
                return var
        return None

    def get_variable_names(self) -> Set[str]:
        return {var.name for var in self.variables}

    def get_agents(self) -> List[Agent]:
        return [e for e in self.elements if isinstance(e, Agent)]

    def get_tools(self) -> List[Tool]:
        return [e for e in self.elements if isinstance(e, Tool)]

    def get_functions(self) -> List[FunctionCall]:
        return [e for e in self.elements if isinstance(e, FunctionCall)]

    def get_element_by_id(self, element_id: str) -> Optional[WorkflowElement]:
        for element in self.get_all_elements_flat():
            if getattr(element, "element_id", None) == element_id:
                return element
        return None

    def get_all_elements_flat(self) -> List[WorkflowElement]:
        all_elements: List[WorkflowElement] = []

        def collect(elements: List[WorkflowElement]) -> None:
            for element in elements:
                all_elements.append(element)
                if isinstance(element, Condition):
                    collect(element.then_branch)
                    if element.else_branch:
                        collect(element.else_branch)
                elif isinstance(element, (WhileLoop, ForLoop)):
                    collect(element.body)

        collect(self.elements)
        return all_elements

    def validate(self) -> List["ValidationError"]:
        from awdl.language.errors import ValidationError

        errors: List[ValidationError] = []
        top_level_vars = self.get_variable_names()

        for element in self.get_all_elements_flat():
            errors.extend(self._validate_element_vars(element, top_level_vars))

            if isinstance(element, Agent):
                profile_name = element.config.get("profile")
                if not profile_name:
                    errors.append(ValidationError(message=f"Agent '{element.element_id}' is missing a profile"))
                elif profile_name not in self.profiles:
                    errors.append(ValidationError(message=f"Unknown profile '{profile_name}' in element '{element.element_id}'"))

            if isinstance(element, FunctionCall) and element.function_name not in self.functions:
                errors.append(
                    ValidationError(
                        message=f"Unknown function '{element.function_name}' in element '{element.element_id}'"
                    )
                )

        for definition in self.functions.values():
            fn_vars = definition.get_variable_names()
            for element in self._flatten_definition_elements(definition.elements):
                errors.extend(self._validate_element_vars(element, fn_vars, definition.name))

            for output_name in definition.outputs:
                if output_name not in fn_vars:
                    errors.append(
                        ValidationError(
                            message=f"Function '{definition.name}' declares unknown output '{output_name}'"
                        )
                    )

        return errors

    def _flatten_definition_elements(self, elements: List[WorkflowElement]) -> List[WorkflowElement]:
        flattened: List[WorkflowElement] = []

        def collect(items: List[WorkflowElement]) -> None:
            for element in items:
                flattened.append(element)
                if isinstance(element, Condition):
                    collect(element.then_branch)
                    if element.else_branch:
                        collect(element.else_branch)
                elif isinstance(element, (WhileLoop, ForLoop)):
                    collect(element.body)

        collect(elements)
        return flattened

    def _validate_element_vars(
        self,
        element: WorkflowElement,
        valid_var_names: Set[str],
        scope_name: str = "workflow",
    ) -> List["ValidationError"]:
        from awdl.language.errors import ValidationError

        errors: List[ValidationError] = []
        for var_name in element.get_read_vars():
            if var_name not in valid_var_names:
                errors.append(
                    ValidationError(
                        message=f"Undefined variable '{var_name}' in element '{element.element_id}' ({scope_name})"
                    )
                )
        for var_name in element.get_write_vars():
            if var_name not in valid_var_names:
                errors.append(
                    ValidationError(
                        message=f"Undefined variable '{var_name}' in element '{element.element_id}' ({scope_name})"
                    )
                )
        return errors

    def get_dependency_analyzer(self) -> "DependencyAnalyzer":
        from awdl.ir.dependency import DependencyAnalyzer

        return DependencyAnalyzer(self)

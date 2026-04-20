"""
LangGraph code generator for rebuilt AWDL.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import List, Optional

from awdl.compiler.base import BaseCompiler
from awdl.compiler.langgraph.graph_builder import GraphBuilder
from awdl.compiler.langgraph.state import StateGenerator
from awdl.ir.conditions import Condition
from awdl.ir.elements import Agent, FunctionCall, FunctionDefinition, Tool
from awdl.ir.workflow import Workflow


class LangGraphCompiler(BaseCompiler):
    def __init__(self, workflow: Workflow):
        super().__init__(workflow)
        self.graph_builder = GraphBuilder(workflow)
        self.state_generator = StateGenerator(workflow)

    def get_target_name(self) -> str:
        return "langgraph"

    def compile(self) -> str:
        parts = [
            self._generate_header(),
            self._generate_imports(),
            self._generate_state_class(),
        ]

        subflows = self._generate_subflow_functions()
        if subflows:
            parts.append(subflows)

        parts.append(self._generate_node_functions())

        condition_funcs = self._generate_condition_functions()
        if condition_funcs:
            parts.append(condition_funcs)

        parts.append(self._generate_graph())
        parts.append(self._generate_entry_point())
        return "\n\n".join(part for part in parts if part)

    def _generate_header(self) -> str:
        return (
            '"""\n'
            "Auto-generated LangGraph workflow from rebuilt AWDL.\n\n"
            f"Workflow: {self.workflow.name}\n"
            f"Version: {self.workflow.version}\n"
            '"""'
        )

    def _generate_imports(self) -> str:
        return "\n".join(
            [
                "from typing import Any, TypedDict",
                "from pathlib import Path",
                "from langgraph.graph import END, StateGraph",
                "from stdlib.runtime import run_agent, run_tool",
            ]
        )

    def _generate_state_class(self) -> str:
        workflow_dir = str(Path(self.workflow.source_path).resolve().parent) if self.workflow.source_path else "."
        inline_profiles = {name: definition.config for name, definition in self.workflow.profiles.items()}
        return "\n".join(
            [
                self.state_generator.generate_state_class("WorkflowState"),
                "",
                f"WORKFLOW_DIR = {workflow_dir!r}",
                f"INLINE_PROFILES = {inline_profiles!r}",
                "",
                self.state_generator.get_initial_state(),
            ]
        )

    def _generate_subflow_functions(self) -> Optional[str]:
        functions: List[str] = []
        for definition in self.workflow.functions.values():
            functions.append(self._generate_subflow_function(definition))
        return "\n\n".join(functions) if functions else None

    def _generate_subflow_function(self, definition: FunctionDefinition) -> str:
        lines = [f"def {definition.name}_impl(call_inputs: dict[str, Any]) -> dict[str, Any]:"]
        lines.append("    local_state: dict[str, Any] = {}")
        for input_name in definition.inputs:
            lines.append(f'    local_state["{input_name}"] = call_inputs.get("{input_name}", "")')
        for output_name in definition.outputs:
            if output_name not in definition.inputs:
                lines.append(f'    local_state.setdefault("{output_name}", "")')
        for variable in definition.variables:
            default = repr(variable.default_value) if variable.has_default() else '""'
            lines.append(f'    local_state.setdefault("{variable.name}", {default})')

        for element in definition.elements:
            lines.extend(self._generate_element_execution_lines(element, "local_state", indent="    "))

        lines.append("    return {")
        for output_name in definition.outputs:
            lines.append(f'        "{output_name}": local_state.get("{output_name}", ""),')
        lines.append("    }")
        return "\n".join(lines)

    def _generate_node_functions(self) -> str:
        functions: List[str] = []
        for element in self.workflow.get_all_elements_flat():
            if isinstance(element, Agent):
                functions.append(self._generate_agent_node(element))
            elif isinstance(element, Tool):
                functions.append(self._generate_tool_node(element))
            elif isinstance(element, FunctionCall):
                functions.append(self._generate_function_call_node(element))
        return "\n\n".join(functions)

    def _generate_agent_node(self, agent: Agent) -> str:
        lines = [f"def {agent.element_id}_node(state: WorkflowState) -> dict:"]
        lines.append("    call_inputs = {")
        for port_name, var_name in agent.inputs.items():
            lines.append(f'        "{port_name}": state["{var_name}"],')
        lines.append("    }")
        profile = agent.config.get("profile", "")
        lines.append(
            f'    result = run_agent("{profile}", call_inputs, INLINE_PROFILES, WORKFLOW_DIR)'
        )
        lines.append("    return {")
        for port_name, var_name in agent.outputs.items():
            lines.append(f'        "{var_name}": result.get("{port_name}", ""),')
        lines.append("    }")
        return "\n".join(lines)

    def _generate_tool_node(self, tool: Tool) -> str:
        lines = [f"def {tool.element_id}_node(state: WorkflowState) -> dict:"]
        lines.append("    call_inputs = {")
        for port_name, var_name in tool.inputs.items():
            lines.append(f'        "{port_name}": state["{var_name}"],')
        lines.append("    }")
        lines.append(f'    result = run_tool("{tool.tool_type}", call_inputs)')
        lines.append("    return {")
        for port_name, var_name in tool.outputs.items():
            lines.append(f'        "{var_name}": result.get("{port_name}", ""),')
        lines.append("    }")
        return "\n".join(lines)

    def _generate_function_call_node(self, call: FunctionCall) -> str:
        lines = [f"def {call.element_id}_node(state: WorkflowState) -> dict:"]
        lines.append("    call_inputs = {")
        for port_name, var_name in call.inputs.items():
            lines.append(f'        "{port_name}": state["{var_name}"],')
        lines.append("    }")
        lines.append(f'    result = {call.function_name}_impl(call_inputs)')
        lines.append("    return {")
        for port_name, var_name in call.outputs.items():
            lines.append(f'        "{var_name}": result.get("{port_name}", ""),')
        lines.append("    }")
        return "\n".join(lines)

    def _generate_element_execution_lines(self, element, state_name: str, indent: str = "") -> List[str]:
        if isinstance(element, Tool):
            lines = [f'{indent}_result = run_tool("{element.tool_type}", {{']
            for port_name, var_name in element.inputs.items():
                lines.append(f'{indent}    "{port_name}": {state_name}.get("{var_name}", ""),')
            lines.append(f"{indent}}})")
            for port_name, var_name in element.outputs.items():
                lines.append(f'{indent}{state_name}["{var_name}"] = _result.get("{port_name}", "")')
            return lines

        if isinstance(element, Agent):
            lines = [f'{indent}_result = run_agent("{element.config.get("profile", "")}", {{']
            for port_name, var_name in element.inputs.items():
                lines.append(f'{indent}    "{port_name}": {state_name}.get("{var_name}", ""),')
            lines.append(f"{indent}}}, INLINE_PROFILES, WORKFLOW_DIR)")
            for port_name, var_name in element.outputs.items():
                lines.append(f'{indent}{state_name}["{var_name}"] = _result.get("{port_name}", "")')
            return lines

        if isinstance(element, FunctionCall):
            lines = [f'{indent}_result = {element.function_name}_impl({{']
            for port_name, var_name in element.inputs.items():
                lines.append(f'{indent}    "{port_name}": {state_name}.get("{var_name}", ""),')
            lines.append(f"{indent}}})")
            for port_name, var_name in element.outputs.items():
                lines.append(f'{indent}{state_name}["{var_name}"] = _result.get("{port_name}", "")')
            return lines

        raise TypeError(f"Unsupported subflow element type: {type(element)!r}")

    def _generate_condition_functions(self) -> Optional[str]:
        functions: List[str] = []
        for element in self.workflow.elements:
            if isinstance(element, Condition):
                func_name = f"should_{element.element_id}"
                functions.append(
                    dedent(
                        f"""\
                        def {func_name}(state: WorkflowState) -> str:
                            if {element.expression.to_python()}:
                                return "then"
                            return "else"
                        """
                    ).strip()
                )
        return "\n\n".join(functions) if functions else None

    def _generate_graph(self) -> str:
        lines = [
            "workflow = StateGraph(WorkflowState)",
            "",
            "# Add nodes",
        ]
        for element in self.workflow.get_all_elements_flat():
            if isinstance(element, (Agent, Tool, FunctionCall)):
                lines.append(f'workflow.add_node("{element.element_id}", {element.element_id}_node)')

        lines.append("")
        lines.append("# Add edges")
        for edge in self.graph_builder.build_edges():
            lines.append(f'workflow.add_edge("{edge.source}", "{edge.target}")')

        conditional_edges = self.graph_builder.build_conditional_edges()
        for edge in conditional_edges:
            routes = ", ".join(
                f'"{key}": "{value}"' if value != "__end__" else f'"{key}": END'
                for key, value in edge.routes.items()
            )
            lines.append(
                f'workflow.add_conditional_edges("{edge.source}", {edge.condition_func}, {{{routes}}})'
            )

        entry_point = self.graph_builder.get_entry_point()
        if entry_point:
            lines.append("")
            lines.append(f'workflow.set_entry_point("{entry_point}")')
        return "\n".join(lines)

    def _generate_entry_point(self) -> str:
        return dedent(
            """\
            app = workflow.compile()
            """
        ).strip()

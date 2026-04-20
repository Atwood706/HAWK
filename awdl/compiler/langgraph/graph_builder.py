"""
LangGraph Graph Builder

This module transforms variable dependencies into LangGraph edges.
This is where the "magic" happens - converting the implicit variable-based
dependencies in AWDL into explicit graph edges for LangGraph.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Set

from awdl.ir.workflow import Workflow, WorkflowElement
from awdl.ir.elements import Agent, FunctionCall, Tool
from awdl.ir.conditions import Condition, WhileLoop, ForLoop
from awdl.ir.dependency import DependencyAnalyzer, ExecutionOrder


@dataclass
class Edge:
    """Represents an edge in the LangGraph graph."""
    source: str
    target: str
    
    def __repr__(self) -> str:
        return f"Edge({self.source} -> {self.target})"


@dataclass
class ConditionalEdge:
    """Represents a conditional edge in the LangGraph graph."""
    source: str
    condition_func: str  # Name of the condition function
    routes: Dict[str, str]  # condition_result -> target_node
    
    def __repr__(self) -> str:
        routes_str = ", ".join(f"{k}: {v}" for k, v in self.routes.items())
        return f"ConditionalEdge({self.source} -[{self.condition_func}]-> {{{routes_str}}})"


class GraphBuilder:
    """
    Transforms variable dependencies into LangGraph edges.
    
    This class is the bridge between the framework-agnostic IR and
    LangGraph's graph-based execution model.
    """
    
    def __init__(self, workflow: Workflow):
        """
        Initialize the graph builder.
        
        Args:
            workflow: The workflow to build a graph for
        """
        self.workflow = workflow
        self.analyzer = workflow.get_dependency_analyzer()
        self._execution_order: Optional[ExecutionOrder] = None
    
    @property
    def execution_order(self) -> ExecutionOrder:
        """Get the execution order (cached)."""
        if self._execution_order is None:
            self._execution_order = self.analyzer.get_execution_order()
        return self._execution_order
    
    def get_entry_point(self) -> Optional[str]:
        """
        Get the entry point node (first element in execution order).
        
        Returns:
            The ID of the entry point element, or None if no elements
        """
        if not self.execution_order.ordered_elements:
            return None
        return self.execution_order.ordered_elements[0].element_id
    
    def build_edges(self) -> List[Edge]:
        """
        Build edges from variable dependencies.
        
        This converts the implicit variable dependencies into explicit
        edges for LangGraph.
        
        Returns:
            List of Edge objects
        """
        edges: List[Edge] = []
        elements = self.execution_order.ordered_elements
        
        # Filter out conditions - they're handled separately
        non_condition_elements = [
            e for e in elements 
            if not isinstance(e, (Condition, WhileLoop, ForLoop))
        ]
        
        # Create edges between consecutive elements in execution order
        for i in range(len(non_condition_elements) - 1):
            current = non_condition_elements[i]
            next_elem = non_condition_elements[i + 1]
            
            # Check if there's actually a dependency
            current_writes = current.get_write_vars()
            next_reads = next_elem.get_read_vars()
            
            # Only add edge if there's a data dependency
            if current_writes & next_reads:
                edges.append(Edge(
                    source=current.element_id,
                    target=next_elem.element_id,
                ))
            else:
                # Even without direct dependency, sequential order is maintained
                edges.append(Edge(
                    source=current.element_id,
                    target=next_elem.element_id,
                ))
        
        return edges
    
    def build_conditional_edges(self) -> List[ConditionalEdge]:
        """
        Build conditional edges from Condition elements.
        
        Returns:
            List of ConditionalEdge objects
        """
        conditional_edges: List[ConditionalEdge] = []
        
        for element in self.workflow.elements:
            if isinstance(element, Condition):
                cond_edge = self._build_condition_edge(element)
                if cond_edge:
                    conditional_edges.append(cond_edge)
        
        return conditional_edges
    
    def _build_condition_edge(self, condition: Condition) -> Optional[ConditionalEdge]:
        """
        Build a conditional edge for a Condition element.
        
        Args:
            condition: The Condition element
            
        Returns:
            A ConditionalEdge, or None if not applicable
        """
        # Find the element that precedes this condition
        elements = self.execution_order.ordered_elements
        condition_idx = next(
            (i for i, e in enumerate(elements) if e.element_id == condition.element_id),
            -1
        )
        
        if condition_idx <= 0:
            return None
        
        source = elements[condition_idx - 1].element_id
        condition_func = f"should_{condition.element_id}"
        
        # Build routes
        routes = {}
        
        # Then branch
        if condition.then_branch:
            then_target = condition.then_branch[0].element_id
            routes["then"] = then_target
        
        # Else branch
        if condition.else_branch:
            else_target = condition.else_branch[0].element_id
            routes["else"] = else_target
        else:
            # If no else, route to next element or END
            if condition_idx < len(elements) - 1:
                routes["else"] = elements[condition_idx + 1].element_id
            else:
                routes["else"] = "__end__"
        
        return ConditionalEdge(
            source=source,
            condition_func=condition_func,
            routes=routes,
        )
    
    def get_all_node_ids(self) -> List[str]:
        """
        Get all node IDs for the graph.
        
        Returns:
            List of node IDs
        """
        node_ids = []
        
        for element in self.workflow.get_all_elements_flat():
            if isinstance(element, (Agent, Tool, FunctionCall)):
                node_ids.append(element.element_id)
        
        return node_ids
    
    def get_nodes_by_type(self) -> Tuple[List[str], List[str]]:
        """
        Get node IDs separated by type (agents and tools).
        
        Returns:
            Tuple of (agent_ids, tool_ids)
        """
        agent_ids = []
        tool_ids = []
        
        for element in self.workflow.get_all_elements_flat():
            if isinstance(element, Agent):
                agent_ids.append(element.element_id)
            elif isinstance(element, (Tool, FunctionCall)):
                tool_ids.append(element.element_id)
        
        return agent_ids, tool_ids

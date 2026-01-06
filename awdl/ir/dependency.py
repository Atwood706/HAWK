"""
AWDL Dependency Analyzer

This module implements the variable dependency analyzer that derives
execution order from variable read/write relationships.

This is the core mechanism that determines workflow order WITHOUT
requiring explicit edges. The order is purely derived from which
elements read/write which variables.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, Union
from collections import defaultdict

from awdl.ir.elements import Agent, Tool, Element
from awdl.ir.conditions import Condition, WhileLoop, ForLoop


# Type alias for workflow elements
WorkflowElement = Union[Agent, Tool, Condition, WhileLoop, ForLoop]


@dataclass
class ExecutionOrder:
    """
    Represents the execution order of workflow elements.
    
    This is derived from variable dependencies, not explicit edges.
    """
    
    ordered_elements: List[WorkflowElement] = field(default_factory=list)
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)  # element_id -> depends on element_ids
    
    def __iter__(self):
        return iter(self.ordered_elements)
    
    def __len__(self):
        return len(self.ordered_elements)


class DependencyAnalyzer:
    """
    Analyzes variable dependencies to derive execution order.
    
    This is the core mechanism that determines workflow order WITHOUT
    requiring explicit edges. The order is purely derived from which
    elements read/write which variables.
    
    The analyzer builds a dependency graph where:
    - Nodes are elements (agents, tools, conditions)
    - Edges represent "must execute after" relationships
    - An edge from A to B means B depends on a variable that A writes
    """
    
    def __init__(self, workflow: "Workflow"):
        """
        Initialize the analyzer with a workflow.
        
        Args:
            workflow: The workflow to analyze
        """
        self.workflow = workflow
        self.write_map: Dict[str, WorkflowElement] = {}  # var -> element that writes it
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)  # element_id -> depends on element_ids
        self.elements: List[WorkflowElement] = []
        
        self._build_dependency_graph()
    
    def _build_dependency_graph(self) -> None:
        """
        Build dependency relationships based on variable read/write.
        
        For each element:
        1. Find which variables it reads
        2. For each read variable, find which element writes it
        3. Add a dependency edge from the writer to this element
        4. Register this element as the writer of its output variables
        """
        # Get top-level elements (don't flatten conditions - we handle them specially)
        self.elements = list(self.workflow.elements)
        
        for element in self.elements:
            self._process_element(element)
    
    def _process_element(self, element: WorkflowElement) -> None:
        """Process a single element for dependencies."""
        # Get variables this element reads
        read_vars = element.get_read_vars()
        
        # For each variable this element reads, find who writes it
        for var_name in read_vars:
            if var_name in self.write_map:
                writer = self.write_map[var_name]
                # Add dependency: this element depends on the writer
                self.dependencies[element.element_id].add(writer.element_id)
        
        # Register this element as the writer of its output variables
        write_vars = element.get_write_vars()
        for var_name in write_vars:
            self.write_map[var_name] = element
        
        # Handle nested elements in conditions/loops
        if isinstance(element, Condition):
            # Process then_branch
            for nested in element.then_branch:
                self._process_element(nested)
            # Process else_branch if present
            if element.else_branch:
                for nested in element.else_branch:
                    self._process_element(nested)
        elif isinstance(element, (WhileLoop, ForLoop)):
            for nested in element.body:
                self._process_element(nested)
    
    def get_dependencies(self, element_id: str) -> Set[str]:
        """
        Get the element IDs that the given element depends on.
        
        Args:
            element_id: The ID of the element to check
            
        Returns:
            Set of element IDs that must execute before this element
        """
        return self.dependencies.get(element_id, set())
    
    def get_dependents(self, element_id: str) -> Set[str]:
        """
        Get the element IDs that depend on the given element.
        
        Args:
            element_id: The ID of the element to check
            
        Returns:
            Set of element IDs that must execute after this element
        """
        dependents = set()
        for eid, deps in self.dependencies.items():
            if element_id in deps:
                dependents.add(eid)
        return dependents
    
    def get_variable_writer(self, var_name: str) -> Optional[WorkflowElement]:
        """
        Get the element that writes to a variable.
        
        Args:
            var_name: The name of the variable
            
        Returns:
            The element that writes to this variable, or None
        """
        return self.write_map.get(var_name)
    
    def get_execution_order(self) -> ExecutionOrder:
        """
        Get the execution order of elements using topological sort.
        
        The order respects variable dependencies: if element B reads
        a variable that element A writes, A will appear before B.
        
        Returns:
            ExecutionOrder with elements in dependency-respecting order
            
        Raises:
            ValueError: If there is a circular dependency
        """
        # Topological sort using Kahn's algorithm
        in_degree: Dict[str, int] = defaultdict(int)
        element_map: Dict[str, WorkflowElement] = {}
        
        # Build element map and calculate in-degrees
        for element in self.elements:
            element_map[element.element_id] = element
            in_degree[element.element_id] = 0
        
        for element_id, deps in self.dependencies.items():
            if element_id in element_map:
                in_degree[element_id] = len(deps)
        
        # Find all elements with no dependencies (in-degree 0)
        queue: List[str] = [
            eid for eid in element_map.keys() 
            if in_degree[eid] == 0
        ]
        
        ordered: List[WorkflowElement] = []
        
        while queue:
            # Get an element with no remaining dependencies
            current_id = queue.pop(0)
            current = element_map[current_id]
            ordered.append(current)
            
            # Reduce in-degree for all dependents
            for other_id in element_map.keys():
                if current_id in self.dependencies.get(other_id, set()):
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)
        
        # Check for circular dependencies
        if len(ordered) != len(element_map):
            remaining = set(element_map.keys()) - {e.element_id for e in ordered}
            raise ValueError(
                f"Circular dependency detected involving elements: {remaining}"
            )
        
        return ExecutionOrder(
            ordered_elements=ordered,
            dependencies=dict(self.dependencies),
        )
    
    def get_edges(self) -> List[Tuple[str, str]]:
        """
        Get the dependency edges as (from, to) tuples.
        
        These represent the "must execute after" relationships.
        An edge (A, B) means B depends on A (A must execute before B).
        
        Returns:
            List of (source_id, target_id) tuples
        """
        edges = []
        for target_id, source_ids in self.dependencies.items():
            for source_id in source_ids:
                edges.append((source_id, target_id))
        return edges
    
    def detect_cycles(self) -> Optional[List[str]]:
        """
        Detect if there are any cycles in the dependency graph.
        
        Returns:
            List of element IDs in the cycle, or None if no cycle exists
        """
        # Use DFS-based cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {e.element_id: WHITE for e in self.elements}
        parent: Dict[str, Optional[str]] = {e.element_id: None for e in self.elements}
        
        def dfs(node: str) -> Optional[List[str]]:
            color[node] = GRAY
            
            for dep_id in self.dependencies.get(node, set()):
                if dep_id not in color:
                    continue
                if color[dep_id] == GRAY:
                    # Found a cycle - reconstruct it
                    cycle = [dep_id, node]
                    current = parent[node]
                    while current and current != dep_id:
                        cycle.append(current)
                        current = parent[current]
                    return cycle[::-1]
                elif color[dep_id] == WHITE:
                    parent[dep_id] = node
                    result = dfs(dep_id)
                    if result:
                        return result
            
            color[node] = BLACK
            return None
        
        for element in self.elements:
            if color[element.element_id] == WHITE:
                cycle = dfs(element.element_id)
                if cycle:
                    return cycle
        
        return None
    
    def __repr__(self) -> str:
        return (
            f"DependencyAnalyzer("
            f"elements={len(self.elements)}, "
            f"edges={len(self.get_edges())})"
        )


# Import Workflow at the end to avoid circular imports
from awdl.ir.workflow import Workflow


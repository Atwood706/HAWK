"""
AWDL Built-in Registry

This module defines the built-in agents and tools available in AWDL.
These are abstract definitions - actual implementations are provided by stdlib.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum, auto


class ElementCategory(Enum):
    """Categories of built-in elements."""
    AGENT = auto()
    TOOL = auto()


@dataclass
class PortDefinition:
    """Definition of an input or output port."""
    
    name: str
    description: str = ""
    required: bool = True
    default: Optional[Any] = None
    port_type: str = "any"  # "string", "int", "float", "bool", "list", "any"


@dataclass
class BuiltinDefinition:
    """Definition of a built-in agent or tool."""
    
    name: str
    category: ElementCategory
    description: str = ""
    inputs: List[PortDefinition] = field(default_factory=list)
    outputs: List[PortDefinition] = field(default_factory=list)
    
    @property
    def input_names(self) -> List[str]:
        """Get list of input port names."""
        return [p.name for p in self.inputs]
    
    @property
    def output_names(self) -> List[str]:
        """Get list of output port names."""
        return [p.name for p in self.outputs]
    
    @property
    def required_inputs(self) -> List[str]:
        """Get list of required input port names."""
        return [p.name for p in self.inputs if p.required]
    
    def get_input(self, name: str) -> Optional[PortDefinition]:
        """Get an input port definition by name."""
        for port in self.inputs:
            if port.name == name:
                return port
        return None
    
    def get_output(self, name: str) -> Optional[PortDefinition]:
        """Get an output port definition by name."""
        for port in self.outputs:
            if port.name == name:
                return port
        return None


class BuiltinRegistry:
    """
    Registry of built-in agents and tools.
    
    This is the central registry that the parser uses to validate
    element invocations and determine element categories.
    """
    
    def __init__(self):
        self._definitions: Dict[str, BuiltinDefinition] = {}
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register the default built-in agents and tools."""
        # Register built-in agents
        self.register(BuiltinDefinition(
            name="llm_agent",
            category=ElementCategory.AGENT,
            description="[Deprecated] Use deepseek_agent instead",
            inputs=[
                PortDefinition(name="prompt", description="The prompt to send to the LLM", required=True),
                PortDefinition(name="context", description="Optional context for the LLM", required=False),
                PortDefinition(name="system_prompt", description="Optional system prompt", required=False),
            ],
            outputs=[
                PortDefinition(name="response", description="The LLM's response"),
            ],
        ))

        self.register(BuiltinDefinition(
            name="deepseek_agent",
            category=ElementCategory.AGENT,
            description="DeepSeek LLM agent for text generation",
            inputs=[
                PortDefinition(name="prompt", description="The prompt to send to the LLM", required=True),
                PortDefinition(name="context", description="Optional context for the LLM", required=False),
                PortDefinition(name="system_prompt", description="Optional system prompt", required=False),
            ],
            outputs=[
                PortDefinition(name="response", description="The LLM's response"),
            ],
        ))

        self.register(BuiltinDefinition(
            name="qwen_agent",
            category=ElementCategory.AGENT,
            description="Qwen LLM agent for text generation",
            inputs=[
                PortDefinition(name="prompt", description="The prompt to send to the LLM", required=True),
                PortDefinition(name="context", description="Optional context for the LLM", required=False),
                PortDefinition(name="system_prompt", description="Optional system prompt", required=False),
            ],
            outputs=[
                PortDefinition(name="response", description="The LLM's response"),
            ],
        ))
        
        self.register(BuiltinDefinition(
            name="router_agent",
            category=ElementCategory.AGENT,
            description="Routes queries to different paths based on content",
            inputs=[
                PortDefinition(name="query", description="The query to route", required=True),
                PortDefinition(name="routes", description="Available routes", required=True),
            ],
            outputs=[
                PortDefinition(name="selected_route", description="The selected route"),
            ],
        ))
        
        self.register(BuiltinDefinition(
            name="fallback_agent",
            category=ElementCategory.AGENT,
            description="Fallback agent for when primary processing fails",
            inputs=[
                PortDefinition(name="input", description="Input to process", required=True),
            ],
            outputs=[
                PortDefinition(name="output", description="Fallback output"),
            ],
        ))
        
        # Register built-in tools
        self.register(BuiltinDefinition(
            name="web_search",
            category=ElementCategory.TOOL,
            description="Search the web for information",
            inputs=[
                PortDefinition(name="query", description="Search query", required=True),
                PortDefinition(name="max_results", description="Maximum results to return", required=False, default=10),
            ],
            outputs=[
                PortDefinition(name="results", description="Search results"),
            ],
        ))
        
        self.register(BuiltinDefinition(
            name="web_fetch",
            category=ElementCategory.TOOL,
            description="Fetch and extract text content from a URL",
            inputs=[
                PortDefinition(name="url", description="URL to fetch", required=True),
            ],
            outputs=[
                PortDefinition(name="content", description="Extracted text content"),
                PortDefinition(name="error", description="Error message if fetch failed", required=False),
            ],
        ))

        self.register(BuiltinDefinition(
            name="pubmed_search",
            category=ElementCategory.TOOL,
            description="Search PubMed (NCBI E-utilities) for medical literature",
            inputs=[
                PortDefinition(name="query", description="PubMed search query", required=True),
                PortDefinition(name="max_results", description="Maximum results to return", required=False, default=10),
                PortDefinition(name="sort", description="Sort order (e.g., relevance, date)", required=False, default="relevance"),
                PortDefinition(name="include_abstracts", description="Whether to fetch abstracts via EFetch", required=False, default=False),
                PortDefinition(name="mindate", description="Start date (YYYY or YYYY/MM/DD)", required=False),
                PortDefinition(name="maxdate", description="End date (YYYY or YYYY/MM/DD)", required=False),
            ],
            outputs=[
                PortDefinition(name="results", description="Formatted PubMed results"),
                PortDefinition(name="pmids", description="List of PMIDs"),
                PortDefinition(name="error", description="Error message if failed", required=False),
            ],
        ))
        
        self.register(BuiltinDefinition(
            name="file_read",
            category=ElementCategory.TOOL,
            description="Read contents of a file",
            inputs=[
                PortDefinition(name="path", description="Path to the file", required=True),
            ],
            outputs=[
                PortDefinition(name="content", description="File contents"),
                PortDefinition(name="error", description="Error message if read failed", required=False),
            ],
        ))
        
        self.register(BuiltinDefinition(
            name="file_write",
            category=ElementCategory.TOOL,
            description="Write contents to a file",
            inputs=[
                PortDefinition(name="path", description="Path to the file", required=True),
                PortDefinition(name="content", description="Content to write", required=True),
            ],
            outputs=[
                PortDefinition(name="success", description="Whether write succeeded"),
                PortDefinition(name="error", description="Error message if write failed", required=False),
            ],
        ))
        
        self.register(BuiltinDefinition(
            name="render_svg",
            category=ElementCategory.TOOL,
            description="Render SVG diagram to PNG image using Playwright (local)",
            inputs=[
                PortDefinition(name="svg_code", description="SVG diagram code", required=True),
                PortDefinition(name="output_path", description="Path to save PNG image", required=True),
            ],
            outputs=[
                PortDefinition(name="success", description="Whether rendering succeeded"),
                PortDefinition(name="error", description="Error message if failed"),
            ],
        ))
        
        # Alias for backward compatibility
        self.register(BuiltinDefinition(
            name="render_drawio",
            category=ElementCategory.TOOL,
            description="[Deprecated] Use render_svg instead",
            inputs=[
                PortDefinition(name="xml_code", description="SVG/XML code", required=True),
                PortDefinition(name="output_path", description="Path to save PNG image", required=True),
            ],
            outputs=[
                PortDefinition(name="success", description="Whether rendering succeeded"),
                PortDefinition(name="error", description="Error message if failed"),
            ],
        ))

        self.register(BuiltinDefinition(
            name="mcp_call",
            category=ElementCategory.TOOL,
            description="Call an external MCP server tool via stdio (args/result as JSON strings)",
            inputs=[
                PortDefinition(name="server", description="MCP server spec, e.g. stdio:<cmd...>", required=True),
                PortDefinition(name="tool", description="MCP tool name to call", required=True),
                PortDefinition(name="args_json", description="JSON string of tool arguments", required=False, default="{}"),
            ],
            outputs=[
                PortDefinition(name="result", description="CallToolResult JSON string"),
                PortDefinition(name="error", description="Error message if failed", required=False),
            ],
        ))
    
    def register(self, definition: BuiltinDefinition) -> None:
        """Register a built-in definition."""
        self._definitions[definition.name] = definition
    
    def get(self, name: str) -> Optional[BuiltinDefinition]:
        """Get a built-in definition by name."""
        return self._definitions.get(name)
    
    def exists(self, name: str) -> bool:
        """Check if a built-in exists."""
        return name in self._definitions
    
    def is_agent(self, name: str) -> bool:
        """Check if a built-in is an agent."""
        defn = self.get(name)
        return defn is not None and defn.category == ElementCategory.AGENT
    
    def is_tool(self, name: str) -> bool:
        """Check if a built-in is a tool."""
        defn = self.get(name)
        return defn is not None and defn.category == ElementCategory.TOOL
    
    def get_all_agents(self) -> List[BuiltinDefinition]:
        """Get all agent definitions."""
        return [d for d in self._definitions.values() if d.category == ElementCategory.AGENT]
    
    def get_all_tools(self) -> List[BuiltinDefinition]:
        """Get all tool definitions."""
        return [d for d in self._definitions.values() if d.category == ElementCategory.TOOL]
    
    def list_all(self) -> List[str]:
        """List all registered built-in names."""
        return list(self._definitions.keys())


# Global registry instance
BUILTIN_REGISTRY = BuiltinRegistry()


# Convenience dictionaries for backward compatibility
BUILTIN_AGENTS: Dict[str, Dict[str, Any]] = {
    "llm_agent": {
        "inputs": ["prompt", "context"],
        "outputs": ["response"],
        "required_inputs": ["prompt"],
    },
    "deepseek_agent": {
        "inputs": ["prompt", "context"],
        "outputs": ["response"],
        "required_inputs": ["prompt"],
    },
    "qwen_agent": {
        "inputs": ["prompt", "context"],
        "outputs": ["response"],
        "required_inputs": ["prompt"],
    },
    "router_agent": {
        "inputs": ["query", "routes"],
        "outputs": ["selected_route"],
        "required_inputs": ["query", "routes"],
    },
    "fallback_agent": {
        "inputs": ["input"],
        "outputs": ["output"],
        "required_inputs": ["input"],
    },
}

BUILTIN_TOOLS: Dict[str, Dict[str, Any]] = {
    "web_search": {
        "inputs": ["query"],
        "outputs": ["results"],
        "required_inputs": ["query"],
    },
    "web_fetch": {
        "inputs": ["url"],
        "outputs": ["content"],
        "required_inputs": ["url"],
    },
    "pubmed_search": {
        "inputs": ["query", "max_results", "sort", "include_abstracts", "mindate", "maxdate"],
        "outputs": ["results", "pmids", "error"],
        "required_inputs": ["query"],
    },
    "file_read": {
        "inputs": ["path"],
        "outputs": ["content"],
        "required_inputs": ["path"],
    },
    "file_write": {
        "inputs": ["path", "content"],
        "outputs": ["success"],
        "required_inputs": ["path", "content"],
    },
}


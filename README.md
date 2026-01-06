# AWDL - Agentic Workflow Description Language

AWDL is a domain-specific language for defining agent workflows in a simple, declarative manner. It allows users to describe complex agent workflows without dealing with the underlying framework implementation details.

## Features

- **Simple Syntax**: Define workflows using a clean, readable syntax
- **Framework Agnostic IR**: The intermediate representation is independent of any specific agent framework
- **Variable-Driven Dependencies**: Execution order is automatically derived from variable dependencies
- **Multiple Compilation Targets**: Currently supports LangGraph, with more frameworks planned

## Installation

```bash
pip install -e .
```

## Quick Start

Create a workflow file `example.awdl`:

```awdl
import hawk.agents.llm
import hawk.tools.web_search

__start__

string user_query: "What is the weather today?"
string search_results
string final_answer

web_search: {
    query: user_query,
    results: search_results
}

llm_agent: {
    context: search_results,
    prompt: user_query,
    response: final_answer
}

__end__
```

Compile and run:

```bash
# 1. 验证工作流（检查语法和依赖）
awdl validate examples/test.awdl --verbose

# 2. 编译成 Python（生成可执行的 LangGraph 代码）
awdl compile examples/test.awdl --target langgraph -o workflow.py

# 3. 运行工作流（使用 .awdl 文件中的默认值）
awdl run examples/test.awdl

# 4. 运行工作流（覆盖默认值，传入自定义输入）
awdl run examples/test.awdl --input user_query=Hello
```

## Architecture

AWDL uses a three-layer architecture:

1. **Layer 1 - Parser**: Tokenizes and parses `.awdl` files into an intermediate representation
2. **Layer 2 - IR**: Framework-agnostic representation of workflows with Agent, Tool, and Condition elements
3. **Layer 3 - Compiler**: Transforms IR into executable code for target frameworks (e.g., LangGraph)

## License

MIT License


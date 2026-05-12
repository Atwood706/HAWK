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

# Dependency for rendering
playwright install chromium
```

## API Configuration
DeepSeek as an example:
- **DEEPSEEK_API_KEY**：Your DeepSeek API Key (NECESSARY)
- **DEEPSEEK_BASE_URL**：`https://api.deepseek.com`(or `https://api.deepseek.com/v1`, OpenAI compatible)
- **DEEPSEEK_MODEL**：`deepseek-chat` (Default)

See [DeepSeek API Configuration](#deepseek-api-configuration) for details.


## Quick Start

Create a workflow file `test.awdl`:

```awdl
profile coder {
    model: "deepseek-chat"
    max_turns: 4
    tools: ["web_search", "web_fetch"]
}

__start__

string user_query: "What is the weather today?"
string final_answer

agent: {
    profile: "coder",
    prompt: user_query,
    response: final_answer
}

__end__
```

Compile and run:

```bash
# 1. Validate the workflow (Check syntax and dependencies)
awdl validate examples/test.awdl --verbose

# 2. Compile the workflow (Compile the .awdl workflow into an executable LangGraph script)
awdl compile examples/test.awdl --target langgraph -o workflow.py

# 3. Run the workflow (Use the model and default input defined in the profile)
awdl run examples/test.awdl

# 4. Run with custom input（Override the default input by passing a custom value）
awdl run examples/test.awdl --input user_query="your string"
```

## Guideline for Customizing .awdl File
```
import stdlib.tools.file_io

profile default_llm {
    model: "gpt-4o"   # model_name
    temperature: 0.7  # other possible configurations
}

__start__

# Strings defined here
string input_text
string output_text

# System Prompts

# Procedure
# for example, LLM processing 
agent: {
    profile: "default_llm",
    system_prompt: "You are a helpful assistant.",
    prompt: input_text,
    response: output_text
}

# for example, tool using
tool_name: {
    query: query_name,
    results: results_name,
    error: error_name
}

# Save File
file_write {
    path: "output.txt",
    content: output_text,
    success: write_status
}

__end__
```


## Local Workbench

### Configuration Panel
The local web workbench exposes a Config page for workspace-local editing and inspection:

- **Profiles**: list, edit, and save TOML profiles through the backend API
- **Tools**: inspect the builtin registry from `awdl/ir/builtins.py`
- **Skills**: browse discovered `SKILL.md` documents from the runtime search paths
- **Settings**: the app reads backend-managed settings and falls back to defaults when none are stored

Run the web app from `apps/web/` and open the `Config` tab to use these panels.

### Built-In OpenRouter Demo

The local workbench seeds a runnable demo profile and workflow into backend-managed local storage:

- **Built-in profile**: `openrouter_chat` - Pre-configured OpenRouter connection
- **Built-in workflow**: `openrouter_demo` - Example workflow demonstrating LLM integration

**Setup** (one time):

```bash
# Check Node.js and npm versions
node -v
npm -v

# Install web app dependencies
cd apps/web
npm install

Run the demo:
- Start the workbench (see [Workbench Startup](#workbench-startup))
- Open the UI at http://127.0.0.1:5174
- Go to Config tab and fill your OpenRouter API Key
- Open Build tab and click Run
- Open View tab to inspect the saved result, generated AWDL, and execution trace

The seeded profile uses OpenRouter's OpenAI-compatible endpoint:
```
base_url = "https://openrouter.ai/api/v1"
model = "openai/gpt-4.1-mini"
```

### Workbench Startup
From the HAWK repository root, start the FastAPI backend and Vite frontend together with one command:

```bash
python scripts/dev_workbench.py
```
This starts:
FastAPI API server at `http://127.0.0.1:8000`
Vite frontend at `http://127.0.0.1:5174`

The frontend dev server proxies /api/* requests to FastAPI, so the browser UI can call the backend without changing frontend API URLs.

Running services separately (alternative):
```bash
# Terminal 1: Backend only
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend only
cd apps/web
npm run dev -- --host 127.0.0.1 --port 5174
```
Note: The dev_workbench.py script handles both services automatically and is the recommended way to run the workbench.

## DeepSeek API Configuration
This project uses `langchain-openai` to call DeepSeek models via an OpenAI-compatible API.

Set environment variables：

- **DEEPSEEK_API_KEY**：Your DeepSeek API Key (NECESSARY)
- **DEEPSEEK_BASE_URL**：Default `https://api.deepseek.com`(or `https://api.deepseek.com/v1`, OpenAI compatible)
- **DEEPSEEK_MODEL**：`deepseek-chat` (Default)

Windows PowerShell：
```powershell
$env:DEEPSEEK_API_KEY="your api_key"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:DEEPSEEK_MODEL="deepseek-chat"
```

Windows CMD：
```cmd
set DEEPSEEK_API_KEY=your api_key
set DEEPSEEK_BASE_URL=https://api.deepseek.com
set DEEPSEEK_MODEL=deepseek-chat
```

Linux CMD:
```cmd
export DEEPSEEK_API_KEY="your api_key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_MODEL="deepseek-chat"
```
> [!WARNING]
> Make sure your `DEEPSEEK_API_KEY` (sk-xxx) is valid before running the demo.  
> If the API key is invalid, expired, or missing, the model response may be empty or the request may fail.
>
> Make sure that the selected `DEEPSEEK_MODEL` is covered by your API key or account permissions.  
> If your API key does not have access to the specified model type, the workflow may return an empty response or an authorization/model-access error.

## 外部 MCP Server 集成

AWDL 支持通过 `mcp_call` 工具调用外部 MCP (Model Context Protocol) Server，实现功能扩展。

### 1. 数据探索 MCP Server

位置：`external/mcp-server-data-exploration`

功能：加载 CSV、执行 Python 数据分析脚本

示例：
```bash
awdl run examples/mcp_load_csv.awdl
```

### 2. HTTP Request MCP Server ⭐ 新增

位置：`external/mcp-server-http`

功能：通用 HTTP/API 调用工具，支持任意 REST API 的 GET/POST/PUT/PATCH/DELETE 等请求

特性：
- ✅ 支持所有常见 HTTP 方法
- ✅ 支持自定义请求头、查询参数、JSON/文本请求体
- ✅ 支持超时控制、响应截断
- ✅ 支持 HTTPS，纯 Python 标准库实现
- ✅ Windows 兼容

安装（可选）：
```powershell
pip install -e external/mcp-server-http
```

示例：
```bash
# 简单 GET 请求
awdl run examples/mcp_http_simple.awdl

# 完整示例（GET/POST/错误处理）
awdl run examples/mcp_http_request.awdl
```

在 AWDL 中使用：
```awdl
string server: "stdio:python D:\\桌面\\HAWK\\external\\mcp-server-http\\src\\mcp_server_http\\server.py"
string tool: "http_request"
string args_json: "{\"url\":\"https://api.example.com/data\",\"method\":\"GET\"}"

string result_json
string error

mcp_call: {
    server: server,
    tool: tool,
    args_json: args_json,
    result: result_json,
    error: error
}
```

详细文档：[external/mcp-server-http/README.md](../external/mcp-server-http/README.md)

## Architecture

AWDL uses a three-layer architecture:

1. **Layer 1 - Parser**: Tokenizes and parses `.awdl` files into an intermediate representation
2. **Layer 2 - IR**: Framework-agnostic representation of workflows with Agent, Tool, and Condition elements
3. **Layer 3 - Compiler**: Transforms IR into executable code for target frameworks (e.g., LangGraph)

## License

MIT License


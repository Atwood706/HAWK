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
```

Run the demo:
- Start the workbench (see [Workbench Startup](#workbench-startup))
- Open the UI at http://127.0.0.1:5174
- Go to Config tab and fill your OpenRouter API Key
- Open Build tab and click Run
- Open View tab to inspect the saved result, generated AWDL, and execution trace

The seeded profile uses OpenRouter's OpenAI-compatible endpoint:

base_url = "https://openrouter.ai/api/v1"

model = "openai/gpt-4.1-mini"

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

## Architecture

AWDL uses a layered architecture:

## License

MIT License


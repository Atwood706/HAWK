"""
AWDL Standard Library - MCP Call Tool

提供一个通用工具 `mcp_call`：通过 MCP（Model Context Protocol）调用外部 MCP server 的任意 tool。

设计约束（不改 .awdl 语法）：
- 仅使用字符串参数表达 server / tool / arguments（JSON 字符串）
- 输出也以 JSON 字符串返回，避免 AWDL 类型系统不匹配

server 参数格式（当前只实现 stdio）：
- "stdio:<command and args...>"  例如： "stdio:mcp-server-ds"
"""

from __future__ import annotations

import json
import os
import shlex
import importlib
import traceback
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MCPCallTool:
    """
    MCP Call Tool.

    Inputs:
        server: MCP server 启动方式（目前仅支持 stdio:<cmd...>）
        tool: MCP tool name（例如 data-exploration-server 里是 "load_csv"）
        args_json: tool arguments 的 JSON 字符串（例如 {"csv_path":"...", "df_name":"df_1"}）

    Outputs:
        result: CallToolResult 的 JSON 字符串（包含 isError/content 等）
        error: 错误信息（如有）
    """

    timeout_seconds: int = 60

    def execute(self, server: str, tool: str, args_json: str = "{}") -> Dict[str, Any]:
        try:
            result = self._call_mcp(server=server, tool=tool, args_json=args_json)
            return {"result": result, "error": ""}
        except BaseException as exc:
            # AnyIO may raise ExceptionGroup / TaskGroup wrappers; include sub-exceptions for debugging.
            detail = self._format_exception(exc)
            return {"result": "", "error": f"mcp_call failed: {detail}"}

    def _format_exception(self, exc: BaseException) -> str:
        """
        Format exceptions with special handling for ExceptionGroup (Python 3.11+).
        Keep output single-line-ish but include nested causes for diagnosis.
        """
        # Python 3.11+: built-in ExceptionGroup; Python 3.10: may be from `exceptiongroup` backport.
        # Detect generically via the `exceptions` attribute and flatten recursively to show leaf causes.
        leaves: list[BaseException] = []

        def _collect(e: BaseException) -> None:
            subs = getattr(e, "exceptions", None)
            if isinstance(subs, (list, tuple)) and subs:
                for s in subs:
                    if isinstance(s, BaseException):
                        _collect(s)
                return
            leaves.append(e)

        _collect(exc)
        if leaves and leaves != [exc]:
            parts = [f"{type(exc).__name__}({len(leaves)} leaf exception(s))"]
            for i, sub in enumerate(leaves[:5], 1):
                parts.append(f"[{i}] {type(sub).__name__}: {sub}")
            if len(leaves) > 5:
                parts.append(f"... (+{len(leaves) - 5} more)")
            return " | ".join(parts)

        # If user wants full traceback, allow via env var (avoids noisy default).
        if os.environ.get("HAWK_MCP_DEBUG", "").strip() in {"1", "true", "True"}:
            return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()

        return f"{type(exc).__name__}: {exc}"

    def _call_mcp(self, server: str, tool: str, args_json: str) -> str:
        # Lazy import so core AWDL usage doesn’t require MCP unless used.
        # Use dynamic imports to avoid editor/linter missing-import warnings in minimal envs.
        anyio = importlib.import_module("anyio")
        ClientSession = importlib.import_module("mcp.client.session").ClientSession
        stdio_mod = importlib.import_module("mcp.client.stdio")
        StdioServerParameters = stdio_mod.StdioServerParameters
        stdio_client = stdio_mod.stdio_client

        server = (server or "").strip()
        if not server:
            raise ValueError("server is required")

        tool = (tool or "").strip()
        if not tool:
            raise ValueError("tool is required")

        args_json = (args_json or "{}").strip()
        try:
            arguments = json.loads(args_json) if args_json else {}
        except json.JSONDecodeError as e:
            raise ValueError(f"args_json must be valid JSON: {e}") from e

        if arguments is not None and not isinstance(arguments, dict):
            raise ValueError("args_json must decode to a JSON object/dict")

        # Parse stdio:<cmd ...>
        if server.lower().startswith("stdio:"):
            cmdline = server[len("stdio:") :].strip()
        else:
            # Backward-compatible: treat as stdio command line
            cmdline = server

        if not cmdline:
            raise ValueError("stdio command is empty")

        tokens = shlex.split(cmdline, posix=(os.name != "nt"))
        if not tokens:
            raise ValueError("stdio command is empty after parsing")

        command = tokens[0]
        args = tokens[1:]

        async def _run() -> str:
            # On Windows, subprocess stderr must be a real file handle with fileno().
            # Use a temporary file so we can capture server stderr without breaking process creation.
            tmp_err = tempfile.NamedTemporaryFile(
                mode="w+",
                encoding="utf-8",
                errors="replace",
                delete=False,
            )
            tmp_err_path = tmp_err.name
            params = StdioServerParameters(
                command=command,
                args=args,
                # MCP SDK默认只继承“安全环境变量”，在 Windows + conda 下可能导致子进程无法复用当前环境。
                # 这里显式继承当前进程环境，确保像 `python`、`mcp-server-ds` 这类入口运行在同一个 conda env。
                env=dict(os.environ),
                cwd=os.getcwd(),  # keep relative paths consistent with caller
            )
            try:
                async with stdio_client(params, errlog=tmp_err) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        call_result = await session.call_tool(name=tool, arguments=arguments)
                        # pydantic v2 model -> JSON
                        return call_result.model_dump_json(by_alias=True, exclude_none=True)
            except BaseException as e:
                try:
                    tmp_err.flush()
                    tmp_err.seek(0)
                    stderr = tmp_err.read().strip()
                except Exception:
                    stderr = ""
                if stderr:
                    raise RuntimeError(f"{e}\n--- mcp server stderr ---\n{stderr}") from e
                raise
            finally:
                try:
                    tmp_err.close()
                finally:
                    try:
                        os.unlink(tmp_err_path)
                    except Exception:
                        pass

        return anyio.run(_run)

    @classmethod
    def create(cls, config: Optional[Dict[str, Any]] = None) -> "MCPCallTool":
        config = config or {}
        return cls(timeout_seconds=int(config.get("timeout_seconds", 60)))



#!/usr/bin/env python3
"""
E2B MCP Server
==============

Model Context Protocol server exposing E2B sandbox tools to Claude SDK.

This server provides Claude with tools to execute commands, read/write files,
and interact with E2B sandboxes through the MCP protocol.

Tools provided:
- e2b_execute_command: Execute shell commands in E2B sandbox
- e2b_list_files: List files in sandbox directory
- e2b_read_file: Read file contents from sandbox
- e2b_write_file: Write content to file in sandbox
- e2b_run_tests: Run test suite in sandbox

Usage:
    python e2b_mcp_server.py

The server communicates via stdio using the MCP protocol.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.e2b_sandbox_manager import (
    E2BSandboxManager,
    ExecutionResult,
    TestResult,
)

# Try to import MCP - gracefully handle if not installed
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None
    stdio_server = None
    types = None

logging.basicConfig(
    level=logging.INFO,
    format='[E2B-MCP] %(levelname)s: %(message)s',
    stream=sys.stderr  # MCP uses stdout for protocol
)
logger = logging.getLogger(__name__)


class E2BMCPServer:
    """MCP Server exposing E2B sandbox tools."""

    def __init__(self):
        """Initialize E2B MCP server."""
        self.app = Server("e2b-sandbox") if Server else None
        self.sandbox_manager: Optional[E2BSandboxManager] = None
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load E2B configuration from environment."""
        return {
            "e2b_enabled": True,
            "e2b_api_key": os.environ.get("E2B_API_KEY"),
            "default_template": os.environ.get("E2B_TEMPLATE", "node20"),
            "sandbox_timeout_seconds": int(os.environ.get("E2B_TIMEOUT", "600")),
            "sandbox_pool_size": int(os.environ.get("E2B_POOL_SIZE", "3")),
        }

    async def initialize(self):
        """Initialize E2B sandbox manager."""
        if not self.sandbox_manager:
            self.sandbox_manager = E2BSandboxManager(self.config)
            await self.sandbox_manager.initialize()
            logger.info("E2B Sandbox Manager initialized")

    def setup_handlers(self):
        """Register MCP tool handlers."""
        if not self.app:
            logger.error("MCP Server not available - install mcp package")
            return

        @self.app.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available E2B tools."""
            return [
                types.Tool(
                    name="e2b_execute_command",
                    description=(
                        "Execute a shell command in E2B sandbox. "
                        "Returns exit code, stdout, and stderr."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute"
                            },
                            "cwd": {
                                "type": "string",
                                "description": "Working directory (default: /)",
                                "default": "/"
                            },
                            "timeout": {
                                "type": "number",
                                "description": "Timeout in seconds (default: 600)",
                                "default": 600
                            },
                            "persistent": {
                                "type": "boolean",
                                "description": "Keep sandbox alive for reuse",
                                "default": False
                            }
                        },
                        "required": ["command"]
                    }
                ),
                types.Tool(
                    name="e2b_list_files",
                    description="List files in a sandbox directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path (default: /)",
                                "default": "/"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "List recursively",
                                "default": False
                            }
                        }
                    }
                ),
                types.Tool(
                    name="e2b_read_file",
                    description="Read file contents from sandbox",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to file to read"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                types.Tool(
                    name="e2b_write_file",
                    description="Write content to file in sandbox",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to file to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to file"
                            }
                        },
                        "required": ["file_path", "content"]
                    }
                ),
                types.Tool(
                    name="e2b_run_tests",
                    description="Run test suite in sandbox",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "Path to project directory"
                            },
                            "test_command": {
                                "type": "string",
                                "description": "Command to run tests (default: npm test)",
                                "default": "npm test"
                            }
                        },
                        "required": ["project_path"]
                    }
                )
            ]

        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls."""
            await self.initialize()

            if name == "e2b_execute_command":
                result = await self._execute_command(arguments)
            elif name == "e2b_list_files":
                result = await self._list_files(arguments)
            elif name == "e2b_read_file":
                result = await self._read_file(arguments)
            elif name == "e2b_write_file":
                result = await self._write_file(arguments)
            elif name == "e2b_run_tests":
                result = await self._run_tests(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}

            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

    async def _execute_command(self, args: Dict) -> Dict:
        """Execute command in sandbox."""
        try:
            result = await self.sandbox_manager.execute_command(
                command=args["command"],
                cwd=args.get("cwd", "/"),
                timeout_seconds=args.get("timeout", 600),
                persistent_session=args.get("persistent", False)
            )

            return {
                "success": result.success,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_seconds": result.duration_seconds,
                "sandbox_id": result.sandbox_id
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {"error": str(e), "success": False}

    async def _list_files(self, args: Dict) -> Dict:
        """List files in sandbox directory."""
        try:
            path = args.get("path", "/")
            recursive = args.get("recursive", False)

            command = f"ls -la {path}"
            if recursive:
                command = f"find {path} -type f"

            result = await self.sandbox_manager.execute_command(command)

            return {
                "success": result.success,
                "files": result.stdout.strip().split("\n") if result.success else [],
                "path": path
            }
        except Exception as e:
            logger.error(f"List files failed: {e}")
            return {"error": str(e), "success": False}

    async def _read_file(self, args: Dict) -> Dict:
        """Read file from sandbox."""
        try:
            file_path = args["file_path"]
            result = await self.sandbox_manager.execute_command(
                command=f"cat {file_path}"
            )

            return {
                "success": result.success,
                "content": result.stdout if result.success else "",
                "file_path": file_path,
                "error": result.stderr if not result.success else None
            }
        except Exception as e:
            logger.error(f"Read file failed: {e}")
            return {"error": str(e), "success": False}

    async def _write_file(self, args: Dict) -> Dict:
        """Write file to sandbox."""
        try:
            file_path = args["file_path"]
            content = args["content"]

            # Escape content for shell
            escaped_content = content.replace("'", "'\"'\"'")

            result = await self.sandbox_manager.execute_command(
                command=f"echo '{escaped_content}' > {file_path}"
            )

            return {
                "success": result.success,
                "file_path": file_path,
                "bytes_written": len(content),
                "error": result.stderr if not result.success else None
            }
        except Exception as e:
            logger.error(f"Write file failed: {e}")
            return {"error": str(e), "success": False}

    async def _run_tests(self, args: Dict) -> Dict:
        """Run tests in sandbox."""
        try:
            project_path = Path(args["project_path"])
            test_command = args.get("test_command", "npm test")

            result = await self.sandbox_manager.run_tests(
                project_path=project_path,
                test_command=test_command
            )

            return {
                "success": result.success,
                "exit_code": result.exit_code,
                "tests_passed": result.tests_passed,
                "tests_failed": result.tests_failed,
                "tests_skipped": result.tests_skipped,
                "coverage_percentage": result.coverage_percentage,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration_seconds": result.duration_seconds
            }
        except Exception as e:
            logger.error(f"Run tests failed: {e}")
            return {"error": str(e), "success": False}

    async def cleanup(self):
        """Cleanup resources."""
        if self.sandbox_manager:
            await self.sandbox_manager.cleanup()

    async def run(self):
        """Run the MCP server."""
        if not MCP_AVAILABLE:
            logger.error("MCP package not installed. Install with: pip install mcp")
            sys.exit(1)

        self.setup_handlers()
        logger.info("E2B MCP Server started")

        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                self.app.create_initialization_options()
            )


async def main():
    """Main entry point."""
    server = E2BMCPServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

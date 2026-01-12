"""
Claude SDK Client Configuration
===============================

Functions for creating and configuring the Claude Agent SDK client.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from claude_code_sdk.types import HookMatcher

from security import bash_security_hook

# Load environment variables from .env file
load_dotenv()


# Playwright MCP tools for browser automation and testing
# See: https://playwright.dev/docs/intro
PLAYWRIGHT_TOOLS = [
    "mcp__playwright__browser_navigate",
    "mcp__playwright__browser_snapshot",
    "mcp__playwright__browser_click",
    "mcp__playwright__browser_type",
    "mcp__playwright__browser_fill_form",
    "mcp__playwright__browser_select_option",
    "mcp__playwright__browser_hover",
    "mcp__playwright__browser_evaluate",
    "mcp__playwright__browser_take_screenshot",
    "mcp__playwright__browser_wait_for",
    "mcp__playwright__browser_console_messages",
    "mcp__playwright__browser_network_requests",
    "mcp__playwright__browser_close",
    "mcp__playwright__browser_resize",
    "mcp__playwright__browser_press_key",
    "mcp__playwright__browser_drag",
    "mcp__playwright__browser_tabs",
    "mcp__playwright__browser_navigate_back",
    "mcp__playwright__browser_handle_dialog",
    "mcp__playwright__browser_file_upload",
    "mcp__playwright__browser_run_code",
    "mcp__playwright__browser_install",
]

# Context7 MCP tools for documentation lookup
# Used by agents to research libraries and best practices before implementing
# See: https://context7.com
CONTEXT7_TOOLS = [
    "mcp__context7__resolve-library-id",
    "mcp__context7__query-docs",
]

# Built-in tools
BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
]


def create_client(project_dir: Path, model: str) -> ClaudeSDKClient:
    """
    Create a Claude Agent SDK client with multi-layered security.

    Args:
        project_dir: Directory for the project
        model: Claude model to use

    Returns:
        Configured ClaudeSDKClient

    Security layers (defense in depth):
    1. Sandbox - OS-level bash command isolation prevents filesystem escape
    2. Permissions - File operations restricted to project_dir only
    3. Security hooks - Bash commands validated against an allowlist
       (see security.py for ALLOWED_COMMANDS)
    """
    api_key = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if not api_key:
        raise ValueError(
            "CLAUDE_CODE_OAUTH_TOKEN environment variable not set.\n"
            "Run 'claude setup-token' after installing the Claude Code CLI."
        )

    # Create comprehensive security settings
    # Note: Using relative paths ("./**") restricts access to project directory
    # since cwd is set to project_dir
    security_settings = {
        "sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True},
        "permissions": {
            "defaultMode": "acceptEdits",  # Auto-approve edits within allowed directories
            "allow": [
                # Allow all file operations within the project directory
                "Read(./**)",
                "Write(./**)",
                "Edit(./**)",
                "Glob(./**)",
                "Grep(./**)",
                # Bash permission granted here, but actual commands are validated
                # by the bash_security_hook (see security.py for allowed commands)
                "Bash(*)",
                # Allow Playwright MCP tools for browser automation and testing
                *PLAYWRIGHT_TOOLS,
                # Allow Context7 MCP tools for documentation lookup
                *CONTEXT7_TOOLS,
            ],
        },
    }

    # Ensure project directory exists before creating settings file
    project_dir.mkdir(parents=True, exist_ok=True)

    # Write settings to a file in the project directory
    settings_file = project_dir / ".claude_settings.json"
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)

    print(f"Created security settings at {settings_file}")
    print("   - Sandbox enabled (OS-level bash isolation)")
    print(f"   - Filesystem restricted to: {project_dir.resolve()}")
    print("   - Bash commands restricted to allowlist (see security.py)")
    print("   - MCP servers:")
    print("     • playwright (browser automation and testing)")
    print("     • context7 (documentation lookup for best practices)")
    print()

    # Get Context7 API key from environment
    context7_api_key = os.environ.get("CONTEXT7_API_KEY", "")

    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            system_prompt="You are an expert full-stack developer building a production-quality web application. You track your work using a local checklist system, test your application using Playwright, and use Context7 to research best practices and documentation before implementing features.",
            allowed_tools=[
                *BUILTIN_TOOLS,
                *PLAYWRIGHT_TOOLS,
                *CONTEXT7_TOOLS,
            ],
            mcp_servers={
                # Playwright MCP server for browser automation
                # See: https://playwright.dev/docs/intro
                "playwright": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-playwright"]},
                # Context7 MCP server for documentation lookup
                # See: https://context7.com
                "context7": {
                    "command": "npx",
                    "args": ["-y", "@context7/mcp-server"],
                    "env": {"CONTEXT7_API_KEY": context7_api_key}
                },
            },
            hooks={
                "PreToolUse": [
                    HookMatcher(matcher="Bash", hooks=[bash_security_hook]),
                ],
            },
            max_turns=1000,
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),  # Use absolute path
        )
    )

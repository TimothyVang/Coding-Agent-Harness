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

# Filesystem MCP tools for file operations
# See: https://github.com/modelcontextprotocol/servers
FILESYSTEM_TOOLS = [
    "mcp__filesystem__read_file",
    "mcp__filesystem__write_file",
    "mcp__filesystem__list_directory",
    "mcp__filesystem__create_directory",
    "mcp__filesystem__move_file",
    "mcp__filesystem__search_files",
    "mcp__filesystem__get_file_info",
]

# GitHub MCP tools for version control and collaboration
# See: https://github.com/modelcontextprotocol/servers
GITHUB_TOOLS = [
    "mcp__github__create_or_update_file",
    "mcp__github__search_repositories",
    "mcp__github__create_repository",
    "mcp__github__get_file_contents",
    "mcp__github__push_files",
    "mcp__github__create_issue",
    "mcp__github__create_pull_request",
    "mcp__github__fork_repository",
    "mcp__github__create_branch",
]

# Git MCP tools for local version control
# See: https://github.com/modelcontextprotocol/servers
GIT_TOOLS = [
    "mcp__git__status",
    "mcp__git__diff",
    "mcp__git__commit",
    "mcp__git__add",
    "mcp__git__log",
    "mcp__git__show",
]

# Memory MCP tools for knowledge graph-based memory
# See: https://github.com/modelcontextprotocol/servers
MEMORY_TOOLS = [
    "mcp__memory__create_entities",
    "mcp__memory__create_relations",
    "mcp__memory__search_nodes",
    "mcp__memory__open_nodes",
    "mcp__memory__delete_entities",
    "mcp__memory__delete_relations",
]

# Sequential Thinking MCP tools for dynamic problem-solving
# See: https://github.com/modelcontextprotocol/servers
SEQUENTIAL_THINKING_TOOLS = [
    "mcp__sequential_thinking__start_sequence",
    "mcp__sequential_thinking__continue_sequence",
    "mcp__sequential_thinking__get_sequence",
]

# Fetch MCP tools for web content retrieval
# See: https://github.com/modelcontextprotocol/servers
FETCH_TOOLS = [
    "mcp__fetch__fetch",
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
                # Allow Filesystem MCP tools for file operations
                *FILESYSTEM_TOOLS,
                # Allow GitHub MCP tools for version control
                *GITHUB_TOOLS,
                # Allow Git MCP tools for local version control
                *GIT_TOOLS,
                # Allow Memory MCP tools for knowledge graph memory
                *MEMORY_TOOLS,
                # Allow Sequential Thinking MCP tools for problem-solving
                *SEQUENTIAL_THINKING_TOOLS,
                # Allow Fetch MCP tools for web content retrieval
                *FETCH_TOOLS,
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
    print("   - MCP servers (8 total):")
    print("     • playwright (browser automation and testing)")
    print("     • context7 (documentation lookup)")
    print("     • filesystem (file operations)")
    print("     • github (version control and collaboration)")
    print("     • git (local version control)")
    print("     • memory (knowledge graph-based memory)")
    print("     • sequential-thinking (dynamic problem-solving)")
    print("     • fetch (web content retrieval)")
    print()

    # Get Context7 API key from environment
    context7_api_key = os.environ.get("CONTEXT7_API_KEY", "")

    # Get GitHub token from environment (optional - GitHub MCP can use OAuth)
    github_token = os.environ.get("GITHUB_TOKEN", "")

    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            system_prompt="""You are an expert full-stack developer building production-quality applications with an advanced AI development platform.

You have access to:
- Local checklist system for task tracking
- Playwright for browser automation and testing
- Context7 for documentation lookup and best practices
- Filesystem operations for file management
- GitHub integration for version control and collaboration
- Git for local version control operations
- Knowledge graph memory for persistent learning
- Sequential thinking for complex problem-solving
- Web fetch for content retrieval

Use these tools strategically to build high-quality software efficiently.""",
            allowed_tools=[
                *BUILTIN_TOOLS,
                *PLAYWRIGHT_TOOLS,
                *CONTEXT7_TOOLS,
                *FILESYSTEM_TOOLS,
                *GITHUB_TOOLS,
                *GIT_TOOLS,
                *MEMORY_TOOLS,
                *SEQUENTIAL_THINKING_TOOLS,
                *FETCH_TOOLS,
            ],
            mcp_servers={
                # Playwright MCP server for browser automation
                # See: https://playwright.dev/docs/intro
                "playwright": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-playwright"]
                },
                # Context7 MCP server for documentation lookup
                # See: https://context7.com
                "context7": {
                    "command": "npx",
                    "args": ["-y", "@context7/mcp-server"],
                    "env": {"CONTEXT7_API_KEY": context7_api_key}
                },
                # Filesystem MCP server for file operations
                # See: https://github.com/modelcontextprotocol/servers
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(project_dir.resolve())]
                },
                # GitHub MCP server for version control
                # See: https://github.com/modelcontextprotocol/servers
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": github_token} if github_token else {}
                },
                # Git MCP server for local version control
                # See: https://github.com/modelcontextprotocol/servers
                "git": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-git", "--repository", str(project_dir.resolve())]
                },
                # Memory MCP server for knowledge graph
                # See: https://github.com/modelcontextprotocol/servers
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"]
                },
                # Sequential Thinking MCP server for problem-solving
                # See: https://github.com/modelcontextprotocol/servers
                "sequential-thinking": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
                },
                # Fetch MCP server for web content retrieval
                # See: https://github.com/modelcontextprotocol/servers
                "fetch": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-fetch"]
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

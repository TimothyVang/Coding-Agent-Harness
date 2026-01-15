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
# Using wildcard to allow all filesystem tools (future-proof)
FILESYSTEM_TOOLS = [
    "mcp__filesystem__*",
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

# Linear MCP tools for project management
# Official Linear MCP server at mcp.linear.app
# See: https://linear.app/docs/mcp
LINEAR_TOOLS = [
    # Team & Project discovery
    "mcp__linear__list_teams",
    "mcp__linear__get_team",
    "mcp__linear__list_projects",
    "mcp__linear__get_project",
    "mcp__linear__create_project",
    "mcp__linear__update_project",
    # Issue management
    "mcp__linear__list_issues",
    "mcp__linear__get_issue",
    "mcp__linear__create_issue",
    "mcp__linear__update_issue",
    "mcp__linear__list_my_issues",
    # Comments
    "mcp__linear__list_comments",
    "mcp__linear__create_comment",
    # Workflow
    "mcp__linear__list_issue_statuses",
    "mcp__linear__get_issue_status",
    "mcp__linear__list_issue_labels",
    # Users
    "mcp__linear__list_users",
    "mcp__linear__get_user",
]

# E2B MCP tools for sandboxed execution (CRITICAL SECURITY)
# All bash commands MUST go through E2B sandbox to prevent host system compromise
E2B_TOOLS = [
    "mcp__e2b__e2b_execute_command",
    "mcp__e2b__e2b_list_files",
    "mcp__e2b__e2b_read_file",
    "mcp__e2b__e2b_write_file",
    "mcp__e2b__e2b_run_tests",
]

# Built-in tools (NOTE: Bash intentionally excluded - use E2B_TOOLS instead)
BUILTIN_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    # "Bash" - REMOVED FOR SECURITY: Direct bash is blocked, use E2B sandbox instead
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

    # SECURITY: Require E2B sandbox for command execution
    # This prevents agents from running commands directly on the host system
    e2b_api_key = os.environ.get("E2B_API_KEY")
    if not e2b_api_key:
        raise ValueError(
            "SECURITY: E2B_API_KEY environment variable not set.\n"
            "E2B sandbox is REQUIRED for safe command execution.\n"
            "Get an API key at https://e2b.dev and add to .env file.\n"
            "Without E2B, bash commands would execute directly on your system!"
        )

    # Require Linear API key for project management
    linear_api_key = os.environ.get("LINEAR_API_KEY")
    if not linear_api_key:
        raise ValueError(
            "LINEAR_API_KEY environment variable not set.\n"
            "Get your API key from: https://linear.app/YOUR-TEAM/settings/api"
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
                # NOTE: Direct Bash is BLOCKED - all commands go through E2B sandbox
                # The bash_security_hook blocks all Bash tool usage and redirects to E2B
                # Allow E2B MCP tools for sandboxed command execution (CRITICAL)
                *E2B_TOOLS,
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
                # Allow Linear MCP tools for project management
                *LINEAR_TOOLS,
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
    print("   - E2B SANDBOX ENFORCED - all bash commands run in cloud sandbox")
    print(f"   - Filesystem restricted to: {project_dir.resolve()}")
    print("   - Direct Bash tool BLOCKED (redirects to E2B)")
    print("   - MCP servers (10 total):")
    print("     • e2b (CRITICAL - sandboxed command execution)")
    print("     • playwright (browser automation and testing)")
    print("     • context7 (documentation lookup)")
    print("     • filesystem (file operations)")
    print("     • github (version control and collaboration)")
    print("     • git (local version control)")
    print("     • memory (knowledge graph-based memory)")
    print("     • sequential-thinking (dynamic problem-solving)")
    print("     • fetch (web content retrieval)")
    print("     • linear (project management and issue tracking)")
    print()

    # Get Context7 API key from environment
    context7_api_key = os.environ.get("CONTEXT7_API_KEY", "")

    # Get GitHub token from environment (optional - GitHub MCP can use OAuth)
    github_token = os.environ.get("GITHUB_TOKEN", "")

    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            system_prompt="""You are an expert full-stack developer building production-quality applications with an advanced AI development platform.

IMPORTANT SECURITY REQUIREMENT:
All shell/bash commands MUST be executed through the E2B sandbox for security.
DO NOT use the Bash tool directly - it will be blocked.
Instead, use these E2B tools for command execution:
  - mcp__e2b__e2b_execute_command: Execute shell commands safely in sandbox
  - mcp__e2b__e2b_list_files: List directory contents in sandbox
  - mcp__e2b__e2b_read_file: Read file contents from sandbox
  - mcp__e2b__e2b_write_file: Write file contents in sandbox
  - mcp__e2b__e2b_run_tests: Run test suites in sandbox

You have access to:
- E2B sandbox for secure command execution (REQUIRED for all bash commands)
- Local checklist system for task tracking
- Linear for project management and issue tracking
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
                *E2B_TOOLS,  # CRITICAL: Sandboxed command execution
                *PLAYWRIGHT_TOOLS,
                *CONTEXT7_TOOLS,
                *FILESYSTEM_TOOLS,
                *GITHUB_TOOLS,
                *GIT_TOOLS,
                *MEMORY_TOOLS,
                *SEQUENTIAL_THINKING_TOOLS,
                *FETCH_TOOLS,
                *LINEAR_TOOLS,  # Project management and issue tracking
            ],
            mcp_servers={
                # E2B MCP server for sandboxed command execution (CRITICAL SECURITY)
                # This is the ONLY safe way to run bash commands - prevents host system compromise
                "e2b": {
                    "command": "python",
                    "args": [str(Path(__file__).parent / "mcp_servers" / "e2b" / "e2b_mcp_server.py")],
                    "env": {"E2B_API_KEY": e2b_api_key}
                },
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
                # Linear MCP server for project management
                # Uses Streamable HTTP transport (recommended over SSE)
                # See: https://linear.app/docs/mcp
                "linear": {
                    "type": "http",
                    "url": "https://mcp.linear.app/mcp",
                    "headers": {
                        "Authorization": f"Bearer {linear_api_key}"
                    }
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

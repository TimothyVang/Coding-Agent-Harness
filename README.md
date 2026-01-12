# Universal AI Development Platform

A comprehensive autonomous development system powered by the Claude Agent SDK. Build, enhance, and manage multiple software projects simultaneously with a coordinated **agent army**.

## 🚀 What's New: Agent Army System

This platform has evolved from a single-agent harness into a **Universal AI Development Platform** that can:

- **Manage Multiple Projects**: Build and enhance multiple applications concurrently
- **Specialized Agent Types**: 9 types of agents (Architect, Builder, TestGen, Verifier, Reviewer, DevOps, Documentation, Reporter, Analytics)
- **Agent Memory & Learning**: Agents learn from mistakes, remember patterns, and continuously improve
- **Automated Testing**: Test Generator creates comprehensive test suites using Context7 documentation lookup
- **Quality Verification**: Verifier agents ensure 100% completion with blocking subtask mechanism
- **Load Balancing**: Intelligent agent allocation based on project workload
- **Self-Improving**: Analytics agent analyzes patterns and provides actionable insights
- **Markdown Reports**: Comprehensive reports for reviewing completed work
- **Multi-Domain Support**: Web apps, CLI tools, APIs, desktop applications

## 📋 Phase 1 Implementation Status (COMPLETED)

**Infrastructure Layer** - ✅ 100% Complete
- Enhanced Checklist Manager (556 lines) - Production-ready
- Project Registry (435 lines) - Multi-project support
- Task Queue (557 lines) - Priority-based routing
- Message Bus (482 lines) - Pub/sub communication
- Agent Memory (555 lines) - Pattern learning system
- Base Agent (463 lines) - Foundation class

**MCP Integration** - ✅ 6 New Servers Added
- Filesystem MCP - File operations
- GitHub MCP - Version control & collaboration
- Git MCP - Local version control
- Memory MCP - Knowledge graph memory
- Sequential Thinking MCP - Enhanced problem-solving
- Fetch MCP - Web content retrieval

**Application Layer** - ⏳ 5/9 Agents Implemented (56%)
- ✅ Architect Agent (600+ lines) - Planning and architectural design
- ✅ Builder Agent (380 lines) - Feature implementation
- ✅ Test Generator Agent (425 lines) - Automated test creation with Context7
- ✅ Verifier Agent (465 lines) - Quality assurance & verification
- ✅ Reviewer Agent (580 lines) - Code review and quality assessment
- ⏳ 4 remaining agents (DevOps, Documentation, Reporter, Analytics)

**Orchestration** - ✅ Multi-Agent Coordination
- Agent Orchestrator (updated) - Multi-agent coordination
- 5-agent pool (Architect, Builder, TestGenerator, Verifier, Reviewer)
- Task routing by agent type
- Health monitoring
- Full workflow support (Architecture → Implementation → Testing → Verification → Review)

**Testing** - ✅ Comprehensive Test Coverage
- Builder Agent test suite (4 tests, all passing)
- Quality Pipeline test suite (7 tests, all passing)
  - Verifier and TestGenerator initialization
  - Blocking subtask workflow verification
  - Test type determination logic
  - System prompt validation
- Architect & Reviewer test suite (7 tests, all passing)
  - Agent initialization and configuration
  - Requirements analysis and complexity determination
  - Quality score calculation
  - Component design logic
  - System prompt validation
- Total: 18 integration tests, 100% passing

**Phase 2 COMPLETE**: Quality Pipeline with blocking task mechanism

**Phase 3 COMPLETE**: Architecture & Review Pipeline
- ArchitectAgent: Planning and design before implementation
- ReviewerAgent: Code review and quality assessment
- Full workflow: Architect → Builder → TestGen → Verifier → Reviewer

**Next Phase**: Implement remaining 4 specialized agents (DevOps, Documentation, Reporter, Analytics)

## Key Features

### Single-Agent Demo (Original)
- **Local Checklist System**: All work is tracked in `.project_checklist.json` with automatic `CHECKLIST.md` generation
- **Real-time Visibility**: Check `CHECKLIST.md` to see project progress at any time
- **Session Handoff**: Agents communicate via checklist notes and session logs
- **Two-Agent Pattern**: Initializer creates checklist, coding agents implement tasks
- **Browser Testing**: Playwright MCP for comprehensive UI verification

### Agent Army Platform (New)
- **Enhanced Checklist**: Subtask support, blocking mechanism, test coverage tracking
- **Project Registry**: Multi-project management with workload distribution
- **Task Queue**: Priority-based task distribution (CRITICAL > HIGH > MEDIUM > LOW)
- **Message Bus**: Inter-agent communication via pub/sub messaging
- **Agent Memory**: Persistent learning with markdown-based memory storage
- **Context7 Integration**: Documentation lookup for best practices before implementation
- **Windows Compatible**: Designed to work seamlessly on Windows systems
- **Claude Opus 4.5**: Uses Claude's most capable model by default

## Prerequisites

### 1. Install Claude Code CLI and Python SDK

```bash
# Install Claude Code CLI (latest version required)
npm install -g @anthropic-ai/claude-code

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set Up Environment Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```env
# Claude Code OAuth Token (Required)
# Get this by running: claude setup-token
CLAUDE_CODE_OAUTH_TOKEN=your-claude-oauth-token-here

# Anthropic API Key (if using direct API access)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Context7 API Key (for documentation lookup)
# Get this from: https://context7.com
CONTEXT7_API_KEY=your-context7-api-key-here

# Agent Army Configuration
MAX_CONCURRENT_AGENTS=10
AGENT_TIMEOUT=3600
DEFAULT_MODEL=claude-opus-4-5-20251101
```

**Generate Claude Code OAuth Token:**

```bash
# All platforms
claude setup-token
```

The `.env` file will be automatically loaded by the harness.

### 3. Verify Installation

```bash
claude --version  # Should be latest version
pip show claude-code-sdk  # Check SDK is installed
```

## Quick Start

**Windows:**
```powershell
python autonomous_agent_demo.py --project-dir ./my_project
```

**Linux/Mac:**
```bash
python autonomous_agent_demo.py --project-dir ./my_project
```

For testing with limited iterations:
```bash
python autonomous_agent_demo.py --project-dir ./my_project --max-iterations 3
```

## Core Infrastructure

The platform is built on five foundational components:

### 1. Enhanced Checklist Manager (`core/enhanced_checklist.py`)
Advanced task tracking with:
- **Subtask Support**: Break down tasks into smaller pieces
- **Blocking Mechanism**: Critical tasks halt project until resolved
- **Completion Tracking**: Calculate % completion based on subtasks
- **Test Coverage**: Track unit, integration, E2E, and API tests per task
- **Agent Assignment**: Know which agent is working on what

### 2. Project Registry (`core/project_registry.py`)
Multi-project management:
- Register and track multiple projects simultaneously
- Calculate workload distribution for load balancing
- Project status tracking (active, paused, completed, archived)
- Automatic task statistics updates

### 3. Task Queue (`core/task_queue.py`)
Priority-based task distribution:
- **Priority Levels**: CRITICAL > HIGH > MEDIUM > LOW
- **Agent Type Matching**: Right agent for the right task
- **Dependency Management**: Tasks wait for dependencies
- **Retry Logic**: Automatic retry for failed tasks (up to 3 attempts)
- **Blocking Awareness**: Blocking tasks go to front of queue

### 4. Message Bus (`core/message_bus.py`)
Inter-agent communication:
- **Pub/Sub Pattern**: Agents subscribe to channels
- **Direct Messaging**: Send to specific agents
- **Message Persistence**: File-based storage (extensible to Redis/DB)
- **Callback Support**: React to messages in real-time

### 5. Agent Memory (`core/agent_memory.py`)
Learning and self-improvement:
- **Persistent Memory**: Markdown files per agent
- **Pattern Learning**: Remember successful approaches
- **Mistake Tracking**: Never make the same error twice
- **Self-Reflection**: Periodic performance analysis
- **Cross-Agent Learning**: Share insights across team

## Agent Architecture

### Base Agent (`agents/base_agent.py`)
Foundation for all agent types:
- **Task Lifecycle**: before_task → execute_task → after_task hooks
- **Memory Integration**: Load patterns, record results
- **Error Handling**: Graceful failure with retry logic
- **Performance Tracking**: Statistics on success rate, duration
- **Message Bus**: Communication with other agents

### Specialized Agents (Planned)
1. **Architect Agent**: Planning and design
2. **Builder Agent**: Feature implementation
3. **Test Generator Agent**: Automated test creation with Context7
4. **Verifier Agent**: Quality assurance, creates blocking subtasks
5. **Reviewer Agent**: Code review
6. **DevOps Agent**: Infrastructure and deployment
7. **Documentation Agent**: Documentation generation
8. **Reporter Agent**: Markdown report creation
9. **Analytics Agent**: Pattern analysis and insights

## How It Works

### Checklist-Centric Workflow

```
┌─────────────────────────────────────────────────────────────┐
│              CHECKLIST-INTEGRATED WORKFLOW                  │
├─────────────────────────────────────────────────────────────┤
│  app_spec.txt ──► Initializer Agent ──► Checklist (30-50)  │
│                                              │               │
│                    ┌─────────────────────────▼──────────┐   │
│                    │   LOCAL CHECKLIST SYSTEM           │   │
│                    │  .project_checklist.json           │   │
│                    │  ┌────────────────────────────┐    │   │
│                    │  │ Task: Auth - Login flow    │    │   │
│                    │  │ Status: Todo → In Progress │    │   │
│                    │  │ Notes: [implementation]    │    │   │
│                    │  └────────────────────────────┘    │   │
│                    │  Automatically generates:          │   │
│                    │  CHECKLIST.md (markdown view)      │   │
│                    └────────────────────────────────────┘   │
│                                              │               │
│                    Coding Agent reads checklist             │
│                    ├── Find next Todo task                  │
│                    ├── Update status to In Progress         │
│                    ├── Implement & test with Playwright     │
│                    ├── Add note with implementation details │
│                    ├── Update status to Done                │
│                    └── Export updated CHECKLIST.md          │
└─────────────────────────────────────────────────────────────┘
```

### Two-Agent Pattern

1. **Initializer Agent (Session 1):**
   - Reads `app_spec.txt`
   - Creates 30-50 tasks in the checklist system
   - Sets up project structure, `init.sh`, and git
   - Generates initial `CHECKLIST.md`

2. **Coding Agent (Sessions 2+):**
   - Reads checklist to find next Todo task
   - Runs verification tests on previously completed features
   - Claims task (status → In Progress)
   - Implements the feature
   - Tests via Playwright browser automation
   - Adds implementation notes to task
   - Marks complete (status → Done)
   - Updates `CHECKLIST.md` automatically

### Session Handoff via Checklist

Agents communicate through:
- **Task Notes**: Implementation details, blockers, context
- **Session Logs**: Session summaries and handoff notes stored in checklist
- **Task Status**: Todo / In Progress / Done workflow
- **CHECKLIST.md**: Always up-to-date markdown view of all tasks

## Environment Variables

Configure these in `.env` file:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code OAuth token (from `claude setup-token`) | Yes | - |
| `ANTHROPIC_API_KEY` | Anthropic API key (for direct API access) | Optional | - |
| `CONTEXT7_API_KEY` | Context7 API key (for documentation lookup) | Recommended | - |
| `MAX_CONCURRENT_AGENTS` | Maximum number of concurrent agents | No | 10 |
| `AGENT_TIMEOUT` | Agent timeout in seconds | No | 3600 |
| `DEFAULT_MODEL` | Claude model to use | No | claude-opus-4-5-20251101 |
| `LOG_LEVEL` | Logging level | No | INFO |
| `DASHBOARD_PORT` | Dashboard port (future) | No | 8080 |

See `.env.example` for all available configuration options.

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir` | Directory for the project | `./autonomous_demo_project` |
| `--max-iterations` | Max agent iterations | Unlimited |
| `--model` | Claude model to use | `claude-opus-4-5-20251101` |

## Project Structure

```
agent-harness/
├── autonomous_agent_demo.py  # Main entry point (single-agent demo)
├── agent.py                  # Agent session logic
├── client.py                 # Claude SDK + MCP client configuration (8 MCP servers)
├── orchestrator.py           # Agent orchestrator for multi-agent coordination (NEW)
├── checklist_manager.py      # Local checklist system for task tracking
├── security.py               # Bash command allowlist and validation
├── progress.py               # Progress tracking utilities
├── prompts.py                # Prompt loading utilities
├── core/                     # Core infrastructure
│   ├── __init__.py
│   ├── enhanced_checklist.py # Enhanced checklist with subtasks & blocking
│   ├── project_registry.py   # Multi-project management
│   ├── task_queue.py         # Priority-based task distribution
│   ├── message_bus.py        # Inter-agent communication
│   └── agent_memory.py       # Agent learning and memory
├── agents/                   # Agent army
│   ├── __init__.py
│   ├── base_agent.py         # Foundation class for all agents
│   └── builder_agent.py      # Builder agent for feature implementation (NEW)
├── tests/                    # Integration tests (NEW)
│   └── test_builder_agent.py # Builder agent test suite
├── prompts/
│   ├── app_spec.txt          # Application specification
│   ├── initializer_prompt.md # First session prompt (creates checklist)
│   └── coding_prompt.md      # Continuation session prompt (works tasks)
├── .env.example              # Environment configuration template
├── .env                      # Your API keys (not committed)
├── ARCHITECTURE.md           # Complete system architecture documentation
└── requirements.txt          # Python dependencies
```

## Generated Project Structure

After running, your project directory will contain:

```
my_project/
├── .project_checklist.json   # Checklist state (JSON format)
├── CHECKLIST.md              # Human-readable checklist (auto-generated)
├── checklist_manager.py      # Copied from harness for agent use
├── app_spec.txt              # Copied specification
├── init.sh                   # Environment setup script
├── .claude_settings.json     # Security settings
└── [application files]       # Generated application code
```

## MCP Servers Used

The platform integrates 8 Model Context Protocol (MCP) servers for enhanced capabilities:

| Server | Transport | Purpose | Status |
|--------|-----------|---------|--------|
| **Playwright** | stdio | Browser automation for UI testing and verification | ✅ Active |
| **Context7** | stdio | Documentation lookup for libraries and best practices | ✅ Active |
| **Filesystem** | stdio | File operations (read, write, search, manage) | ✅ Active |
| **GitHub** | stdio | Version control and collaboration (repos, PRs, issues) | ✅ Active |
| **Git** | stdio | Local version control operations (commit, diff, log) | ✅ Active |
| **Memory** | stdio | Knowledge graph-based persistent memory | ✅ Active |
| **Sequential Thinking** | stdio | Dynamic problem-solving through thought sequences | ✅ Active |
| **Fetch** | stdio | Web content retrieval and conversion | ✅ Active |

**Official MCP Documentation:**
- MCP Servers Repository: https://github.com/modelcontextprotocol/servers
- Playwright MCP: https://playwright.dev/docs/intro
- Context7 MCP: https://context7.com

All MCP servers are official Anthropic reference implementations and 100% free to use.

## Security Model

This harness uses defense-in-depth security (see `security.py` and `client.py`):

1. **OS-level Sandbox:** Bash commands run in an isolated environment
2. **Filesystem Restrictions:** File operations restricted to project directory
3. **Bash Allowlist:** Only specific commands permitted (npm, node, git, etc.)
4. **MCP Permissions:** Tools explicitly allowed in security settings

## Viewing Progress

You can check project progress at any time:

1. **Read CHECKLIST.md** - Human-readable markdown with all tasks and status
2. **Check .project_checklist.json** - Full JSON data including notes and session logs
3. **Use Python** to query the checklist:
   ```python
   from pathlib import Path
   from checklist_manager import ChecklistManager

   manager = ChecklistManager(Path("./my_project"))
   summary = manager.get_progress_summary()
   print(f"Progress: {summary['Done']}/{sum(summary.values())} tasks complete")
   ```

## Customization

### Changing the Application

Edit `prompts/app_spec.txt` to specify a different application to build.

### Adjusting Task Count

The initializer agent will automatically create 30-50 tasks based on the complexity
of your `app_spec.txt`. The agent determines the optimal number.

### Modifying Allowed Commands

Edit `security.py` to add or remove commands from `ALLOWED_COMMANDS`.

## Troubleshooting

**"CLAUDE_CODE_OAUTH_TOKEN not set"**
Run `claude setup-token` to generate a token, then export/set it as an environment variable.

**"Appears to hang on first run"**
Normal behavior. The initializer is creating the checklist and setting up the project.
Watch for `[Tool: ...]` output indicating progress.

**"Command blocked by security hook"**
The agent tried to run a disallowed command. Add it to `ALLOWED_COMMANDS` in `security.py` if needed.

**"Playwright MCP not working"**
Ensure you have Node.js installed. The MCP server is installed automatically via npx.
Try running: `npx -y @modelcontextprotocol/server-playwright` manually to test.

## Windows-Specific Notes

- Use PowerShell or Command Prompt for setting environment variables
- The harness uses bash commands internally but runs them through Git Bash (included with Git for Windows)
- Ensure Git for Windows is installed: https://git-scm.com/download/win
- Path separators are handled automatically by Python's `pathlib`

## License

MIT License - see [LICENSE](LICENSE) for details.

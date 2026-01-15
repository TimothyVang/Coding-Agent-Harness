# Universal AI Development Platform

A comprehensive autonomous development system powered by the Claude Agent SDK. Build, enhance, and manage multiple software projects simultaneously with a coordinated **agent army**.

## 🚀 Multi-Agent Orchestrator

This platform uses a **Multi-Agent Orchestrator** that coordinates 13 specialized agents:

- **Architect Agent**: Planning and design - analyzes requirements, designs architecture
- **Builder Agent**: Feature implementation - writes code, creates tests
- **Test Generator Agent**: Automated test creation with Context7 documentation lookup
- **Verifier Agent**: Quality assurance - ensures 100% completion with blocking subtasks
- **Reviewer Agent**: Code review - checks quality, security, performance
- **DevOps Agent**: CI/CD pipelines, containerization, cloud deployment
- **Documentation Agent**: API docs, user guides, technical specs
- **Reporter Agent**: Project status reports, sprint summaries
- **Analytics Agent**: Pattern analysis, bottleneck detection, optimization recommendations
- **Refactor Agent**: Code quality, technical debt reduction
- **Database Agent**: Schema design, migrations, query optimization
- **UI Design Agent**: UI/UX, WCAG accessibility validation, responsive design
- **E2B Sandbox Agent**: Secure sandboxed code execution

## 🔒 Security Model

**All code execution runs in E2B cloud sandboxes** - never on your local machine.

| Layer | Protection |
|-------|------------|
| **E2B Sandbox** | All bash commands execute in isolated cloud VMs |
| **Hard-Fail** | System refuses to run if E2B unavailable (no silent fallback) |
| **Shell Injection** | All paths escaped with `shlex.quote()` |
| **Bash Blocking** | Direct Bash tool blocked, redirects to E2B MCP tools |
| **File Locking** | Concurrent access protected with `filelock` |

## Prerequisites

### 1. Install Dependencies

```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your API keys:

```env
# Required
CLAUDE_CODE_OAUTH_TOKEN=your-token    # Run: claude setup-token
E2B_API_KEY=your-e2b-key              # Get from: https://e2b.dev

# Recommended
CONTEXT7_API_KEY=your-context7-key    # Get from: https://context7.com

# Optional
ANTHROPIC_API_KEY=your-anthropic-key
MAX_CONCURRENT_AGENTS=10
AGENT_TIMEOUT=3600
DEFAULT_MODEL=claude-opus-4-5-20251101
```

### 3. Verify Installation

```bash
claude --version
pip show claude-code-sdk
python verify_fixes.py  # Verify all security fixes
```

## Quick Start

### Run the Orchestrator

**Windows (double-click or command line):**
```powershell
python run_orchestrator.py
# Or double-click: run_orchestrator.bat
```

**Linux/Mac:**
```bash
python run_orchestrator.py
```

The orchestrator will:
1. Load your project spec from `prompts/dfir_spec.txt`
2. Initialize 13 specialized agents
3. Create/resume the project checklist
4. Coordinate agents to complete tasks

Press `Ctrl+C` to stop gracefully.

### Custom Project

Edit the launcher or create your own:

```python
import asyncio
from pathlib import Path
from orchestrator import AgentOrchestrator

async def main():
    orchestrator = AgentOrchestrator()

    orchestrator.register_project(
        name="My Project",
        path=Path("./my_project"),
        spec_file=Path("./prompts/my_spec.txt"),
        priority=1
    )

    await orchestrator.start()

asyncio.run(main())
```

## Core Infrastructure

### 1. Enhanced Checklist Manager (`core/enhanced_checklist.py`)
- Subtask support with blocking mechanism
- Test coverage tracking per task
- Agent assignment tracking
- Automatic CHECKLIST.md generation

### 2. Project Registry (`core/project_registry.py`)
- Multi-project management
- Workload distribution and load balancing
- Project status tracking (active, paused, completed)

### 3. Task Queue (`core/task_queue.py`)
- Priority levels: CRITICAL > HIGH > MEDIUM > LOW
- Agent type matching
- Dependency management
- Automatic retry (up to 3 attempts)

### 4. Message Bus (`core/message_bus.py`)
- Pub/sub inter-agent communication
- Direct messaging to specific agents
- File-based persistence with locking

### 5. Agent Memory (`core/agent_memory.py`)
- Persistent markdown-based memory per agent
- Pattern learning from successes
- Mistake tracking to avoid repeated errors

### 6. E2B Sandbox Manager (`core/e2b_sandbox_manager.py`)
- Cloud-based isolated execution
- Hard-fail if unavailable (no local fallback)
- Shell injection protection

## Project Structure

```
Coding-Agent-Harness/
├── run_orchestrator.py       # Main entry point
├── run_orchestrator.bat      # Windows launcher
├── orchestrator.py           # Multi-agent coordinator
├── client.py                 # Claude SDK + 9 MCP servers
├── security.py               # Bash blocking, E2B redirect
├── verify_fixes.py           # Security verification script
├── core/
│   ├── enhanced_checklist.py # Task tracking with subtasks
│   ├── project_registry.py   # Multi-project management
│   ├── task_queue.py         # Priority-based distribution
│   ├── message_bus.py        # Inter-agent communication
│   ├── agent_memory.py       # Learning and memory
│   └── e2b_sandbox_manager.py # Sandboxed execution
├── agents/
│   ├── base_agent.py         # Foundation class
│   ├── architect_agent.py    # Planning and design
│   ├── builder_agent.py      # Feature implementation
│   ├── test_generator_agent.py # Test creation
│   ├── verifier_agent.py     # Quality assurance
│   ├── reviewer_agent.py     # Code review
│   ├── devops_agent.py       # Infrastructure
│   ├── documentation_agent.py # Documentation
│   ├── reporter_agent.py     # Reports
│   ├── analytics_agent.py    # Pattern analysis
│   ├── refactor_agent.py     # Code quality
│   ├── database_agent.py     # Schema design
│   └── ui_design_agent.py    # UI/UX design
├── mcp_servers/
│   └── e2b/
│       └── e2b_mcp_server.py # E2B sandbox MCP server
├── prompts/
│   ├── app_spec.txt          # Default app specification
│   ├── dfir_spec.txt         # Rust-DFIR specification
│   ├── initializer_prompt.md # Checklist creation prompt
│   └── coding_prompt.md      # Task implementation prompt
├── tests/                    # Integration tests
├── .env.example              # Environment template
└── requirements.txt          # Python dependencies
```

## MCP Servers (9 Total)

| Server | Purpose |
|--------|---------|
| **E2B** | Sandboxed command execution (CRITICAL) |
| **Playwright** | Browser automation and UI testing |
| **Context7** | Documentation lookup |
| **Filesystem** | File operations |
| **GitHub** | Version control and PRs |
| **Git** | Local git operations |
| **Memory** | Knowledge graph memory |
| **Sequential Thinking** | Problem-solving |
| **Fetch** | Web content retrieval |

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                 MULTI-AGENT ORCHESTRATOR                     │
├─────────────────────────────────────────────────────────────┤
│  Project Spec ──► Orchestrator ──► Agent Pool (13 agents)   │
│                        │                                     │
│           ┌────────────┴────────────┐                       │
│           ▼                         ▼                       │
│     Task Queue              Message Bus                     │
│     (prioritized)           (pub/sub)                       │
│           │                         │                       │
│           └─────────┬───────────────┘                       │
│                     ▼                                       │
│              ┌──────────────┐                               │
│              │ E2B Sandbox  │  ◄── All execution here       │
│              └──────────────┘                               │
│                     │                                       │
│                     ▼                                       │
│              ┌──────────────┐                               │
│              │  Checklist   │  ◄── Progress tracking        │
│              │   System     │                               │
│              └──────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

**"E2B_API_KEY not set"**
Get an API key from https://e2b.dev and add to `.env`

**"CLAUDE_CODE_OAUTH_TOKEN not set"**
Run `claude setup-token` and add the token to `.env`

**"SECURITY: Direct bash execution blocked"**
This is expected! All commands must go through E2B sandbox.
The agent should use `mcp__e2b__e2b_execute_command` instead.

**Verify security fixes:**
```bash
python verify_fixes.py
```

## License

MIT License - see [LICENSE](LICENSE) for details.

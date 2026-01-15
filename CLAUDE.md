# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **Universal AI Development Platform** - an autonomous multi-agent system powered by the Claude Agent SDK that builds and manages software projects through specialized agent types. The platform implements a "checklist-centric" workflow where agents collaborate via shared task tracking and inter-agent messaging.

## Running the System

### Interactive TUI (Recommended)
```bash
# Windows
python tui.py
# Or double-click: tui.bat

# Linux/Mac
python tui.py
```

The TUI provides:
- Project creation and management
- Real-time progress monitoring
- Agent memory dashboard with pattern/mistake visualization
- Linear issue integration

### Multi-Agent Orchestrator
```bash
# Windows
python run_orchestrator.py
# Or double-click: run_orchestrator.bat

# Linux/Mac
python run_orchestrator.py
```

### Programmatic Usage
```python
import asyncio
from pathlib import Path
from orchestrator import AgentOrchestrator

async def main():
    orchestrator = AgentOrchestrator()
    orchestrator.register_project(
        name="My Project",
        path=Path("./projects/example"),
        spec_file=Path("./prompts/app_spec.txt"),
        priority=1
    )
    await orchestrator.start()

asyncio.run(main())
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_embeddings.py -v
pytest tests/test_security.py -v
```

## Core Architecture

### Checklist-Centric Workflow

The entire system revolves around `.project_checklist.json` files that track task state:

1. **Initializer Agent** (Session 1): Reads `app_spec.txt`, creates 30-50 tasks in checklist
2. **Coding Agents** (Sessions 2+): Read checklist → claim task → implement → test → mark done
3. **Checklist Format**: JSON with task status, notes, session logs → auto-generates `CHECKLIST.md`

**Critical**: Agents determine completion by checking `"status": "Done"` in the JSON, NOT by inspecting actual code.

### Multi-Agent Coordination System

The platform has **5 core infrastructure layers** working together:

```
┌─────────────────────────────────────────────────┐
│           AgentOrchestrator                     │
│  Manages: Agent Pool, Task Routing, Health     │
└───────────────┬─────────────────────────────────┘
                │
        ┌───────┼───────┐
        ▼       ▼       ▼
    ┌────────┬─────────┬─────────┐
    │Project │  Task   │ Message │
    │Registry│  Queue  │   Bus   │
    └────────┴─────────┴─────────┘
                │
        ┌───────┼───────────┐
        ▼       ▼           ▼
    [Agent] [Agent]    [Agent]
     Pool    Pool       Pool
```

**Key Components**:
- `core/project_registry.py`: Multi-project tracking, workload distribution
- `core/task_queue.py`: Priority-based task distribution (CRITICAL > HIGH > MEDIUM > LOW)
- `core/message_bus.py`: Pub/sub inter-agent communication with JSON error handling
- `core/agent_memory.py`: Persistent learning with vector embeddings for semantic search
- `core/embeddings.py`: Sentence-transformers integration for similarity search
- `core/memory_dashboard.py`: Rich console visualization for agent memory
- `core/enhanced_checklist.py`: Subtasks, blocking mechanism, test coverage tracking

### 13 Specialized Agent Types

Each agent type has a specific role in the development workflow:

| Agent Type | Primary Role | When Used |
|------------|-------------|-----------|
| **Architect** | Planning, design, architecture decisions | Start of projects, major features |
| **Builder** | Feature implementation, coding | Main workforce (multiple instances) |
| **TestGenerator** | Creates test suites using Context7 docs | After feature implementation |
| **Verifier** | Quality assurance, ensures 100% completion | After implementation, creates blocking subtasks for issues |
| **Reviewer** | Code review, security, best practices | Post-implementation review |
| **DevOps** | CI/CD, infrastructure, deployment | Infrastructure tasks |
| **Documentation** | API docs, README, user guides | Documentation tasks |
| **Reporter** | Markdown reports, sprint summaries | Periodic reporting |
| **Analytics** | Pattern analysis, identifies trends | Strategic insights |
| **Refactor** | Code quality, technical debt reduction | Code quality improvement |
| **Database** | Schema design, query optimization | Database-related tasks |
| **UIDesign** | UI/UX, accessibility (WCAG), responsive design | UI/UX tasks |
| **E2BSandbox** | Sandboxed code execution (optional) | When E2B enabled |

All agents inherit from `agents/base_agent.py` with standard lifecycle: `before_task()` → `execute_task()` → `after_task()`.

## Security Architecture

**Defense-in-depth** security with 4 layers:

1. **OS-level Sandbox**: Bash commands run in isolated environment (E2B when available)
2. **Filesystem Restrictions**: File operations restricted to `project_dir` via `.claude_settings.json`
3. **Bash Security Hook**: `security.py` validates commands (allowlist currently disabled for E2B sandbox autonomy)
4. **MCP Permissions**: Explicit tool allowlist in `.claude_settings.json`

**Security settings generated per-project**:
```json
{
  "sandbox": {"enabled": true, "autoAllowBashIfSandboxed": true},
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": ["Read(./**)", "Write(./**)", "Bash(*)", "mcp__*"]
  }
}
```

## MCP Server Integration

The platform uses **10 MCP servers** (configured in `client.py`):

- **E2B**: Sandboxed command execution (`mcp__e2b__*` tools) - **CRITICAL for security**
- **Playwright**: Browser automation (`mcp__playwright__*` tools)
- **Context7**: Documentation lookup (`mcp__context7__resolve-library-id`, `mcp__context7__query-docs`)
- **Filesystem**: File operations (`mcp__filesystem__*` - note: uses wildcard pattern)
- **GitHub**: Version control, PRs, issues (`mcp__github__*`)
- **Git**: Local git operations (`mcp__git__*`)
- **Memory**: Knowledge graph memory (`mcp__memory__*`)
- **Sequential Thinking**: Problem-solving (`mcp__sequential_thinking__*`)
- **Fetch**: Web content retrieval (`mcp__fetch__*`)
- **Linear**: Project management and issue tracking (`mcp__linear__*` tools) - HTTP transport

Most MCP servers are initialized via `npx` (stdio transport). Linear uses HTTP transport to `https://mcp.linear.app/mcp`. E2B uses a custom local server in `mcp_servers/e2b/`.

## Working with Checklists

### Reading Checklist State
```python
from checklist_manager import ChecklistManager
from pathlib import Path

manager = ChecklistManager(Path("./my_project"))

# Get progress summary
summary = manager.get_progress_summary()
# Returns: {"Todo": N, "In Progress": M, "Done": X, "Blocked": Y}

# Get specific task
task = manager.get_task(task_id=5)

# Find next pending task
next_task = manager.get_next_pending_task()
```

### Updating Task Status
```python
# Mark task complete
manager.update_task_status(
    task_id=10,
    status="Done",
    notes="Implemented MultiHasher with MD5/SHA1/SHA256. Tests passing."
)

# Export markdown view
manager.export_to_markdown()  # Updates CHECKLIST.md
```

### Enhanced Checklist Features
```python
from core.enhanced_checklist import EnhancedChecklistManager

ecm = EnhancedChecklistManager(Path("./my_project"))

# Add subtask
ecm.add_subtask(
    parent_id=5,
    title="Write unit tests",
    description="Test all hash algorithms"
)

# Create blocking task (halts other work)
ecm.add_task(
    title="Fix critical security issue",
    priority="CRITICAL",
    blocking=True
)

# Track test coverage
ecm.update_test_coverage(
    task_id=5,
    unit_tests=5,
    integration_tests=2
)
```

## Environment Configuration

Required variables in `.env`:
```env
# Required - Authentication
CLAUDE_CODE_OAUTH_TOKEN=your-token  # Get via: claude setup-token
E2B_API_KEY=your-key                # Required: Get from https://e2b.dev
LINEAR_API_KEY=your-key             # Required: Get from https://linear.app/YOUR-TEAM/settings/api

# Optional
ANTHROPIC_API_KEY=your-key          # Optional: for direct API access
CONTEXT7_API_KEY=your-key           # Recommended: for doc lookup
GITHUB_TOKEN=your-token             # Optional: for GitHub MCP server

# Agent Army Config
MAX_CONCURRENT_AGENTS=10
AGENT_TIMEOUT=3600
DEFAULT_MODEL=claude-opus-4-5-20251101
```

## Project Customization

### Changing Application Spec
Edit `prompts/app_spec.txt` to define what the agents should build. The initializer agent will:
1. Parse the spec
2. Create 30-50 tasks
3. Set up project structure
4. Generate `init.sh`/`init.bat`

### Adding New Agent Type
```python
# 1. Create agent class in agents/
from agents.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self, agent_id, config, message_bus, claude_client):
        super().__init__(agent_id, "my_agent_type", config, message_bus)
        self.claude_client = claude_client

    async def execute_task(self, task):
        # Implement task logic
        return {"success": True, "result": "..."}

# 2. Register in orchestrator.py
from agents import MyNewAgent

# In _initialize_agent_pool():
my_agent = MyNewAgent(
    agent_id="myagent-001",
    config=self.config,
    message_bus=self.message_bus,
    claude_client=None
)
await my_agent.initialize()
self.agents["myagent-001"] = my_agent
```

### Modifying Security Allowlist
If not using E2B sandboxes, restore command validation in `security.py`:
```python
ALLOWED_COMMANDS = {
    "ls", "cat", "npm", "node", "python", "cargo", "git",
    # Add your commands
}

def bash_security_hook(tool_name, tool_input):
    # Implement validation logic
    pass
```

## Troubleshooting

### Agent Not Recognizing Completed Work
**Cause**: Checklist JSON not updated with `"status": "Done"`
**Fix**: Manually update via `ChecklistManager.update_task_status()`

### MCP Permission Errors
**Cause**: Tool not in allowed list in `client.py` or `.claude_settings.json`
**Fix**: Add tool to `ALLOWED_TOOLS` list, regenerate settings (delete `.claude_settings.json`)

### Agent Appears Stuck
**Cause**: Waiting for user input, blocking task, or compilation error
**Fix**: Check session logs, review last tool output, check for blocking tasks

### Temp Directory Cleanup
```python
from utils.cleanup_temp_files import cleanup_temp_files

cleanup_temp_files(
    project_dir=Path.cwd(),
    patterns=["tmpclaude-*-cwd", "tmpclaude-*"],
    older_than_hours=24
)
```

## Key Design Patterns

### Two-Agent Pattern
1. **Session 1** (Initializer): Creates checklist from `app_spec.txt`
2. **Session 2+** (Coding): Reads checklist → implements tasks

### Blocking Task Mechanism
Verifier agents create blocking subtasks when issues found:
- Project work halts until blocking tasks resolved
- Blocking tasks go to front of task queue
- Prevents building on broken foundations

### Agent Memory & Learning
Agents persist learnings to `AGENT_MEMORY/*.md` with optional vector embeddings:
```python
from core.agent_memory import AgentMemory

# Initialize with embeddings enabled
memory = AgentMemory("builder-001", use_embeddings=True)

# Add patterns and mistakes
memory.add_pattern("JWT Auth", "Use refresh tokens for session management")
memory.add_mistake("SQL Injection", "task-123", "Raw query", "Use parameterized queries")

# Semantic similarity search (uses embeddings if available)
relevant_patterns = memory.find_similar_patterns("authentication login")
relevant_mistakes = memory.get_relevant_mistakes("database query security")

# Save and load
memory.save()
memory.load()
```

### Memory Dashboard
Visualize agent memory with the Rich console dashboard:
```python
from core.memory_dashboard import MemoryDashboard
from pathlib import Path

dashboard = MemoryDashboard(Path("./AGENT_MEMORY"))
dashboard.display()  # Shows patterns, mistakes, and statistics
```

### Message Bus Communication
```python
# Subscribe to channel
self.message_bus.subscribe("task_completed", callback=self.handle_completion)

# Publish message
self.message_bus.publish(
    channel="task_completed",
    message={"task_id": "task-001", "status": "success"},
    sender="builder-001",
    priority="HIGH"
)

# Direct message
self.message_bus.send_direct(
    recipient="verifier-001",
    message={"task_id": "task-001", "verify": True},
    sender="builder-001"
)
```

## Testing the Platform

**Test Structure**:
- `tests/test_embeddings.py`: EmbeddingManager, EmbeddingStorage, AgentMemory integration
- `tests/test_security.py`: Bash command security validation
- `tests/test_builder_agent.py`: Builder agent initialization and execution
- `tests/test_quality_pipeline.py`: Verifier/TestGenerator workflow
- `tests/test_architect_reviewer.py`: Architect/Reviewer integration
- `tests/test_phase4_agents.py`: DevOps/Docs/Reporter/Analytics

**Running Tests**:
```bash
# All tests with verbose output
pytest tests/ -v

# Specific test file
pytest tests/test_embeddings.py -v

# Specific test function
pytest tests/test_embeddings.py::TestEmbeddingManager::test_similarity_search -v

# Skip tests requiring embeddings if not installed
pytest tests/ -v -k "not embeddings"
```

## Windows Compatibility Notes

- Git Bash required for bash command execution (included with Git for Windows)
- Path separators handled automatically via `pathlib`
- PowerShell/CMD supported for environment variable configuration
- E2B sandboxes provide cross-platform consistency when enabled

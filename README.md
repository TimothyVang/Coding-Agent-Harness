# Autonomous Coding Agent Harness

A minimal harness demonstrating long-running autonomous coding with the Claude Agent SDK. This demo implements a two-agent pattern (initializer + coding agent) with a **local checklist system** for tracking all work.

## Key Features

- **Local Checklist System**: All work is tracked in `.project_checklist.json` with automatic `CHECKLIST.md` generation
- **Real-time Visibility**: Check `CHECKLIST.md` to see project progress at any time
- **Session Handoff**: Agents communicate via checklist notes and session logs
- **Two-Agent Pattern**: Initializer creates checklist, coding agents implement tasks
- **Browser Testing**: Playwright MCP for comprehensive UI verification
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

### 2. Set Up Authentication

You need a Claude Code OAuth token:

**Windows (PowerShell):**
```powershell
# Generate the token using Claude Code CLI
claude setup-token

# Set the environment variable
$env:CLAUDE_CODE_OAUTH_TOKEN = "your-oauth-token-here"
```

**Windows (Command Prompt):**
```cmd
# Generate the token
claude setup-token

# Set the environment variable
set CLAUDE_CODE_OAUTH_TOKEN=your-oauth-token-here
```

**Linux/Mac:**
```bash
# Generate the token
claude setup-token

# Set the environment variable
export CLAUDE_CODE_OAUTH_TOKEN='your-oauth-token-here'
```

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

| Variable | Description | Required |
|----------|-------------|----------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code OAuth token (from `claude setup-token`) | Yes |

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir` | Directory for the project | `./autonomous_demo_project` |
| `--max-iterations` | Max agent iterations | Unlimited |
| `--model` | Claude model to use | `claude-opus-4-5-20251101` |

## Project Structure

```
agent-harness/
├── autonomous_agent_demo.py  # Main entry point
├── agent.py                  # Agent session logic
├── client.py                 # Claude SDK + MCP client configuration
├── checklist_manager.py      # Local checklist system for task tracking
├── security.py               # Bash command allowlist and validation
├── progress.py               # Progress tracking utilities
├── prompts.py                # Prompt loading utilities
├── prompts/
│   ├── app_spec.txt          # Application specification
│   ├── initializer_prompt.md # First session prompt (creates checklist)
│   └── coding_prompt.md      # Continuation session prompt (works tasks)
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

| Server | Transport | Purpose |
|--------|-----------|---------|
| **Playwright** | stdio | Browser automation for UI testing and verification |

See: https://playwright.dev/docs/intro

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

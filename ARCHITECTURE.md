# Agent Army Architecture

## Vision
A fully autonomous multi-agent system that can build and maintain multiple applications simultaneously with specialized agent roles working in parallel.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR (Central Command)                  │
│  - Project Registry                                                     │
│  - Task Queue Management                                                │
│  - Agent Pool Management                                                │
│  - Health Monitoring                                                    │
│  - Resource Allocation                                                  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             │ Dispatches Tasks
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   PROJECT 1   │    │   PROJECT 2   │    │   PROJECT 3   │
│               │    │               │    │               │
│ Checklist     │    │ Checklist     │    │ Checklist     │
│ Tasks         │    │ Tasks         │    │ Tasks         │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             │ Tasks Feed Into
                             │
                             ▼
                    ┌─────────────────┐
                    │   TASK QUEUE    │
                    │  (Priority-based)│
                    └────────┬─────────┘
                             │
                 ┌───────────┼───────────┐
                 │           │           │
                 ▼           ▼           ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │  Agent   │  │  Agent   │  │  Agent   │
         │  Pool    │  │  Pool    │  │  Pool    │
         │  Slot 1  │  │  Slot 2  │  │  Slot 3  │
         └──────────┘  └──────────┘  └──────────┘
              │             │             │
     ┌────────┼─────────────┼─────────────┼────────┐
     │        │             │             │        │
     ▼        ▼             ▼             ▼        ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│Architect│ │ Builder │ │Verifier │ │Reviewer │ │ DevOps  │
│  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

## Agent Types

### 1. **Architect Agent**
**Role:** Planning and design decisions
- Analyzes requirements from app_spec.txt
- Creates initial project structure
- Makes technology stack decisions
- Designs system architecture
- Breaks down features into tasks
- **Priority:** Runs first on new projects

### 2. **Builder Agent** (formerly Coding Agent)
**Role:** Feature implementation
- Claims tasks from checklist
- Implements features
- Writes code (frontend/backend)
- Runs basic tests
- Commits changes
- **Priority:** Main workforce, multiple instances

### 3. **Verifier Agent** ⭐ NEW
**Role:** Quality assurance and testing
- Verifies completed tasks
- Runs Playwright UI tests
- Checks for regressions
- Visual testing (screenshots)
- Console error detection
- Performance checks
- **Priority:** Runs after Builder agents

### 4. **Reviewer Agent** ⭐ NEW
**Role:** Code review and quality
- Reviews code changes
- Checks coding standards
- Security vulnerability scanning
- Suggests improvements
- Approves or requests changes
- **Priority:** Runs parallel with Verifier

### 5. **DevOps Agent** ⭐ NEW
**Role:** Infrastructure and deployment
- Manages build processes
- Handles dependencies
- Environment configuration
- Deployment automation
- CI/CD pipeline management
- **Priority:** Runs as needed

### 6. **Documentation Agent** ⭐ NEW
**Role:** Documentation maintenance
- Generates API documentation
- Updates README files
- Creates user guides
- Maintains changelogs
- **Priority:** Runs periodically

## Multi-Project Support

### Project Registry Structure
```json
{
  "projects": [
    {
      "id": "proj-001",
      "name": "E-Commerce Platform",
      "path": "/projects/ecommerce",
      "status": "active",
      "created_at": "2025-01-11T10:00:00Z",
      "last_activity": "2025-01-11T15:30:00Z",
      "checklist_path": "/projects/ecommerce/.project_checklist.json",
      "priority": 1,
      "agents_assigned": ["builder-1", "verifier-1"]
    },
    {
      "id": "proj-002",
      "name": "Blog Platform",
      "path": "/projects/blog",
      "status": "active",
      "created_at": "2025-01-11T11:00:00Z",
      "last_activity": "2025-01-11T15:25:00Z",
      "checklist_path": "/projects/blog/.project_checklist.json",
      "priority": 2,
      "agents_assigned": ["builder-2"]
    }
  ]
}
```

## Task Queue System

### Priority Levels
1. **CRITICAL** - Blocking issues, security vulnerabilities
2. **HIGH** - Failed verifications, core features
3. **MEDIUM** - New features, enhancements
4. **LOW** - Documentation, polish

### Task Structure
```json
{
  "task_id": "task-001",
  "project_id": "proj-001",
  "type": "implementation",
  "priority": "HIGH",
  "assigned_to": "builder-1",
  "status": "in_progress",
  "created_at": "2025-01-11T15:00:00Z",
  "dependencies": [],
  "estimated_duration": "30m",
  "retry_count": 0
}
```

## Orchestrator Components

### 1. Project Manager
- Registers new projects
- Tracks project status
- Manages project lifecycle
- Load balancing across projects

### 2. Task Dispatcher
- Pulls tasks from all project checklists
- Prioritizes tasks globally
- Assigns tasks to appropriate agent types
- Handles task dependencies

### 3. Agent Pool Manager
- Spawns agents as needed
- Monitors agent health
- Terminates idle agents
- Respawns failed agents
- Load balancing

### 4. Communication Hub
- Inter-agent messaging
- Event broadcasting
- Status updates
- Log aggregation

### 5. Monitoring System
- Real-time dashboard
- Agent status tracking
- Project progress metrics
- Performance metrics
- Error tracking

## Background Execution

### Agent Lifecycle
```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  IDLE    │────▶│  READY   │────▶│  RUNNING │────▶│ COMPLETE │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
      ▲                                  │                │
      │                                  │                │
      └──────────────────────────────────┴────────────────┘
                          (Recycle)
```

### Execution Modes
1. **Daemon Mode** - Runs continuously in background
2. **Batch Mode** - Processes N tasks then stops
3. **Scheduled Mode** - Runs at specific times
4. **On-Demand Mode** - Manual trigger

## Inter-Agent Communication

### Message Types
- **TaskComplete** - Agent finished a task
- **TaskFailed** - Agent failed a task
- **VerificationRequired** - Request verification
- **ReviewRequired** - Request code review
- **Blocked** - Agent blocked on dependency
- **HealthCheck** - Agent status ping
- **ResourceRequest** - Request additional resources

### Communication Channels
- **Redis Pub/Sub** - Real-time messaging
- **File-based Queue** - Fallback for simple setups
- **Database Queue** - Persistent queue with SQLite

## Verification System

### Verifier Agent Workflow
1. **Monitor** - Watch for completed tasks
2. **Claim** - Claim verification task
3. **Test** - Run comprehensive tests
   - Unit tests
   - Integration tests
   - UI tests (Playwright)
   - Visual regression tests
   - Performance tests
4. **Report** - Update task with results
5. **Approve/Reject** - Mark task as verified or failed
6. **Alert** - Notify if critical issues found

### Verification Checklist
- [ ] Code compiles/runs without errors
- [ ] All unit tests pass
- [ ] UI tests pass (Playwright)
- [ ] No console errors
- [ ] Visual regression check
- [ ] Performance benchmarks met
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] No new technical debt

## Configuration

### Global Config (`agent_army_config.yaml`)
```yaml
orchestrator:
  max_concurrent_agents: 10
  agent_timeout: 3600  # 1 hour
  health_check_interval: 60  # seconds

projects:
  base_path: "./projects"
  max_concurrent_projects: 5

agent_pool:
  architect: 1
  builder: 5
  verifier: 2
  reviewer: 1
  devops: 1

task_queue:
  priority_levels: 4
  batch_size: 10
  retry_limit: 3

communication:
  mode: "file"  # file, redis, database
  message_ttl: 3600

monitoring:
  enabled: true
  dashboard_port: 8080
  log_level: "INFO"
```

## File Structure

```
agent-army/
├── orchestrator/
│   ├── __init__.py
│   ├── project_manager.py      # Multi-project management
│   ├── task_dispatcher.py      # Task queue and dispatch
│   ├── agent_pool.py           # Agent lifecycle management
│   ├── communication.py        # Inter-agent messaging
│   └── monitoring.py           # Health checks and metrics
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Base class for all agents
│   ├── architect_agent.py      # Planning and design
│   ├── builder_agent.py        # Feature implementation
│   ├── verifier_agent.py       # Testing and verification
│   ├── reviewer_agent.py       # Code review
│   ├── devops_agent.py         # Infrastructure
│   └── documentation_agent.py  # Documentation
├── core/
│   ├── __init__.py
│   ├── checklist_manager.py    # Task tracking (existing)
│   ├── project_registry.py     # Project registration
│   ├── task_queue.py           # Priority queue
│   └── message_bus.py          # Event system
├── dashboard/
│   ├── __init__.py
│   ├── app.py                  # Flask/FastAPI dashboard
│   ├── templates/              # Dashboard UI
│   └── static/                 # CSS/JS
├── config/
│   ├── agent_army_config.yaml  # Global configuration
│   └── agent_profiles.yaml     # Agent type definitions
├── data/
│   ├── projects.db             # SQLite for project data
│   ├── task_queue.db           # SQLite for tasks
│   └── logs/                   # Agent logs
├── army.py                     # Main entry point
└── requirements.txt
```

## Usage Examples

### Start the Agent Army
```bash
# Start orchestrator in daemon mode
python army.py start --mode daemon

# Start with specific agent pool
python army.py start --builders 5 --verifiers 2

# Start for single project
python army.py start --project-dir ./my-app
```

### Register a New Project
```bash
# Register new project
python army.py register --name "My App" --path ./my-app --spec ./spec.txt

# List all projects
python army.py projects list

# Check project status
python army.py projects status my-app
```

### Monitor Agents
```bash
# View dashboard
python army.py dashboard

# Check agent status
python army.py agents status

# View logs
python army.py logs --agent builder-1
```

### Manual Control
```bash
# Spawn specific agent type
python army.py spawn verifier --project my-app

# Stop all agents
python army.py stop

# Restart failed agents
python army.py restart --failed-only
```

## Benefits

1. **Scale** - Handle multiple projects simultaneously
2. **Specialization** - Each agent type optimized for its role
3. **Quality** - Dedicated verification and review agents
4. **Resilience** - Auto-restart, health monitoring
5. **Visibility** - Real-time dashboard and monitoring
6. **Efficiency** - Parallel execution, smart task distribution
7. **Automation** - Fully autonomous operation

## Next Steps

1. Implement orchestrator core
2. Create specialized agent types
3. Build task queue system
4. Add monitoring dashboard
5. Test with multiple projects
6. Add advanced features (ML-based priority, predictive scaling)

"""
Agent Orchestrator
==================

Coordinates multiple specialized agents for autonomous software development.

The orchestrator manages:
- Agent pool initialization and lifecycle
- Task routing to appropriate agent types
- Load balancing across agents
- Inter-agent communication via message bus
- Project registry coordination
- Health monitoring and recovery
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from claude_code_sdk import ClaudeSDKClient

from core.project_registry import ProjectRegistry
from core.task_queue import TaskQueue
from core.message_bus import MessageBus, MessageTypes
from core.agent_memory import AgentMemory
from core.e2b_sandbox_manager import E2BSandboxManager
from agents import (
    BaseAgent, ArchitectAgent, BuilderAgent, TestGeneratorAgent,
    VerifierAgent, ReviewerAgent, DevOpsAgent, DocumentationAgent,
    ReporterAgent, AnalyticsAgent, RefactorAgent, DatabaseAgent,
    UIDesignAgent, E2BSandboxAgent
)
from client import create_client


class AgentOrchestrator:
    """
    Orchestrates multiple specialized agents for software development.

    Manages:
    - Agent pool (currently: BuilderAgent)
    - Task routing by agent type
    - Project coordination
    - Message bus communication
    - Health monitoring
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize orchestrator.

        Args:
            config: Optional configuration dict
        """
        self.config = config or self._load_default_config()

        # Core infrastructure
        self.project_registry = ProjectRegistry()
        self.task_queue = TaskQueue()
        self.message_bus = MessageBus()

        # E2B Sandbox Manager (optional)
        e2b_config = self.config.get("e2b", {})
        self.sandbox_manager = None
        if e2b_config.get("enabled", True):
            try:
                self.sandbox_manager = E2BSandboxManager(e2b_config)
                print("[Orchestrator] E2B Sandbox Manager initialized")
            except Exception as e:
                print(f"[Orchestrator] Warning: E2B initialization failed: {e}")
                print("[Orchestrator] Continuing without E2B (will use local execution)")

        # Auto-cleanup temp files
        if self.config.get("auto_cleanup_temp_files", True):
            self._cleanup_temp_files()

        # Agent pool
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_types_available = [
            "architect", "builder", "test_generator", "verifier", "reviewer",
            "devops", "documentation", "reporter", "analytics", "refactor",
            "database", "ui_design", "e2b_sandbox"
        ]  # All 13 agents implemented! 🎉

        # Orchestrator state
        self.running = False
        self.max_concurrent_agents = self.config.get("max_concurrent_agents", 10)

        print("[Orchestrator] Initialized")
        print(f"  - Max concurrent agents: {self.max_concurrent_agents}")
        print(f"  - Agent types available: {', '.join(self.agent_types_available)}")

    def _load_default_config(self) -> Dict:
        """Load default configuration from environment."""
        return {
            "max_concurrent_agents": int(os.getenv("MAX_CONCURRENT_AGENTS", "10")),
            "agent_timeout": int(os.getenv("AGENT_TIMEOUT", "3600")),
            "projects_base_path": os.getenv("PROJECTS_BASE_PATH", "./projects"),
            "default_model": os.getenv("DEFAULT_MODEL", "claude-opus-4-5-20251101"),
            "memory_dir": Path.cwd() / "AGENT_MEMORY",
            "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "60")),
            "auto_cleanup_temp_files": True,
            "e2b": {
                "enabled": bool(os.getenv("E2B_ENABLED", "true").lower() in ("true", "1", "yes")),
                "e2b_api_key": os.getenv("E2B_API_KEY"),
                "default_template": os.getenv("E2B_TEMPLATE", "node20"),
                "sandbox_pool_size": int(os.getenv("E2B_POOL_SIZE", "5")),
                "sandbox_timeout_seconds": int(os.getenv("E2B_TIMEOUT", "600")),
                "sandbox_memory_mb": int(os.getenv("E2B_MEMORY_MB", "2048")),
                "sandbox_cpu_count": int(os.getenv("E2B_CPU_COUNT", "2")),
                "persistent_sessions": True,
                "auto_cleanup_age_minutes": 60,
            }
        }

    def _cleanup_temp_files(self):
        """Clean up temporary files on orchestrator startup."""
        try:
            from utils.cleanup_temp_files import cleanup_temp_files

            patterns = ["tmpclaude-*-cwd", "tmpclaude-*"]
            result = cleanup_temp_files(
                project_dir=Path.cwd(),
                patterns=patterns,
                older_than_hours=24
            )

            if result["deleted"] > 0:
                print(f"[Orchestrator] Cleaned up {result['deleted']} temp files "
                      f"({result['freed_bytes']} bytes)")
        except Exception as e:
            print(f"[Orchestrator] Warning: Temp file cleanup failed: {e}")

    async def start(self):
        """
        Start the orchestrator.

        Initializes agent pool and begins task processing.
        """
        print("[Orchestrator] Starting...")
        self.running = True

        # Initialize E2B sandbox manager
        if self.sandbox_manager:
            await self.sandbox_manager.initialize()

        # Initialize agent pool
        await self._initialize_agent_pool()

        # Start background tasks
        tasks = [
            asyncio.create_task(self._task_processor()),
            asyncio.create_task(self._health_monitor()),
        ]

        print("[Orchestrator] Started successfully")

        try:
            # Wait for all tasks
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("[Orchestrator] Shutting down...")
            await self.stop()

    async def stop(self):
        """Stop the orchestrator and cleanup agents."""
        print("[Orchestrator] Stopping...")
        self.running = False

        # Cleanup all agents
        for agent_id, agent in self.agents.items():
            print(f"[Orchestrator] Cleaning up agent: {agent_id}")
            await agent.cleanup()

        # Cleanup E2B sandbox manager
        if self.sandbox_manager:
            await self.sandbox_manager.cleanup()

        print("[Orchestrator] Stopped")

    async def _initialize_agent_pool(self):
        """Initialize pool of agents."""
        print("[Orchestrator] Initializing agent pool...")

        # Create agents for each type
        # In production, would create multiple agents of each type based on workload

        # Architect agents - for planning and design
        architect = ArchitectAgent(
            agent_id="architect-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None  # Will be created per-project as needed
        )
        await architect.initialize()
        self.agents["architect-001"] = architect
        print(f"[Orchestrator] Created agent: architect-001 (type: architect)")

        # Builder agents - for feature implementation
        builder = BuilderAgent(
            agent_id="builder-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None,  # Will be created per-project as needed
            sandbox_manager=self.sandbox_manager
        )
        await builder.initialize()
        self.agents["builder-001"] = builder
        print(f"[Orchestrator] Created agent: builder-001 (type: builder)")

        # Test Generator agents - for test creation
        test_gen = TestGeneratorAgent(
            agent_id="testgen-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None,
            sandbox_manager=self.sandbox_manager
        )
        await test_gen.initialize()
        self.agents["testgen-001"] = test_gen
        print(f"[Orchestrator] Created agent: testgen-001 (type: test_generator)")

        # Verifier agents - for quality assurance
        verifier = VerifierAgent(
            agent_id="verifier-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None,
            sandbox_manager=self.sandbox_manager
        )
        await verifier.initialize()
        self.agents["verifier-001"] = verifier
        print(f"[Orchestrator] Created agent: verifier-001 (type: verifier)")

        # Reviewer agents - for code review
        reviewer = ReviewerAgent(
            agent_id="reviewer-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None
        )
        await reviewer.initialize()
        self.agents["reviewer-001"] = reviewer
        print(f"[Orchestrator] Created agent: reviewer-001 (type: reviewer)")

        # DevOps agents - for infrastructure and deployment
        devops = DevOpsAgent(
            agent_id="devops-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None
        )
        await devops.initialize()
        self.agents["devops-001"] = devops
        print(f"[Orchestrator] Created agent: devops-001 (type: devops)")

        # Documentation agents - for documentation generation
        documentation = DocumentationAgent(
            agent_id="docs-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None
        )
        await documentation.initialize()
        self.agents["docs-001"] = documentation
        print(f"[Orchestrator] Created agent: docs-001 (type: documentation)")

        # Reporter agents - for report generation
        reporter = ReporterAgent(
            agent_id="reporter-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None
        )
        await reporter.initialize()
        self.agents["reporter-001"] = reporter
        print(f"[Orchestrator] Created agent: reporter-001 (type: reporter)")

        # Analytics agents - for pattern analysis and insights
        analytics = AnalyticsAgent(
            agent_id="analytics-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None
        )
        await analytics.initialize()
        self.agents["analytics-001"] = analytics
        print(f"[Orchestrator] Created agent: analytics-001 (type: analytics)")

        # Refactor agents - for code quality and refactoring
        refactor = RefactorAgent(
            agent_id="refactor-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None
        )
        await refactor.initialize()
        self.agents["refactor-001"] = refactor
        print(f"[Orchestrator] Created agent: refactor-001 (type: refactor)")

        # Database agents - for schema design and optimization
        database = DatabaseAgent(
            agent_id="database-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None
        )
        await database.initialize()
        self.agents["database-001"] = database
        print(f"[Orchestrator] Created agent: database-001 (type: database)")

        # UI Design agents - for UI/UX and accessibility
        ui_design = UIDesignAgent(
            agent_id="uidesign-001",
            config=self.config,
            message_bus=self.message_bus,
            claude_client=None
        )
        await ui_design.initialize()
        self.agents["uidesign-001"] = ui_design
        print(f"[Orchestrator] Created agent: uidesign-001 (type: ui_design)")

        # E2B Sandbox agents - for sandboxed code execution (optional)
        if self.sandbox_manager:
            e2b_agent = E2BSandboxAgent(
                agent_id="e2b-001",
                config=self.config,
                message_bus=self.message_bus,
                sandbox_manager=self.sandbox_manager
            )
            await e2b_agent.initialize()
            self.agents["e2b-001"] = e2b_agent
            print(f"[Orchestrator] Created agent: e2b-001 (type: e2b_sandbox)")
            print(f"  - E2B enabled: {self.sandbox_manager.is_available()}")

        print(f"[Orchestrator] Agent pool initialized with {len(self.agents)} agents")
        print(f"[Orchestrator] All {len(self.agent_types_available)} specialized agent types ready!")

    async def _task_processor(self):
        """
        Main task processing loop.

        Continuously dequeues tasks and routes to appropriate agents.
        """
        print("[Orchestrator] Task processor started")

        while self.running:
            try:
                # Check for available agents
                available_agents = [
                    (agent_id, agent)
                    for agent_id, agent in self.agents.items()
                    if agent.status == "idle"
                ]

                if not available_agents:
                    # No agents available, wait
                    await asyncio.sleep(1)
                    continue

                # Try to get task for each available agent type
                for agent_id, agent in available_agents:
                    task = self.task_queue.dequeue(
                        agent_type=agent.agent_type,
                        agent_id=agent_id
                    )

                    if task:
                        print(f"[Orchestrator] Routing task {task['task_id']} to {agent_id}")

                        # Run task in background
                        asyncio.create_task(self._execute_task(agent, task))

                # Small delay to prevent tight loop
                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"[Orchestrator] Error in task processor: {e}")
                await asyncio.sleep(1)

    async def _execute_task(self, agent: BaseAgent, task: Dict):
        """
        Execute task with an agent.

        Args:
            agent: Agent to execute task
            task: Task dict from queue
        """
        task_id = task.get("task_id")

        try:
            print(f"[Orchestrator] Agent {agent.agent_id} starting task {task_id}")

            # Execute task
            result = await agent.run_task(task)

            # Update task queue
            if result["success"]:
                self.task_queue.mark_completed(task_id)
                print(f"[Orchestrator] Task {task_id} completed successfully")
            else:
                self.task_queue.mark_failed(task_id, result.get("error", "Unknown error"))
                print(f"[Orchestrator] Task {task_id} failed: {result.get('error')}")

        except Exception as e:
            print(f"[Orchestrator] Error executing task {task_id}: {e}")
            self.task_queue.mark_failed(task_id, str(e))

    async def _health_monitor(self):
        """
        Monitor agent health periodically.

        Checks agent status and restarts failed agents.
        """
        interval = self.config.get("health_check_interval", 60)
        print(f"[Orchestrator] Health monitor started (interval: {interval}s)")

        while self.running:
            try:
                await asyncio.sleep(interval)

                # Check each agent
                for agent_id, agent in self.agents.items():
                    # Send health check message
                    self.message_bus.send_direct(
                        recipient=agent_id,
                        message={"type": "health_check"},
                        sender="orchestrator"
                    )

                    # Check if agent is stuck
                    if agent.status == "working" and agent._task_start_time:
                        elapsed = (datetime.now() - agent._task_start_time).total_seconds()
                        timeout = self.config.get("agent_timeout", 3600)

                        if elapsed > timeout:
                            print(f"[Orchestrator] ⚠️  Agent {agent_id} appears stuck (timeout)")
                            # TODO: Implement recovery logic

            except Exception as e:
                print(f"[Orchestrator] Error in health monitor: {e}")

    def register_project(
        self,
        name: str,
        path: Path,
        spec_file: Path,
        priority: int = 1
    ) -> str:
        """
        Register a new project with the orchestrator.

        Args:
            name: Project name
            path: Project directory path
            spec_file: Application specification file
            priority: Project priority (1-10)

        Returns:
            Project ID
        """
        project_id = self.project_registry.register_project(
            name=name,
            path=path,
            spec_file=spec_file,
            priority=priority
        )

        print(f"[Orchestrator] Registered project: {name} (ID: {project_id})")

        # Announce to agents
        self.message_bus.publish(
            "project_updates",
            {
                "type": "project_registered",
                "project_id": project_id,
                "name": name
            },
            sender="orchestrator",
            priority="HIGH"
        )

        return project_id

    def enqueue_task(
        self,
        project_id: str,
        checklist_task_id: int,
        task_type: str,
        agent_type: str = "builder",
        priority: str = "MEDIUM",
        blocking: bool = False,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Enqueue a task for agent execution.

        Args:
            project_id: Project ID
            checklist_task_id: Task ID from project checklist
            task_type: Type of task (feature, bugfix, refactor, etc.)
            agent_type: Required agent type (builder, verifier, etc.)
            priority: Task priority (CRITICAL, HIGH, MEDIUM, LOW)
            blocking: Whether task is blocking
            dependencies: Optional list of task IDs that must complete first
            metadata: Optional additional task metadata

        Returns:
            Task ID in queue
        """
        task_id = self.task_queue.enqueue(
            project_id=project_id,
            checklist_task_id=checklist_task_id,
            task_type=task_type,
            agent_type=agent_type,
            priority=priority,
            blocking=blocking,
            dependencies=dependencies,
            metadata=metadata or {}
        )

        print(f"[Orchestrator] Enqueued task: {task_id} (type: {task_type}, priority: {priority})")

        return task_id

    def get_status(self) -> Dict:
        """
        Get orchestrator status.

        Returns:
            Status dict with orchestrator and agent information
        """
        return {
            "running": self.running,
            "agents": {
                agent_id: agent.get_statistics()
                for agent_id, agent in self.agents.items()
            },
            "task_queue": {
                "pending": len([t for t in self.task_queue.data["tasks"] if t["status"] == "pending"]),
                "in_progress": len([t for t in self.task_queue.data["tasks"] if t["status"] == "in_progress"]),
                "completed": len([t for t in self.task_queue.data["tasks"] if t["status"] == "completed"]),
                "failed": len([t for t in self.task_queue.data["tasks"] if t["status"] == "failed"]),
            },
            "projects": {
                "total": len(self.project_registry.data["projects"]),
                "active": len([
                    p for p in self.project_registry.data["projects"]
                    if p["status"] == "active"
                ]),
            }
        }


# Example usage function
async def run_example():
    """Example of using the orchestrator."""
    # Create orchestrator
    orchestrator = AgentOrchestrator()

    # Register a project
    project_id = orchestrator.register_project(
        name="Example Project",
        path=Path("./projects/example"),
        spec_file=Path("./prompts/app_spec.txt"),
        priority=1
    )

    # Enqueue some tasks
    orchestrator.enqueue_task(
        project_id=project_id,
        checklist_task_id=1,
        task_type="feature",
        agent_type="builder",
        priority="HIGH",
        metadata={"description": "Implement user authentication"}
    )

    # Start orchestrator (this blocks until stopped)
    await orchestrator.start()


if __name__ == "__main__":
    # Run example
    asyncio.run(run_example())

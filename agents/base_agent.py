"""
Base Agent Class
================

Foundation class for all agent types in the agent army.

Features:
- Agent lifecycle management (init, execute, cleanup)
- Memory integration for learning and improvement
- Task execution with before/after hooks
- Error handling and retry logic
- Communication via message bus
- Performance tracking
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from core.agent_memory import AgentMemory
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus, MessageTypes


class BaseAgent:
    """
    Base class for all agent types.

    Provides:
    - Common initialization and cleanup
    - Memory integration for learning
    - Task execution framework with hooks
    - Error handling
    - Message bus communication
    - Performance tracking

    Subclasses should override:
    - execute_task(): Main task execution logic
    - get_system_prompt(): Agent-specific system prompt
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None
    ):
        """
        Initialize base agent.

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (builder, verifier, etc.)
            config: Configuration dict
            message_bus: Optional message bus for communication
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config
        self.status = "idle"
        self.current_task = None
        self.client = None

        # Initialize memory
        memory_dir = config.get("memory_dir", Path.cwd() / "AGENT_MEMORY")
        self.memory = AgentMemory(agent_id, memory_dir)
        self.memory.load()
        self.memory.data["agent_type"] = agent_type

        # Message bus for communication
        self.message_bus = message_bus

        # Performance tracking
        self.task_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_duration_seconds = 0.0

        # Task start time
        self._task_start_time = None

    async def initialize(self):
        """
        Initialize agent resources.

        Subclasses can override to add custom initialization.
        """
        self.status = "initializing"

        # Load memory
        self.memory.load()

        # Subscribe to relevant message bus channels
        if self.message_bus:
            self.message_bus.subscribe(
                f"agent.{self.agent_type}",
                self.agent_id,
                self._handle_message
            )

            self.message_bus.subscribe(
                f"direct.{self.agent_id}",
                self.agent_id,
                self._handle_message
            )

        # Announce agent start
        if self.message_bus:
            self.message_bus.publish(
                "agent_lifecycle",
                {
                    "type": MessageTypes.AGENT_STARTED,
                    "agent_id": self.agent_id,
                    "agent_type": self.agent_type
                },
                sender=self.agent_id
            )

        self.status = "idle"

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a task.

        This is a template method that subclasses should override
        with their specific implementation logic.

        Args:
            task: Task dict from task queue

        Returns:
            Result dict with success status and data
        """
        raise NotImplementedError("Subclasses must implement execute_task()")

    async def run_task(self, task: Dict) -> Dict:
        """
        Run a task with full lifecycle (before, execute, after hooks).

        Args:
            task: Task dict from task queue

        Returns:
            Result dict
        """
        self.current_task = task
        self.status = "working"
        self._task_start_time = datetime.now()

        result = {
            "success": False,
            "error": None,
            "data": None
        }

        try:
            # Before task hook
            await self.before_task(task)

            # Execute task
            task_result = await self.execute_task(task)

            result["success"] = True
            result["data"] = task_result

            self.success_count += 1

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

            self.failure_count += 1

            # Handle failure
            await self.handle_failure(task, e)

        finally:
            # After task hook (always runs)
            duration = (datetime.now() - self._task_start_time).total_seconds()
            self.total_duration_seconds += duration

            await self.after_task(task, result)

            self.task_count += 1
            self.current_task = None
            self.status = "idle"

        return result

    async def before_task(self, task: Dict):
        """
        Hook called before executing task.

        Loads relevant memory, checks for similar patterns, etc.

        Args:
            task: Task to be executed
        """
        # Load memory
        self.memory.load()

        # Check for similar past tasks
        task_desc = task.get("metadata", {}).get("description", "")
        if task_desc:
            similar_patterns = self.memory.find_similar_patterns(task_desc)
            if similar_patterns:
                print(f"[{self.agent_id}] Found {len(similar_patterns)} similar patterns in memory")

            # Check for relevant mistakes to avoid
            relevant_mistakes = self.memory.get_relevant_mistakes(task_desc)
            if relevant_mistakes:
                print(f"[{self.agent_id}] ⚠️  {len(relevant_mistakes)} common mistakes to avoid")
                for mistake in relevant_mistakes[:3]:
                    print(f"  - {mistake['title']}: {mistake['solution']}")

        # Update context
        self.memory.update_context(
            last_task=task.get("checklist_task_id"),
            last_project=task.get("project_id"),
            current_focus=task.get("type")
        )

    async def after_task(self, task: Dict, result: Dict):
        """
        Hook called after task completion (success or failure).

        Records outcome, updates memory, extracts patterns, etc.

        Args:
            task: Task that was executed
            result: Result dict from execution
        """
        # Calculate duration
        duration_minutes = (
            (datetime.now() - self._task_start_time).total_seconds() / 60
        ) if self._task_start_time else 0

        # Record outcome in memory
        self.memory.add_task_result(
            task_id=str(task.get("task_id")),
            success=result["success"],
            duration_minutes=duration_minutes,
            notes=result.get("data", {}).get("notes", "") if result["success"] else result.get("error", "")
        )

        # If successful, try to extract patterns
        if result["success"]:
            # Subclasses can override this to extract domain-specific patterns
            await self.extract_patterns(task, result)

        # If failed, record mistake
        else:
            await self.record_mistake(task, result)

        # Publish completion message
        if self.message_bus:
            message_type = MessageTypes.TASK_COMPLETED if result["success"] else MessageTypes.TASK_FAILED

            self.message_bus.publish(
                "task_updates",
                {
                    "type": message_type,
                    "agent_id": self.agent_id,
                    "task_id": task.get("task_id"),
                    "project_id": task.get("project_id"),
                    "duration_minutes": duration_minutes,
                    "error": result.get("error") if not result["success"] else None
                },
                sender=self.agent_id,
                priority="HIGH"
            )

    async def extract_patterns(self, task: Dict, result: Dict):
        """
        Extract learned patterns from successful task.

        Subclasses can override to add domain-specific pattern extraction.

        Args:
            task: Completed task
            result: Task result
        """
        # Default implementation - subclasses should override
        pass

    async def record_mistake(self, task: Dict, result: Dict):
        """
        Record mistake from failed task.

        Args:
            task: Failed task
            result: Task result with error
        """
        error = result.get("error", "Unknown error")

        self.memory.add_mistake(
            title=f"Failed: {task.get('type', 'task')}",
            task_id=str(task.get("task_id")),
            error=error,
            solution="To be determined",  # Can be updated later
            cost_minutes=0
        )

    async def handle_failure(self, task: Dict, error: Exception):
        """
        Handle task failure.

        Args:
            task: Failed task
            error: Exception that occurred
        """
        print(f"[{self.agent_id}] Task failed: {error}")

        # Record in memory
        await self.record_mistake(task, {"error": str(error)})

        # Publish failure message
        if self.message_bus:
            self.message_bus.publish(
                "agent_errors",
                {
                    "type": MessageTypes.TASK_FAILED,
                    "agent_id": self.agent_id,
                    "task_id": task.get("task_id"),
                    "error": str(error)
                },
                sender=self.agent_id,
                priority="HIGH"
            )

    async def cleanup(self):
        """
        Cleanup agent resources.

        Subclasses can override to add custom cleanup.
        """
        self.status = "shutting_down"

        # Save memory
        self.memory.save()

        # Announce agent stop
        if self.message_bus:
            self.message_bus.publish(
                "agent_lifecycle",
                {
                    "type": MessageTypes.AGENT_STOPPED,
                    "agent_id": self.agent_id,
                    "stats": self.get_statistics()
                },
                sender=self.agent_id
            )

        self.status = "stopped"

    async def reflect(self):
        """
        Periodic self-reflection.

        Analyzes performance, updates goals, etc.
        """
        # What am I good at?
        strengths = self.memory.get_strengths()

        # What do I struggle with?
        weaknesses = self.memory.get_weaknesses()

        # What should I improve?
        goals = self.memory.generate_improvement_goals()

        # Update memory
        self.memory.data["strengths"] = strengths
        self.memory.data["weaknesses"] = weaknesses

        # Add goals
        for goal in goals:
            self.memory.add_goal(goal)

        # Save
        self.memory.save()

        print(f"[{self.agent_id}] Reflection complete")
        print(f"  Strengths: {len(strengths)}")
        print(f"  Weaknesses: {len(weaknesses)}")
        print(f"  New goals: {len(goals)}")

    def get_system_prompt(self) -> str:
        """
        Get agent-specific system prompt.

        Subclasses must override this to provide their specialized prompt.

        Returns:
            System prompt string
        """
        return f"""You are a {self.agent_type} agent.

Agent ID: {self.agent_id}
Status: {self.status}

Your role is to execute tasks assigned to you efficiently and effectively.
Learn from your experiences and continuously improve your performance.
"""

    def get_statistics(self) -> Dict:
        """
        Get agent performance statistics.

        Returns:
            Statistics dict
        """
        success_rate = (
            (self.success_count / self.task_count * 100)
            if self.task_count > 0 else 0
        )

        avg_duration = (
            (self.total_duration_seconds / self.task_count)
            if self.task_count > 0 else 0
        )

        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "task_count": self.task_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": success_rate,
            "average_duration_seconds": avg_duration,
            "total_duration_seconds": self.total_duration_seconds
        }

    async def _handle_message(self, message: Dict):
        """
        Handle incoming message from message bus.

        Args:
            message: Message dict
        """
        msg_type = message.get("message", {}).get("type")

        if msg_type == "health_check":
            # Respond to health check
            if self.message_bus:
                self.message_bus.send_direct(
                    recipient=message.get("sender"),
                    message={
                        "type": "health_check_response",
                        "agent_id": self.agent_id,
                        "status": self.status,
                        "stats": self.get_statistics()
                    },
                    sender=self.agent_id
                )

        # Subclasses can handle additional message types

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id} type={self.agent_type} status={self.status}>"

"""
Task Queue System
=================

Priority-based global task queue for distributing work across agent army.

Features:
- Priority-based queuing (CRITICAL > HIGH > MEDIUM > LOW)
- Agent type matching
- Task dependencies
- Retry logic for failed tasks
- Queue statistics and monitoring
- File locking for concurrency safety
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from filelock import FileLock
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False
    FileLock = None


class TaskQueue:
    """
    Global priority-based task queue for agent army.

    Responsibilities:
    - Maintain queue of tasks from all projects
    - Distribute tasks based on priority and agent type
    - Handle task lifecycle (pending -> assigned -> completed/failed)
    - Implement retry logic for failed tasks
    - Provide queue statistics
    """

    def __init__(self, queue_path: Optional[Path] = None):
        """
        Initialize task queue.

        Args:
            queue_path: Path to queue file (defaults to .agent_army/task_queue.json)
        """
        if queue_path is None:
            queue_dir = Path.cwd() / ".agent_army"
            queue_dir.mkdir(parents=True, exist_ok=True)
            self.queue_path = queue_dir / "task_queue.json"
        else:
            self.queue_path = Path(queue_path)
            self.queue_path.parent.mkdir(parents=True, exist_ok=True)

        self.data = self._load_or_create()

        # Priority order mapping
        self.priority_order = {
            "CRITICAL": 0,
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3
        }

    def _load_or_create(self) -> Dict:
        """Load existing queue or create new structure with file locking."""
        def _do_load():
            if self.queue_path.exists():
                with open(self.queue_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "tasks": [],
                    "history": []
                }

        if FILELOCK_AVAILABLE:
            lock = FileLock(str(self.queue_path) + ".lock")
            with lock:
                return _do_load()
        else:
            return _do_load()

    def _save(self):
        """Save queue to disk with file locking."""
        def _do_save():
            self.data["last_updated"] = datetime.now().isoformat()
            with open(self.queue_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)

        if FILELOCK_AVAILABLE:
            lock = FileLock(str(self.queue_path) + ".lock")
            with lock:
                _do_save()
        else:
            _do_save()

    def enqueue(
        self,
        project_id: str,
        checklist_task_id: int,
        task_type: str,
        agent_type: str,
        priority: str = "MEDIUM",
        blocking: bool = False,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add a task to the queue.

        Args:
            project_id: Project ID this task belongs to
            checklist_task_id: Task ID in the project's checklist
            task_type: Type of task (implementation, verification, testing, etc.)
            agent_type: Type of agent needed (builder, verifier, test_generator, etc.)
            priority: Priority level (CRITICAL, HIGH, MEDIUM, LOW)
            blocking: Whether this task blocks other work
            dependencies: List of task IDs that must complete first
            metadata: Additional task metadata

        Returns:
            Task ID (queue task ID, not checklist task ID)
        """
        task_id = f"task-{str(uuid.uuid4())[:8]}"

        task = {
            "task_id": task_id,
            "project_id": project_id,
            "checklist_task_id": checklist_task_id,
            "type": task_type,
            "agent_type": agent_type,
            "priority": priority,
            "blocking": blocking,
            "assigned_to": None,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "assigned_at": None,
            "started_at": None,
            "completed_at": None,
            "dependencies": dependencies or [],
            "retry_count": 0,
            "max_retries": 3,
            "error_history": [],
            "metadata": metadata or {}
        }

        self.data["tasks"].append(task)
        self._save()

        return task_id

    def dequeue(
        self,
        agent_type: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get next task for a specific agent type.

        Respects:
        - Priority order (CRITICAL > HIGH > MEDIUM > LOW)
        - Blocking tasks (blocking tasks go first)
        - Dependencies (tasks with unmet dependencies are skipped)
        - Agent type matching

        Args:
            agent_type: Type of agent requesting work
            agent_id: Optional agent ID for assignment
            project_id: Optional project ID to filter tasks

        Returns:
            Task dict or None if no suitable task available
        """
        # Get pending tasks for this agent type
        pending_tasks = [
            task for task in self.data["tasks"]
            if task["status"] == "pending"
            and task["agent_type"] == agent_type
            and (project_id is None or task["project_id"] == project_id)
            and self._dependencies_met(task)
        ]

        if not pending_tasks:
            return None

        # Sort by blocking (blocking first), then priority, then created time
        pending_tasks.sort(
            key=lambda t: (
                not t["blocking"],  # False (blocking=True) sorts before True (blocking=False)
                self.priority_order.get(t["priority"], 2),
                t["created_at"]
            )
        )

        # Get the highest priority task
        task = pending_tasks[0]

        # Assign to agent
        if agent_id:
            task["assigned_to"] = agent_id
            task["status"] = "assigned"
            task["assigned_at"] = datetime.now().isoformat()
            self._save()

        return task

    def mark_started(self, task_id: str):
        """
        Mark task as started.

        Args:
            task_id: Task ID to mark as started
        """
        task = self._get_task(task_id)
        if task:
            task["status"] = "in_progress"
            task["started_at"] = datetime.now().isoformat()
            self._save()

    def mark_completed(self, task_id: str, result: Optional[Dict] = None):
        """
        Mark task as completed.

        Args:
            task_id: Task ID to mark as completed
            result: Optional result data from task execution
        """
        task = self._get_task(task_id)
        if task:
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            if result:
                task["metadata"]["result"] = result

            # Move to history
            self.data["history"].append(task)
            self.data["tasks"] = [t for t in self.data["tasks"] if t["task_id"] != task_id]

            self._save()

    def mark_failed(self, task_id: str, error: str):
        """
        Mark task as failed and requeue if retries available.

        Args:
            task_id: Task ID to mark as failed
            error: Error message
        """
        task = self._get_task(task_id)
        if not task:
            return

        task["retry_count"] += 1
        task["error_history"].append({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "retry_attempt": task["retry_count"]
        })

        if task["retry_count"] < task["max_retries"]:
            # Requeue for retry
            task["status"] = "pending"
            task["assigned_to"] = None
            task["assigned_at"] = None
            task["started_at"] = None
        else:
            # Max retries exceeded - mark as failed permanently
            task["status"] = "failed"
            task["completed_at"] = datetime.now().isoformat()

            # Move to history
            self.data["history"].append(task)
            self.data["tasks"] = [t for t in self.data["tasks"] if t["task_id"] != task_id]

        self._save()

    def requeue_task(self, task_id: str):
        """
        Manually requeue a failed task for retry.

        Args:
            task_id: Task ID to requeue
        """
        task = self._get_task(task_id)
        if task:
            task["status"] = "pending"
            task["assigned_to"] = None
            task["assigned_at"] = None
            task["started_at"] = None
            task["retry_count"] = 0
            task["error_history"] = []
            self._save()

    def cancel_task(self, task_id: str):
        """
        Cancel a pending or assigned task.

        Args:
            task_id: Task ID to cancel
        """
        task = self._get_task(task_id)
        if task and task["status"] in ["pending", "assigned"]:
            task["status"] = "cancelled"
            task["completed_at"] = datetime.now().isoformat()

            # Move to history
            self.data["history"].append(task)
            self.data["tasks"] = [t for t in self.data["tasks"] if t["task_id"] != task_id]

            self._save()

    def get_pending_count(
        self,
        project_id: Optional[str] = None,
        agent_type: Optional[str] = None
    ) -> int:
        """
        Count pending tasks.

        Args:
            project_id: Optional project ID filter
            agent_type: Optional agent type filter

        Returns:
            Number of pending tasks
        """
        tasks = [
            t for t in self.data["tasks"]
            if t["status"] == "pending"
            and (project_id is None or t["project_id"] == project_id)
            and (agent_type is None or t["agent_type"] == agent_type)
        ]
        return len(tasks)

    def get_assigned_count(
        self,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> int:
        """
        Count assigned tasks.

        Args:
            agent_id: Optional agent ID filter
            project_id: Optional project ID filter

        Returns:
            Number of assigned tasks
        """
        tasks = [
            t for t in self.data["tasks"]
            if t["status"] in ["assigned", "in_progress"]
            and (agent_id is None or t["assigned_to"] == agent_id)
            and (project_id is None or t["project_id"] == project_id)
        ]
        return len(tasks)

    def get_blocking_tasks(self) -> List[Dict]:
        """
        Get all blocking tasks in the queue.

        Returns:
            List of blocking task dicts
        """
        return [
            t for t in self.data["tasks"]
            if t["blocking"] and t["status"] in ["pending", "assigned", "in_progress"]
        ]

    def get_tasks_by_project(self, project_id: str) -> List[Dict]:
        """
        Get all tasks for a specific project.

        Args:
            project_id: Project ID to filter by

        Returns:
            List of task dicts
        """
        return [t for t in self.data["tasks"] if t["project_id"] == project_id]

    def get_tasks_by_agent(self, agent_id: str) -> List[Dict]:
        """
        Get all tasks assigned to a specific agent.

        Args:
            agent_id: Agent ID to filter by

        Returns:
            List of task dicts
        """
        return [t for t in self.data["tasks"] if t["assigned_to"] == agent_id]

    def get_queue_statistics(self) -> Dict:
        """
        Get queue statistics.

        Returns:
            Dict with queue statistics
        """
        all_tasks = self.data["tasks"] + self.data["history"]

        stats = {
            "total_tasks": len(all_tasks),
            "pending": len([t for t in self.data["tasks"] if t["status"] == "pending"]),
            "assigned": len([t for t in self.data["tasks"] if t["status"] == "assigned"]),
            "in_progress": len([t for t in self.data["tasks"] if t["status"] == "in_progress"]),
            "completed": len([t for t in self.data["history"] if t["status"] == "completed"]),
            "failed": len([t for t in self.data["history"] if t["status"] == "failed"]),
            "cancelled": len([t for t in self.data["history"] if t["status"] == "cancelled"]),
            "blocking_tasks": len(self.get_blocking_tasks()),
            "by_priority": {
                "CRITICAL": len([t for t in self.data["tasks"] if t["priority"] == "CRITICAL"]),
                "HIGH": len([t for t in self.data["tasks"] if t["priority"] == "HIGH"]),
                "MEDIUM": len([t for t in self.data["tasks"] if t["priority"] == "MEDIUM"]),
                "LOW": len([t for t in self.data["tasks"] if t["priority"] == "LOW"])
            },
            "by_agent_type": {}
        }

        # Count by agent type
        for task in self.data["tasks"]:
            agent_type = task["agent_type"]
            if agent_type not in stats["by_agent_type"]:
                stats["by_agent_type"][agent_type] = 0
            stats["by_agent_type"][agent_type] += 1

        return stats

    def _get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID from active queue."""
        for task in self.data["tasks"]:
            if task["task_id"] == task_id:
                return task
        return None

    def _dependencies_met(self, task: Dict) -> bool:
        """Check if task dependencies are met."""
        if not task.get("dependencies"):
            return True

        # Check if all dependency tasks are completed
        for dep_id in task["dependencies"]:
            dep_task = self._get_task(dep_id)
            if dep_task and dep_task["status"] != "completed":
                return False

            # Also check history
            dep_in_history = any(
                t["task_id"] == dep_id and t["status"] == "completed"
                for t in self.data["history"]
            )

            if not dep_in_history and not dep_task:
                # Dependency not found - fail safe, don't allow task to run
                # This prevents race conditions where tasks start before dependencies complete
                return False

            if not dep_in_history:
                return False

        return True

    def clear_completed(self, older_than_days: int = 7):
        """
        Clear completed tasks from history older than specified days.

        Args:
            older_than_days: Only clear tasks older than this many days
        """
        cutoff = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)

        self.data["history"] = [
            task for task in self.data["history"]
            if self._parse_datetime(task["completed_at"]).timestamp() > cutoff
        ]

        self._save()

    def _parse_datetime(self, iso_string: str) -> datetime:
        """Parse ISO format datetime string."""
        try:
            return datetime.fromisoformat(iso_string)
        except (ValueError, AttributeError, TypeError):
            return datetime.now()

    def export_to_markdown(self, output_path: Optional[Path] = None) -> str:
        """
        Export queue status to markdown format.

        Args:
            output_path: Optional path to write markdown file

        Returns:
            Markdown string
        """
        if not output_path:
            output_path = self.queue_path.parent / "TASK_QUEUE.md"

        lines = []
        lines.append("# Task Queue Status")
        lines.append("")
        lines.append(f"**Last Updated**: {self.data['last_updated']}")
        lines.append("")

        # Statistics
        stats = self.get_queue_statistics()
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- **Total Tasks**: {stats['total_tasks']}")
        lines.append(f"- **Pending**: {stats['pending']}")
        lines.append(f"- **In Progress**: {stats['in_progress']}")
        lines.append(f"- **Completed**: {stats['completed']}")
        lines.append(f"- **Failed**: {stats['failed']}")
        lines.append(f"- **Blocking Tasks**: {stats['blocking_tasks']}")
        lines.append("")

        # Blocking tasks warning
        blocking_tasks = self.get_blocking_tasks()
        if blocking_tasks:
            lines.append("## ⚠️ BLOCKING TASKS")
            lines.append("")
            for task in blocking_tasks:
                lines.append(f"- **{task['task_id']}**: {task['type']}")
                lines.append(f"  - Project: {task['project_id']}")
                lines.append(f"  - Priority: {task['priority']}")
                lines.append(f"  - Status: {task['status']}")
            lines.append("")

        # Active tasks
        active_tasks = [t for t in self.data["tasks"] if t["status"] in ["pending", "assigned", "in_progress"]]
        if active_tasks:
            lines.append("## Active Tasks")
            lines.append("")

            # Sort by priority
            active_tasks.sort(key=lambda t: (
                not t["blocking"],
                self.priority_order.get(t["priority"], 2)
            ))

            for task in active_tasks:
                status_emoji = {
                    "pending": "⏳",
                    "assigned": "📋",
                    "in_progress": "⚙️"
                }.get(task["status"], "")

                lines.append(f"### {status_emoji} {task['task_id']}")
                lines.append("")
                lines.append(f"- **Type**: {task['type']}")
                lines.append(f"- **Agent Type**: {task['agent_type']}")
                lines.append(f"- **Priority**: {task['priority']}")
                lines.append(f"- **Status**: {task['status']}")
                lines.append(f"- **Project**: {task['project_id']}")

                if task["assigned_to"]:
                    lines.append(f"- **Assigned To**: {task['assigned_to']}")

                if task["dependencies"]:
                    lines.append(f"- **Dependencies**: {', '.join(task['dependencies'])}")

                if task["blocking"]:
                    lines.append(f"- **🚫 BLOCKING TASK**")

                lines.append("")

        markdown = "\n".join(lines)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return markdown

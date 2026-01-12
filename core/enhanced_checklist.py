"""
Enhanced Checklist Manager
===========================

Enhanced task tracking system with:
- Subtask support (parent-child relationships)
- Blocking tasks (halt project until resolved)
- Completion percentage calculation
- Test coverage tracking
- Agent assignment tracking
- Session history
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class EnhancedChecklistManager:
    """
    Enhanced checklist manager with subtask and blocking support.

    Extends the basic checklist functionality with:
    - Hierarchical tasks (parent-child subtasks)
    - Blocking mechanism (tasks that halt other work)
    - Completion percentage calculation
    - Test coverage tracking per task
    - Agent assignment and tracking
    """

    def __init__(self, project_dir: Path):
        """
        Initialize enhanced checklist manager.

        Args:
            project_dir: Project directory containing .project_checklist.json
        """
        self.project_dir = Path(project_dir)
        self.checklist_file = self.project_dir / ".project_checklist.json"
        self.data = self._load_or_create()

    def _load_or_create(self) -> Dict:
        """Load existing checklist or create new structure."""
        if self.checklist_file.exists():
            with open(self.checklist_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "project_name": "",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "next_task_id": 1,
                "tasks": [],
                "sessions": []
            }

    def _save(self):
        """Save checklist to disk."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.checklist_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def initialize(self, project_name: str, tasks: List[Dict]):
        """
        Initialize checklist with project name and initial tasks.

        Args:
            project_name: Name of the project
            tasks: List of task dicts with 'title' and optional 'description', 'priority'
        """
        self.data["project_name"] = project_name
        self.data["created_at"] = datetime.now().isoformat()

        for task_data in tasks:
            self.add_task(
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                priority=task_data.get("priority", "MEDIUM")
            )

        self._save()

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: str = "MEDIUM",
        parent_task_id: Optional[int] = None
    ) -> int:
        """
        Add a new task to the checklist.

        Args:
            title: Task title
            description: Task description
            priority: Priority level (CRITICAL, HIGH, MEDIUM, LOW)
            parent_task_id: Optional parent task ID for subtasks

        Returns:
            Task ID of the newly created task
        """
        task_id = self.data["next_task_id"]
        self.data["next_task_id"] += 1

        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": "Todo",
            "priority": priority,
            "blocking": False,
            "parent_task_id": parent_task_id,
            "subtasks": [],
            "completion_percentage": 0.0,
            "test_coverage": {
                "unit_tests": False,
                "integration_tests": False,
                "e2e_tests": False,
                "api_tests": False
            },
            "assigned_agent": None,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "notes": []
        }

        self.data["tasks"].append(task)

        # If this is a subtask, add to parent's subtask list
        if parent_task_id is not None:
            parent = self.get_task(parent_task_id)
            if parent:
                parent["subtasks"].append(task_id)

        self._save()
        return task_id

    def add_subtask(self, parent_task_id: int, subtask: Dict) -> int:
        """
        Add a subtask under a parent task.

        Args:
            parent_task_id: ID of the parent task
            subtask: Dict with 'title', optional 'description', 'priority', 'blocking'

        Returns:
            Task ID of the newly created subtask
        """
        is_blocking = subtask.get("blocking", False)

        subtask_id = self.add_task(
            title=subtask.get("title", ""),
            description=subtask.get("description", ""),
            priority=subtask.get("priority", "HIGH"),
            parent_task_id=parent_task_id
        )

        # Mark as blocking if specified
        if is_blocking:
            self.mark_task_blocking(subtask_id)

        return subtask_id

    def mark_task_blocking(self, task_id: int):
        """
        Mark a task as blocking - prevents other tasks from starting.

        Args:
            task_id: ID of task to mark as blocking
        """
        task = self.get_task(task_id)
        if task:
            task["blocking"] = True
            self._save()

    def get_task(self, task_id: int) -> Optional[Dict]:
        """
        Get task by ID.

        Args:
            task_id: Task ID to retrieve

        Returns:
            Task dict or None if not found
        """
        for task in self.data["tasks"]:
            if task["id"] == task_id:
                return task
        return None

    def get_next_available_task(self, project_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get next available task, respecting blocking tasks.

        Returns None if blocking task exists (must be resolved first).

        Args:
            project_id: Optional project ID filter (for multi-project support)

        Returns:
            Next available task or None if blocked
        """
        # Check for blocking tasks
        blocking_tasks = self.get_blocking_tasks()
        if blocking_tasks:
            return None  # Cannot proceed until blocking tasks are resolved

        # Find next pending task (prioritized)
        pending_tasks = [
            task for task in self.data["tasks"]
            if task["status"] == "Todo" and task["parent_task_id"] is None
        ]

        if not pending_tasks:
            return None

        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        pending_tasks.sort(key=lambda t: priority_order.get(t["priority"], 2))

        return pending_tasks[0]

    def get_blocking_tasks(self) -> List[Dict]:
        """
        Get all tasks marked as blocking.

        Returns:
            List of blocking tasks
        """
        return [
            task for task in self.data["tasks"]
            if task["blocking"] and task["status"] != "Done"
        ]

    def get_subtasks(self, parent_task_id: int) -> List[Dict]:
        """
        Get all subtasks for a parent task.

        Args:
            parent_task_id: Parent task ID

        Returns:
            List of subtask dicts
        """
        parent = self.get_task(parent_task_id)
        if not parent:
            return []

        subtask_ids = parent.get("subtasks", [])
        return [self.get_task(tid) for tid in subtask_ids if self.get_task(tid)]

    def calculate_task_completion(self, task_id: int) -> float:
        """
        Calculate completion percentage (0-100) based on subtasks.

        If task has no subtasks, completion is based on status:
        - Todo: 0%
        - In Progress: 50%
        - Done: 100%

        If task has subtasks, completion is average of subtask completions.

        Args:
            task_id: Task ID to calculate completion for

        Returns:
            Completion percentage (0.0 to 100.0)
        """
        task = self.get_task(task_id)
        if not task:
            return 0.0

        subtasks = self.get_subtasks(task_id)

        if not subtasks:
            # No subtasks - use status
            if task["status"] == "Done":
                return 100.0
            elif task["status"] == "In Progress":
                return 50.0
            else:
                return 0.0

        # Has subtasks - calculate average
        if len(subtasks) == 0:
            return 0.0

        total_completion = sum(
            self.calculate_task_completion(subtask["id"]) for subtask in subtasks
        )

        completion = total_completion / len(subtasks)

        # Update task's stored completion percentage
        task["completion_percentage"] = completion
        self._save()

        return completion

    def update_task_status(
        self,
        task_id: int,
        status: str,
        agent_id: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """
        Update task status.

        Args:
            task_id: Task ID to update
            status: New status (Todo, In Progress, Done, Verified, Needs Work)
            agent_id: Optional agent ID performing the update
            notes: Optional notes to add
        """
        task = self.get_task(task_id)
        if not task:
            return

        old_status = task["status"]
        task["status"] = status

        # Track timestamps
        if status == "In Progress" and not task["started_at"]:
            task["started_at"] = datetime.now().isoformat()
        elif status == "Done" and not task["completed_at"]:
            task["completed_at"] = datetime.now().isoformat()

        # Assign agent
        if agent_id and not task["assigned_agent"]:
            task["assigned_agent"] = agent_id

        # Add notes
        if notes:
            task["notes"].append({
                "timestamp": datetime.now().isoformat(),
                "agent": agent_id,
                "note": notes,
                "status_change": f"{old_status} -> {status}"
            })

        # Recalculate parent completion if this is a subtask
        if task["parent_task_id"]:
            self.calculate_task_completion(task["parent_task_id"])

        self._save()

    def update_test_coverage(
        self,
        task_id: int,
        unit_tests: bool = False,
        integration_tests: bool = False,
        e2e_tests: bool = False,
        api_tests: bool = False
    ):
        """
        Update test coverage for a task.

        Args:
            task_id: Task ID to update
            unit_tests: Whether unit tests exist
            integration_tests: Whether integration tests exist
            e2e_tests: Whether E2E tests exist
            api_tests: Whether API tests exist
        """
        task = self.get_task(task_id)
        if task:
            task["test_coverage"] = {
                "unit_tests": unit_tests,
                "integration_tests": integration_tests,
                "e2e_tests": e2e_tests,
                "api_tests": api_tests
            }
            self._save()

    def get_progress_summary(self) -> Dict[str, int]:
        """
        Get count of tasks by status.

        Returns:
            Dict mapping status to count
        """
        summary = {"Todo": 0, "In Progress": 0, "Done": 0, "Verified": 0, "Needs Work": 0}

        for task in self.data["tasks"]:
            # Only count top-level tasks (not subtasks)
            if task["parent_task_id"] is None:
                status = task["status"]
                if status in summary:
                    summary[status] += 1

        return summary

    def export_to_markdown(self, output_path: Optional[Path] = None) -> str:
        """
        Export checklist to markdown format.

        Args:
            output_path: Optional path to write markdown file

        Returns:
            Markdown string
        """
        if not output_path:
            output_path = self.project_dir / "CHECKLIST.md"

        lines = []
        lines.append(f"# {self.data['project_name']}")
        lines.append("")
        lines.append(f"**Created**: {self.data['created_at']}")
        lines.append(f"**Last Updated**: {self.data['last_updated']}")
        lines.append("")

        # Progress summary
        summary = self.get_progress_summary()
        lines.append("## Progress Summary")
        lines.append("")
        total = sum(summary.values())
        done = summary.get("Done", 0) + summary.get("Verified", 0)
        progress = (done / total * 100) if total > 0 else 0
        lines.append(f"**Overall Progress**: {done}/{total} ({progress:.1f}%)")
        lines.append("")
        for status, count in summary.items():
            lines.append(f"- {status}: {count}")
        lines.append("")

        # Blocking tasks warning
        blocking = self.get_blocking_tasks()
        if blocking:
            lines.append("## ⚠️ BLOCKING TASKS")
            lines.append("")
            lines.append("The following tasks are blocking other work and must be completed first:")
            lines.append("")
            for task in blocking:
                lines.append(f"- **Task #{task['id']}**: {task['title']}")
                lines.append(f"  - Status: {task['status']}")
                lines.append(f"  - Priority: {task['priority']}")
            lines.append("")

        # Tasks
        lines.append("## Tasks")
        lines.append("")

        # Group by status
        for status in ["Todo", "In Progress", "Needs Work", "Done", "Verified"]:
            tasks = [
                t for t in self.data["tasks"]
                if t["status"] == status and t["parent_task_id"] is None
            ]

            if tasks:
                lines.append(f"### {status}")
                lines.append("")

                for task in tasks:
                    self._append_task_markdown(task, lines, indent=0)

                lines.append("")

        markdown = "\n".join(lines)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return markdown

    def _append_task_markdown(self, task: Dict, lines: List[str], indent: int = 0):
        """Helper to append task and subtasks to markdown lines."""
        prefix = "  " * indent

        # Status checkbox
        checkbox = "☑" if task["status"] in ["Done", "Verified"] else "☐"

        # Blocking indicator
        blocking_indicator = " 🚫 BLOCKING" if task["blocking"] else ""

        lines.append(f"{prefix}- {checkbox} **Task #{task['id']}**: {task['title']}{blocking_indicator}")

        # Description
        if task["description"]:
            lines.append(f"{prefix}  - Description: {task['description']}")

        # Priority
        lines.append(f"{prefix}  - Priority: {task['priority']}")

        # Status and completion
        completion = self.calculate_task_completion(task["id"])
        lines.append(f"{prefix}  - Status: {task['status']} ({completion:.1f}% complete)")

        # Agent assignment
        if task["assigned_agent"]:
            lines.append(f"{prefix}  - Assigned to: {task['assigned_agent']}")

        # Test coverage
        test_cov = task["test_coverage"]
        if any(test_cov.values()):
            tests = []
            if test_cov["unit_tests"]:
                tests.append("Unit")
            if test_cov["integration_tests"]:
                tests.append("Integration")
            if test_cov["e2e_tests"]:
                tests.append("E2E")
            if test_cov["api_tests"]:
                tests.append("API")
            lines.append(f"{prefix}  - Tests: {', '.join(tests)}")

        # Notes
        if task["notes"]:
            lines.append(f"{prefix}  - Notes:")
            for note in task["notes"]:
                lines.append(f"{prefix}    - [{note['timestamp']}] {note['note']}")

        # Subtasks
        subtasks = self.get_subtasks(task["id"])
        if subtasks:
            lines.append(f"{prefix}  - Subtasks:")
            for subtask in subtasks:
                self._append_task_markdown(subtask, lines, indent + 2)

    def start_session(self, session_name: str, agent_type: str):
        """
        Start a new work session.

        Args:
            session_name: Name/description of the session
            agent_type: Type of agent running the session
        """
        session = {
            "name": session_name,
            "agent_type": agent_type,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "tasks_completed": [],
            "notes": []
        }
        self.data["sessions"].append(session)
        self._save()

    def end_session(self, notes: Optional[str] = None):
        """
        End the current session.

        Args:
            notes: Optional notes about the session
        """
        if self.data["sessions"]:
            session = self.data["sessions"][-1]
            session["end_time"] = datetime.now().isoformat()
            if notes:
                session["notes"].append(notes)
            self._save()

"""
Checklist Manager
=================

Local task tracking system for project tasks and progress.
Maintains a JSON-based checklist for project tasks and progress.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


# Checklist file name
CHECKLIST_FILE = ".project_checklist.json"

# Task statuses
STATUS_TODO = "Todo"
STATUS_IN_PROGRESS = "In Progress"
STATUS_DONE = "Done"
STATUS_BLOCKED = "Blocked"

# Valid status values
VALID_STATUSES = {STATUS_TODO, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_BLOCKED}


class ChecklistManager:
    """Manages project checklist and task tracking."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.checklist_path = project_dir / CHECKLIST_FILE
        self.data = self._load()

    def _load(self) -> dict:
        """Load checklist from file or create new one."""
        if self.checklist_path.exists():
            try:
                with open(self.checklist_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Create new checklist structure
        return {
            "initialized": False,
            "project_name": "",
            "created_at": datetime.now().isoformat(),
            "tasks": [],
            "sessions": []
        }

    def _save(self):
        """Save checklist to file."""
        with open(self.checklist_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def initialize(self, project_name: str, tasks: List[Dict[str, str]]):
        """
        Initialize the checklist with tasks.

        Args:
            project_name: Name of the project
            tasks: List of task dicts with 'title' and 'description'
        """
        self.data["initialized"] = True
        self.data["project_name"] = project_name
        self.data["tasks"] = [
            {
                "id": i + 1,
                "title": task["title"],
                "description": task.get("description", ""),
                "status": STATUS_TODO,
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
                "notes": []
            }
            for i, task in enumerate(tasks)
        ]
        self._save()

    def is_initialized(self) -> bool:
        """Check if checklist is initialized."""
        return self.data.get("initialized", False)

    def get_next_task(self) -> Optional[Dict]:
        """Get the next todo task."""
        for task in self.data["tasks"]:
            if task["status"] == STATUS_TODO:
                return task
        return None

    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """Get task by ID."""
        for task in self.data["tasks"]:
            if task["id"] == task_id:
                return task
        return None

    def update_task_status(self, task_id: int, status: str, note: str = ""):
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status (Todo, In Progress, Done, Blocked)
            note: Optional note to add

        Raises:
            ValueError: If status is not a valid status value
        """
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

        task = self.get_task_by_id(task_id)
        if task:
            task["status"] = status
            if status == STATUS_DONE:
                task["completed_at"] = datetime.now().isoformat()
            if note:
                task["notes"].append({
                    "timestamp": datetime.now().isoformat(),
                    "content": note
                })
            self._save()

    def add_task_note(self, task_id: int, note: str):
        """Add a note to a task."""
        task = self.get_task_by_id(task_id)
        if task:
            task["notes"].append({
                "timestamp": datetime.now().isoformat(),
                "content": note
            })
            self._save()

    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks."""
        return self.data["tasks"]

    def get_tasks_by_status(self, status: str) -> List[Dict]:
        """Get tasks by status."""
        return [task for task in self.data["tasks"] if task["status"] == status]

    def get_progress_summary(self) -> Dict[str, int]:
        """Get progress summary with counts."""
        summary = {
            STATUS_TODO: 0,
            STATUS_IN_PROGRESS: 0,
            STATUS_DONE: 0
        }
        for task in self.data["tasks"]:
            status = task["status"]
            if status in summary:
                summary[status] += 1
        return summary

    def add_session_log(self, session_num: int, summary: str):
        """Add a session log entry."""
        self.data["sessions"].append({
            "session_num": session_num,
            "timestamp": datetime.now().isoformat(),
            "summary": summary
        })
        self._save()

    def get_session_logs(self) -> List[Dict]:
        """Get all session logs."""
        return self.data.get("sessions", [])

    def export_to_markdown(self, output_path: Optional[Path] = None) -> str:
        """
        Export checklist to markdown format.

        Args:
            output_path: Optional path to save markdown file. If None, returns string only.

        Returns:
            Markdown formatted checklist
        """
        if not output_path:
            output_path = self.project_dir / "CHECKLIST.md"

        # Generate markdown content
        lines = []
        lines.append(f"# Project Checklist: {self.data.get('project_name', 'Untitled')}\n")
        lines.append(f"**Created:** {self.data.get('created_at', 'Unknown')}\n")

        summary = self.get_progress_summary()
        total = sum(summary.values())
        done_count = summary[STATUS_DONE]
        progress_pct = (done_count / total * 100) if total > 0 else 0

        lines.append(f"\n## Progress: {done_count}/{total} tasks completed ({progress_pct:.1f}%)\n")
        lines.append(f"- ✓ Done: {summary[STATUS_DONE]}\n")
        lines.append(f"- ⚙ In Progress: {summary[STATUS_IN_PROGRESS]}\n")
        lines.append(f"- ☐ Todo: {summary[STATUS_TODO]}\n")

        lines.append("\n---\n")
        lines.append("\n## Tasks\n")

        for task in self.data["tasks"]:
            status_checkbox = {
                STATUS_DONE: "[x]",
                STATUS_IN_PROGRESS: "[-]",
                STATUS_TODO: "[ ]"
            }.get(task["status"], "[ ]")

            lines.append(f"\n### {status_checkbox} Task #{task['id']}: {task['title']}\n")

            if task.get("description"):
                lines.append(f"\n{task['description']}\n")

            lines.append(f"\n**Status:** {task['status']}\n")

            if task.get("completed_at"):
                lines.append(f"**Completed:** {task['completed_at']}\n")

            if task.get("notes"):
                lines.append("\n**Notes:**\n")
                for note in task["notes"]:
                    timestamp = note.get("timestamp", "")
                    content = note.get("content", "")
                    lines.append(f"- [{timestamp}] {content}\n")

        # Add session logs if any
        sessions = self.get_session_logs()
        if sessions:
            lines.append("\n---\n")
            lines.append("\n## Session History\n")
            for session in sessions:
                lines.append(f"\n### Session {session['session_num']} - {session['timestamp']}\n")
                lines.append(f"{session['summary']}\n")

        markdown_content = "".join(lines)

        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return markdown_content


def create_checklist_manager(project_dir: Path) -> ChecklistManager:
    """Create a ChecklistManager instance."""
    return ChecklistManager(project_dir)

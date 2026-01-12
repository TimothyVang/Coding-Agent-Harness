"""
Project Registry
================

Multi-project management system for tracking and managing multiple concurrent projects.

Features:
- Project registration with unique IDs
- Status tracking (active, paused, completed, archived)
- Workload distribution calculation for load balancing
- Project metadata storage
- Last activity tracking
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ProjectRegistry:
    """
    Manages multiple projects for the agent army.

    Responsibilities:
    - Register new projects with unique IDs
    - Track project status and metadata
    - Calculate workload distribution for load balancing
    - Provide project listing and filtering
    - Track activity timestamps
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize project registry.

        Args:
            registry_path: Path to registry file (defaults to .agent_army/projects.json)
        """
        if registry_path is None:
            # Default to .agent_army directory in current working directory
            registry_dir = Path.cwd() / ".agent_army"
            registry_dir.mkdir(parents=True, exist_ok=True)
            self.registry_path = registry_dir / "projects.json"
        else:
            self.registry_path = Path(registry_path)
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        self.data = self._load_or_create()

    def _load_or_create(self) -> Dict:
        """Load existing registry or create new structure."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "projects": {}
            }

    def _save(self):
        """Save registry to disk."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def register_project(
        self,
        name: str,
        path: Path,
        spec_file: Optional[Path] = None,
        priority: int = 1
    ) -> str:
        """
        Register a new project.

        Args:
            name: Project name
            path: Path to project directory
            spec_file: Optional path to specification file
            priority: Project priority (1 = highest)

        Returns:
            Project ID (UUID string)
        """
        project_id = f"proj-{str(uuid.uuid4())[:8]}"

        project_path = Path(path).resolve()
        checklist_path = project_path / ".project_checklist.json"

        project_data = {
            "id": project_id,
            "name": name,
            "path": str(project_path),
            "spec_file": str(spec_file.resolve()) if spec_file else None,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "checklist_path": str(checklist_path),
            "priority": priority,
            "total_tasks": 0,
            "completed_tasks": 0,
            "agents_assigned": [],
            "tags": [],
            "metadata": {}
        }

        self.data["projects"][project_id] = project_data
        self._save()

        return project_id

    def get_project(self, project_id: str) -> Optional[Dict]:
        """
        Get project by ID.

        Args:
            project_id: Project ID to retrieve

        Returns:
            Project dict or None if not found
        """
        return self.data["projects"].get(project_id)

    def list_projects(
        self,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        List all projects, optionally filtered.

        Args:
            status: Optional status filter (active, paused, completed, archived)
            tags: Optional list of tags to filter by

        Returns:
            List of project dicts
        """
        projects = list(self.data["projects"].values())

        # Filter by status
        if status:
            projects = [p for p in projects if p["status"] == status]

        # Filter by tags
        if tags:
            projects = [
                p for p in projects
                if any(tag in p.get("tags", []) for tag in tags)
            ]

        # Sort by priority (ascending) and last activity (descending)
        projects.sort(key=lambda p: (p["priority"], -self._parse_datetime(p["last_activity"]).timestamp()))

        return projects

    def update_project_status(self, project_id: str, status: str):
        """
        Update project status.

        Args:
            project_id: Project ID to update
            status: New status (active, paused, completed, archived)
        """
        project = self.get_project(project_id)
        if project:
            project["status"] = status
            project["last_activity"] = datetime.now().isoformat()
            self._save()

    def update_project_activity(self, project_id: str):
        """
        Update last activity timestamp for a project.

        Args:
            project_id: Project ID to update
        """
        project = self.get_project(project_id)
        if project:
            project["last_activity"] = datetime.now().isoformat()
            self._save()

    def update_project_stats(
        self,
        project_id: str,
        total_tasks: Optional[int] = None,
        completed_tasks: Optional[int] = None
    ):
        """
        Update project task statistics.

        Args:
            project_id: Project ID to update
            total_tasks: Total number of tasks
            completed_tasks: Number of completed tasks
        """
        project = self.get_project(project_id)
        if project:
            if total_tasks is not None:
                project["total_tasks"] = total_tasks
            if completed_tasks is not None:
                project["completed_tasks"] = completed_tasks
            project["last_activity"] = datetime.now().isoformat()
            self._save()

    def assign_agent(self, project_id: str, agent_id: str):
        """
        Assign an agent to a project.

        Args:
            project_id: Project ID
            agent_id: Agent ID to assign
        """
        project = self.get_project(project_id)
        if project:
            if agent_id not in project["agents_assigned"]:
                project["agents_assigned"].append(agent_id)
                project["last_activity"] = datetime.now().isoformat()
                self._save()

    def unassign_agent(self, project_id: str, agent_id: str):
        """
        Unassign an agent from a project.

        Args:
            project_id: Project ID
            agent_id: Agent ID to unassign
        """
        project = self.get_project(project_id)
        if project and agent_id in project["agents_assigned"]:
            project["agents_assigned"].remove(agent_id)
            project["last_activity"] = datetime.now().isoformat()
            self._save()

    def add_project_tag(self, project_id: str, tag: str):
        """
        Add a tag to a project.

        Args:
            project_id: Project ID
            tag: Tag to add
        """
        project = self.get_project(project_id)
        if project:
            if tag not in project.get("tags", []):
                if "tags" not in project:
                    project["tags"] = []
                project["tags"].append(tag)
                self._save()

    def set_project_metadata(self, project_id: str, key: str, value: any):
        """
        Set project metadata field.

        Args:
            project_id: Project ID
            key: Metadata key
            value: Metadata value
        """
        project = self.get_project(project_id)
        if project:
            if "metadata" not in project:
                project["metadata"] = {}
            project["metadata"][key] = value
            self._save()

    def get_workload_distribution(self, active_only: bool = True) -> Dict[str, int]:
        """
        Calculate workload distribution across projects.

        Returns number of pending tasks per project for load balancing.

        Args:
            active_only: Only include active projects

        Returns:
            Dict mapping project_id to number of pending tasks
        """
        distribution = {}

        projects = self.list_projects(status="active" if active_only else None)

        for project in projects:
            pending_tasks = project["total_tasks"] - project["completed_tasks"]
            distribution[project["id"]] = max(0, pending_tasks)

        return distribution

    def get_project_by_path(self, path: Path) -> Optional[Dict]:
        """
        Find project by its path.

        Args:
            path: Project path to search for

        Returns:
            Project dict or None if not found
        """
        path_str = str(Path(path).resolve())
        for project in self.data["projects"].values():
            if project["path"] == path_str:
                return project
        return None

    def delete_project(self, project_id: str):
        """
        Delete a project from the registry.

        Args:
            project_id: Project ID to delete
        """
        if project_id in self.data["projects"]:
            del self.data["projects"][project_id]
            self._save()

    def get_active_project_count(self) -> int:
        """
        Get count of active projects.

        Returns:
            Number of active projects
        """
        return len(self.list_projects(status="active"))

    def get_summary(self) -> Dict:
        """
        Get summary statistics for all projects.

        Returns:
            Dict with summary statistics
        """
        projects = list(self.data["projects"].values())

        total = len(projects)
        by_status = {
            "active": len([p for p in projects if p["status"] == "active"]),
            "paused": len([p for p in projects if p["status"] == "paused"]),
            "completed": len([p for p in projects if p["status"] == "completed"]),
            "archived": len([p for p in projects if p["status"] == "archived"])
        }

        total_tasks = sum(p["total_tasks"] for p in projects)
        completed_tasks = sum(p["completed_tasks"] for p in projects)

        return {
            "total_projects": total,
            "by_status": by_status,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }

    def _parse_datetime(self, iso_string: str) -> datetime:
        """Parse ISO format datetime string."""
        try:
            return datetime.fromisoformat(iso_string)
        except (ValueError, AttributeError):
            return datetime.now()

    def export_to_markdown(self, output_path: Optional[Path] = None) -> str:
        """
        Export project registry to markdown format.

        Args:
            output_path: Optional path to write markdown file

        Returns:
            Markdown string
        """
        if not output_path:
            output_path = self.registry_path.parent / "PROJECTS.md"

        lines = []
        lines.append("# Project Registry")
        lines.append("")
        lines.append(f"**Last Updated**: {self.data['last_updated']}")
        lines.append("")

        # Summary
        summary = self.get_summary()
        lines.append("## Summary")
        lines.append("")
        lines.append(f"**Total Projects**: {summary['total_projects']}")
        lines.append(f"**Active**: {summary['by_status']['active']}")
        lines.append(f"**Paused**: {summary['by_status']['paused']}")
        lines.append(f"**Completed**: {summary['by_status']['completed']}")
        lines.append(f"**Archived**: {summary['by_status']['archived']}")
        lines.append("")
        lines.append(f"**Total Tasks**: {summary['total_tasks']}")
        lines.append(f"**Completed Tasks**: {summary['completed_tasks']}")
        lines.append(f"**Completion Rate**: {summary['completion_rate']:.1f}%")
        lines.append("")

        # Projects by status
        for status in ["active", "paused", "completed", "archived"]:
            projects = self.list_projects(status=status)

            if projects:
                lines.append(f"## {status.capitalize()} Projects")
                lines.append("")

                for project in projects:
                    lines.append(f"### {project['name']} (`{project['id']}`)")
                    lines.append("")
                    lines.append(f"- **Path**: `{project['path']}`")
                    lines.append(f"- **Priority**: {project['priority']}")
                    lines.append(f"- **Tasks**: {project['completed_tasks']}/{project['total_tasks']}")

                    if project['completed_tasks'] > 0 and project['total_tasks'] > 0:
                        progress = project['completed_tasks'] / project['total_tasks'] * 100
                        lines.append(f"- **Progress**: {progress:.1f}%")

                    lines.append(f"- **Last Activity**: {project['last_activity']}")

                    if project['agents_assigned']:
                        lines.append(f"- **Agents**: {', '.join(project['agents_assigned'])}")

                    if project.get('tags'):
                        lines.append(f"- **Tags**: {', '.join(project['tags'])}")

                    lines.append("")

        markdown = "\n".join(lines)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return markdown

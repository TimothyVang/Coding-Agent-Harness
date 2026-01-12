"""
Agent Memory System
===================

Persistent memory system for agents to learn, improve, and remember.

Features:
- Persistent memory storage (markdown format)
- Pattern learning and reuse
- Mistake tracking and avoidance
- Self-improvement goals
- Knowledge base management
- Cross-agent feedback integration
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AgentMemory:
    """
    Persistent memory system for an individual agent.

    Stores:
    - Task history and performance metrics
    - Learned patterns (successful approaches)
    - Mistakes to avoid
    - Self-improvement goals
    - Knowledge base (libraries, techniques)
    - Feedback from other agents
    """

    def __init__(self, agent_id: str, memory_dir: Optional[Path] = None):
        """
        Initialize agent memory.

        Args:
            agent_id: Unique agent identifier
            memory_dir: Optional memory directory (defaults to AGENT_MEMORY/)
        """
        self.agent_id = agent_id

        if memory_dir is None:
            memory_dir = Path.cwd() / "AGENT_MEMORY" / agent_id
        else:
            memory_dir = Path(memory_dir) / agent_id

        memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir = memory_dir

        # Memory files
        self.memory_file = self.memory_dir / "memory.md"
        self.patterns_file = self.memory_dir / "learned_patterns.md"
        self.mistakes_file = self.memory_dir / "mistakes.md"
        self.knowledge_file = self.memory_dir / "knowledge_base.md"

        self.data = self._load_or_create()

    def _load_or_create(self) -> Dict:
        """Load existing memory or create new structure."""
        if self.memory_file.exists():
            return self._parse_memory_markdown()
        else:
            return {
                "agent_id": self.agent_id,
                "agent_type": "unknown",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "stats": {
                    "total_tasks": 0,
                    "successful_tasks": 0,
                    "failed_tasks": 0,
                    "success_rate": 0.0,
                    "average_duration_minutes": 0.0
                },
                "recent_context": {
                    "last_task": None,
                    "last_project": None,
                    "current_focus": None
                },
                "strengths": [],
                "weaknesses": [],
                "patterns": [],
                "mistakes": [],
                "knowledge": [],
                "feedback": [],
                "goals": []
            }

    def _parse_memory_markdown(self) -> Dict:
        """Parse memory markdown file into structured data."""
        content = self.memory_file.read_text(encoding='utf-8')

        data = {
            "agent_id": self.agent_id,
            "agent_type": "unknown",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "stats": {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "success_rate": 0.0,
                "average_duration_minutes": 0.0
            },
            "recent_context": {},
            "strengths": [],
            "weaknesses": [],
            "patterns": [],
            "mistakes": [],
            "knowledge": [],
            "feedback": [],
            "goals": []
        }

        # Parse basic info
        if match := re.search(r'\*\*Agent Type\*\*: (.+)', content):
            data["agent_type"] = match.group(1)

        # Parse stats
        if match := re.search(r'\*\*Total Tasks Completed\*\*: (\d+)', content):
            data["stats"]["total_tasks"] = int(match.group(1))
        if match := re.search(r'\*\*Success Rate\*\*: ([\d.]+)%', content):
            data["stats"]["success_rate"] = float(match.group(1))

        return data

    def load(self):
        """Load memory from disk."""
        self.data = self._load_or_create()

    def save(self):
        """Save memory to disk in markdown format."""
        markdown = self._generate_memory_markdown()
        self.memory_file.write_text(markdown, encoding='utf-8')

        # Also save patterns and mistakes to separate files
        if self.data["patterns"]:
            self._save_patterns()
        if self.data["mistakes"]:
            self._save_mistakes()

    def _generate_memory_markdown(self) -> str:
        """Generate markdown representation of memory."""
        lines = []

        # Header
        lines.append(f"# Agent Memory: {self.agent_id}")
        lines.append(f"**Agent Type**: {self.data['agent_type']}")
        lines.append(f"**Created**: {self.data['created_at']}")
        lines.append(f"**Last Updated**: {datetime.now().isoformat()}")
        lines.append(f"**Total Tasks Completed**: {self.data['stats']['total_tasks']}")
        lines.append(f"**Success Rate**: {self.data['stats']['success_rate']:.1f}%")
        lines.append("")

        # Recent context
        lines.append("## Recent Context")
        if self.data["recent_context"]:
            for key, value in self.data["recent_context"].items():
                if value:
                    lines.append(f"**{key.replace('_', ' ').title()}**: {value}")
        lines.append("")

        # Strengths
        if self.data["strengths"]:
            lines.append("## What I'm Good At")
            for strength in self.data["strengths"]:
                lines.append(f"- {strength}")
            lines.append("")

        # Weaknesses
        if self.data["weaknesses"]:
            lines.append("## What I Struggle With")
            for weakness in self.data["weaknesses"]:
                lines.append(f"- {weakness}")
            lines.append("")

        # Learned patterns summary
        if self.data["patterns"]:
            lines.append("## Learned Patterns")
            lines.append(f"Total patterns: {len(self.data['patterns'])}")
            lines.append("See `learned_patterns.md` for details.")
            lines.append("")

        # Mistakes summary
        if self.data["mistakes"]:
            lines.append("## Mistakes to Avoid")
            lines.append(f"Total mistakes recorded: {len(self.data['mistakes'])}")
            lines.append("See `mistakes.md` for details.")
            lines.append("")

        # Knowledge base
        if self.data["knowledge"]:
            lines.append("## Knowledge Base")
            for item in self.data["knowledge"][:5]:  # Show top 5
                lines.append(f"- {item}")
            if len(self.data["knowledge"]) > 5:
                lines.append(f"- ... and {len(self.data['knowledge']) - 5} more")
            lines.append("")

        # Feedback
        if self.data["feedback"]:
            lines.append("## Feedback from Other Agents")
            for feedback in self.data["feedback"][-3:]:  # Show last 3
                lines.append(f"### From {feedback['from_agent']} ({feedback['timestamp']})")
                lines.append(feedback["message"])
                lines.append("")

        # Goals
        if self.data["goals"]:
            lines.append("## Self-Improvement Goals")
            for goal in self.data["goals"]:
                status = "✓" if goal.get("completed") else "☐"
                lines.append(f"{status} {goal['goal']}")
            lines.append("")

        return "\n".join(lines)

    def _save_patterns(self):
        """Save learned patterns to separate file."""
        lines = []
        lines.append(f"# Learned Patterns: {self.agent_id}")
        lines.append("")

        for pattern in self.data["patterns"]:
            lines.append(f"## {pattern['title']}")
            lines.append(f"**Learned from**: {pattern.get('learned_from', 'Unknown')}")
            lines.append(f"**Success Rate**: {pattern.get('success_rate', 100)}%")
            lines.append(f"**Used**: {pattern.get('use_count', 1)} times")
            lines.append("")

            if pattern.get("description"):
                lines.append(pattern["description"])
                lines.append("")

            if pattern.get("code"):
                lines.append("```")
                lines.append(pattern["code"])
                lines.append("```")
                lines.append("")

        self.patterns_file.write_text("\n".join(lines), encoding='utf-8')

    def _save_mistakes(self):
        """Save mistakes to separate file."""
        lines = []
        lines.append(f"# Mistakes to Avoid: {self.agent_id}")
        lines.append("")

        for mistake in self.data["mistakes"]:
            lines.append(f"## {mistake['title']}")
            lines.append(f"**Occurred in**: {mistake.get('task_id', 'Unknown')}")
            lines.append(f"**Cost**: {mistake.get('cost_minutes', 0)} minutes")
            lines.append("")
            lines.append(f"**Error**: {mistake['error']}")
            lines.append("")
            lines.append(f"**Solution**: {mistake['solution']}")
            lines.append("")

        self.mistakes_file.write_text("\n".join(lines), encoding='utf-8')

    def add_task_result(
        self,
        task_id: str,
        success: bool,
        duration_minutes: Optional[float] = None,
        notes: str = ""
    ):
        """
        Record a task result.

        Args:
            task_id: Task ID that was completed/failed
            success: Whether task succeeded
            duration_minutes: Optional duration in minutes
            notes: Optional notes about the task
        """
        self.data["stats"]["total_tasks"] += 1

        if success:
            self.data["stats"]["successful_tasks"] += 1
        else:
            self.data["stats"]["failed_tasks"] += 1

        # Update success rate
        if self.data["stats"]["total_tasks"] > 0:
            self.data["stats"]["success_rate"] = (
                self.data["stats"]["successful_tasks"] /
                self.data["stats"]["total_tasks"] * 100
            )

        # Update average duration
        if duration_minutes:
            current_avg = self.data["stats"]["average_duration_minutes"]
            total = self.data["stats"]["total_tasks"]
            self.data["stats"]["average_duration_minutes"] = (
                (current_avg * (total - 1) + duration_minutes) / total
            )

        self.save()

    def add_pattern(
        self,
        title: str,
        description: str = "",
        code: str = "",
        learned_from: str = "",
        context: Optional[Dict] = None
    ):
        """
        Add a learned pattern.

        Args:
            title: Pattern title
            description: Pattern description
            code: Optional code snippet
            learned_from: Where this was learned from (task ID, etc.)
            context: Optional context dict
        """
        pattern = {
            "title": title,
            "description": description,
            "code": code,
            "learned_from": learned_from,
            "learned_at": datetime.now().isoformat(),
            "use_count": 1,
            "success_rate": 100.0,
            "context": context or {}
        }

        self.data["patterns"].append(pattern)
        self.save()

    def add_mistake(
        self,
        title: str,
        task_id: str,
        error: str,
        solution: str,
        cost_minutes: int = 0
    ):
        """
        Record a mistake to avoid in future.

        Args:
            title: Mistake title
            task_id: Task ID where mistake occurred
            error: Error description
            solution: How to avoid this mistake
            cost_minutes: Time cost of the mistake
        """
        mistake = {
            "title": title,
            "task_id": task_id,
            "error": error,
            "solution": solution,
            "cost_minutes": cost_minutes,
            "timestamp": datetime.now().isoformat()
        }

        self.data["mistakes"].append(mistake)
        self.save()

    def add_feedback(self, from_agent: str, message: str):
        """
        Add feedback from another agent.

        Args:
            from_agent: Agent ID providing feedback
            message: Feedback message
        """
        feedback = {
            "from_agent": from_agent,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        self.data["feedback"].append(feedback)
        self.save()

    def add_knowledge(self, item: str):
        """
        Add item to knowledge base.

        Args:
            item: Knowledge item (e.g., "React: Use hooks for state management")
        """
        if item not in self.data["knowledge"]:
            self.data["knowledge"].append(item)
            self.save()

    def add_goal(self, goal: str):
        """
        Add self-improvement goal.

        Args:
            goal: Goal description
        """
        goal_obj = {
            "goal": goal,
            "created_at": datetime.now().isoformat(),
            "completed": False,
            "completed_at": None
        }

        self.data["goals"].append(goal_obj)
        self.save()

    def complete_goal(self, goal: str):
        """
        Mark a goal as completed.

        Args:
            goal: Goal description to complete
        """
        for g in self.data["goals"]:
            if g["goal"] == goal and not g["completed"]:
                g["completed"] = True
                g["completed_at"] = datetime.now().isoformat()
                self.save()
                break

    def update_context(self, **kwargs):
        """
        Update recent context.

        Args:
            **kwargs: Context fields to update (last_task, last_project, current_focus, etc.)
        """
        self.data["recent_context"].update(kwargs)
        self.save()

    def find_similar_patterns(self, query: str) -> List[Dict]:
        """
        Find patterns similar to a query.

        Simple keyword matching - can be enhanced with embeddings.

        Args:
            query: Query string to search for

        Returns:
            List of matching pattern dicts
        """
        query_lower = query.lower()
        matches = []

        for pattern in self.data["patterns"]:
            if (query_lower in pattern["title"].lower() or
                query_lower in pattern.get("description", "").lower()):
                matches.append(pattern)

        # Sort by success rate and use count
        matches.sort(
            key=lambda p: (p.get("success_rate", 0), p.get("use_count", 0)),
            reverse=True
        )

        return matches

    def get_relevant_mistakes(self, context: str) -> List[Dict]:
        """
        Get mistakes relevant to current context.

        Args:
            context: Context string (task description, etc.)

        Returns:
            List of relevant mistake dicts
        """
        context_lower = context.lower()
        relevant = []

        for mistake in self.data["mistakes"]:
            if (context_lower in mistake["title"].lower() or
                context_lower in mistake.get("error", "").lower()):
                relevant.append(mistake)

        return relevant

    def get_strengths(self) -> List[str]:
        """
        Identify strengths based on performance.

        Returns:
            List of strength descriptions
        """
        # This is a simplified version - can be enhanced with ML
        strengths = []

        if self.data["stats"]["success_rate"] > 90:
            strengths.append(f"High success rate ({self.data['stats']['success_rate']:.1f}%)")

        if len(self.data["patterns"]) > 10:
            strengths.append(f"Extensive pattern library ({len(self.data['patterns'])} patterns)")

        return strengths

    def get_weaknesses(self) -> List[str]:
        """
        Identify weaknesses based on performance.

        Returns:
            List of weakness descriptions
        """
        weaknesses = []

        if self.data["stats"]["success_rate"] < 80:
            weaknesses.append(f"Lower success rate ({self.data['stats']['success_rate']:.1f}%)")

        if len(self.data["mistakes"]) > 5:
            # Find most common mistake types
            weaknesses.append(f"Recurring mistakes ({len(self.data['mistakes'])} recorded)")

        return weaknesses

    def generate_improvement_goals(self) -> List[str]:
        """
        Generate self-improvement goals based on weaknesses.

        Returns:
            List of goal strings
        """
        goals = []

        weaknesses = self.get_weaknesses()
        for weakness in weaknesses[:3]:  # Top 3 weaknesses
            if "success rate" in weakness.lower():
                goals.append("Improve task success rate to >90%")
            elif "mistakes" in weakness.lower():
                goals.append("Reduce recurring mistakes by reviewing common errors")

        return goals

    def get_summary(self) -> Dict:
        """
        Get summary of agent memory.

        Returns:
            Summary dict
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.data["agent_type"],
            "total_tasks": self.data["stats"]["total_tasks"],
            "success_rate": self.data["stats"]["success_rate"],
            "patterns_learned": len(self.data["patterns"]),
            "mistakes_recorded": len(self.data["mistakes"]),
            "knowledge_items": len(self.data["knowledge"]),
            "active_goals": len([g for g in self.data["goals"] if not g["completed"]])
        }

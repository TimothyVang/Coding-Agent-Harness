"""
Reporter Agent
==============

Report generation agent for creating comprehensive markdown reports.

Responsibilities:
- Project status reports
- Sprint/milestone reports
- Agent activity summaries
- Task completion reports
- Performance metrics reports
- Quality assurance reports
- Deployment reports
- Executive summaries
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_agent import BaseAgent
from core.enhanced_checklist import EnhancedChecklistManager
from core.project_registry import ProjectRegistry
from core.task_queue import TaskQueue
from core.message_bus import MessageBus, MessageTypes
from core.agent_memory import AgentMemory


class ReporterAgent(BaseAgent):
    """
    Reporter Agent - Comprehensive Report Generation

    Responsibilities:
    - Generate project status reports
    - Create sprint/milestone summaries
    - Summarize agent activities
    - Report task completion statistics
    - Generate performance metrics
    - Create quality assurance summaries
    - Produce deployment reports
    - Generate executive summaries

    This agent aggregates data from all sources to create insightful reports.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[Any] = None
    ):
        """
        Initialize ReporterAgent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="reporter",
            config=config,
            message_bus=message_bus
        )
        self.client = claude_client

        # Reporter-specific configuration
        self.report_types = config.get("report_types", [
            "project_status",
            "sprint_summary",
            "agent_activity",
            "task_completion",
            "quality_metrics",
            "deployment_summary"
        ])

        self.report_format = config.get("report_format", "markdown")
        self.include_charts = config.get("include_charts", True)  # ASCII/text charts
        self.include_recommendations = config.get("include_recommendations", True)

        print(f"[ReporterAgent] Initialized with ID: {self.agent_id}")
        print(f"  - Report types: {len(self.report_types)}")
        print(f"  - Format: {self.report_format}")
        print(f"  - Include recommendations: {self.include_recommendations}")

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a reporting task.

        Process:
        1. Load task details from checklist
        2. Determine report type needed
        3. Gather data from all sources
        4. Aggregate and analyze data
        5. Generate report sections
        6. Add visualizations (text-based)
        7. Include recommendations
        8. Generate executive summary
        9. Save report and update checklist

        Args:
            task: Task dict from queue with project_id, checklist_task_id

        Returns:
            Dict with success status and report details
        """
        project_id = task.get("project_id")
        checklist_task_id = task.get("checklist_task_id")

        try:
            # Load project checklist
            project_path = Path(self.config["projects_base_path"]) / project_id
            checklist = EnhancedChecklistManager(project_path)

            # Get task details
            task_details = checklist.get_task(checklist_task_id)
            if not task_details:
                return {
                    "success": False,
                    "error": f"Task {checklist_task_id} not found in checklist"
                }

            task_title = task_details.get("title", "Unknown task")
            self.print_status(f"Generating report: {task_title}")

            # Report result tracking
            report_result = {
                "task_id": checklist_task_id,
                "timestamp": datetime.now().isoformat(),
                "report_type": "project_status",  # default
                "sections_generated": [],
                "data_sources": [],
                "recommendations": []
            }

            # Step 1: Load patterns from memory
            self.memory.load_patterns()

            # Step 2: Determine report type
            report_type = await self._determine_report_type(task_details)
            report_result["report_type"] = report_type

            # Step 3: Gather data
            report_data = await self._gather_report_data(
                project_id,
                project_path,
                checklist,
                report_type
            )
            report_result["data_sources"] = report_data.get("sources", [])

            # Step 4: Generate report
            report_content = await self._generate_report(
                report_type,
                report_data,
                task_details,
                project_id
            )

            # Step 5: Add recommendations if enabled
            if self.include_recommendations:
                recommendations = await self._generate_recommendations(report_data)
                report_result["recommendations"] = recommendations

            # Step 6: Save report
            report_path = project_path / "reports"
            report_path.mkdir(exist_ok=True)

            report_filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_file = report_path / report_filename

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"[Reporter] Report saved to: {report_file}")

            # Step 7: Update checklist
            if self.client:
                summary = f"Report generated: {report_type}"
                checklist.add_note(checklist_task_id, f"{summary} - {report_filename}")

            return {
                "success": True,
                "data": {
                    "report_result": report_result,
                    "report_content": report_content,
                    "report_file": str(report_file),
                    "report_type": report_type,
                    "sections_count": len(report_result["sections_generated"]),
                    "recommendations_count": len(report_result["recommendations"])
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Report generation failed: {str(e)}"
            }

    async def _determine_report_type(self, task_details: Dict) -> str:
        """Determine what type of report to generate."""
        title = task_details.get("title", "").lower()
        description = task_details.get("description", "").lower()
        combined = f"{title} {description}"

        if "sprint" in combined or "milestone" in combined:
            return "sprint_summary"
        elif "agent" in combined or "activity" in combined:
            return "agent_activity"
        elif "quality" in combined or "qa" in combined:
            return "quality_metrics"
        elif "deployment" in combined or "release" in combined:
            return "deployment_summary"
        elif "task" in combined or "completion" in combined:
            return "task_completion"
        else:
            return "project_status"

    async def _gather_report_data(
        self,
        project_id: str,
        project_path: Path,
        checklist: EnhancedChecklistManager,
        report_type: str
    ) -> Dict:
        """Gather data from all available sources."""
        report_data = {
            "sources": [],
            "project_stats": {},
            "task_stats": {},
            "agent_stats": {},
            "quality_stats": {},
            "time_range": {}
        }

        # Gather checklist data
        try:
            tasks = checklist.get_all_tasks()
            task_stats = {
                "total": len(tasks),
                "completed": len([t for t in tasks if t.get("status") == "Done"]),
                "in_progress": len([t for t in tasks if t.get("status") == "In Progress"]),
                "todo": len([t for t in tasks if t.get("status") == "Todo"]),
                "blocked": len([t for t in tasks if t.get("blocking", False)])
            }
            report_data["task_stats"] = task_stats
            report_data["sources"].append("Checklist")
        except Exception as e:
            print(f"[Reporter] Error gathering checklist data: {e}")

        # Gather project registry data
        try:
            project_registry = ProjectRegistry()
            projects = project_registry.list_projects()
            current_project = next((p for p in projects if p["id"] == project_id), None)
            if current_project:
                report_data["project_stats"] = current_project
                report_data["sources"].append("Project Registry")
        except Exception as e:
            print(f"[Reporter] Error gathering project registry data: {e}")

        # Gather agent memory data
        try:
            # Load agent memories for statistics
            memory_dir = self.config.get("memory_dir", Path.cwd() / "AGENT_MEMORY")
            if memory_dir.exists():
                agent_count = len(list(memory_dir.glob("*.json")))
                report_data["agent_stats"]["agents_active"] = agent_count
                report_data["sources"].append("Agent Memory")
        except Exception as e:
            print(f"[Reporter] Error gathering agent memory data: {e}")

        # Set time range
        report_data["time_range"] = {
            "start": (datetime.now() - timedelta(days=7)).isoformat(),
            "end": datetime.now().isoformat()
        }

        return report_data

    async def _generate_report(
        self,
        report_type: str,
        report_data: Dict,
        task_details: Dict,
        project_id: str
    ) -> str:
        """Generate the complete report."""
        report_lines = []

        # Report header
        report_lines.extend(self._generate_report_header(report_type, project_id))

        # Executive summary
        report_lines.extend(self._generate_executive_summary(report_data))

        # Type-specific sections
        if report_type == "project_status":
            report_lines.extend(self._generate_project_status_sections(report_data))
        elif report_type == "sprint_summary":
            report_lines.extend(self._generate_sprint_summary_sections(report_data))
        elif report_type == "agent_activity":
            report_lines.extend(self._generate_agent_activity_sections(report_data))
        elif report_type == "quality_metrics":
            report_lines.extend(self._generate_quality_metrics_sections(report_data))
        elif report_type == "deployment_summary":
            report_lines.extend(self._generate_deployment_summary_sections(report_data))
        elif report_type == "task_completion":
            report_lines.extend(self._generate_task_completion_sections(report_data))

        # Recommendations
        if self.include_recommendations:
            recommendations = await self._generate_recommendations(report_data)
            if recommendations:
                report_lines.extend(self._generate_recommendations_section(recommendations))

        # Report footer
        report_lines.extend(self._generate_report_footer())

        return "\n".join(report_lines)

    def _generate_report_header(self, report_type: str, project_id: str) -> List[str]:
        """Generate report header."""
        lines = []
        lines.append(f"# {report_type.replace('_', ' ').title()} Report")
        lines.append("")
        lines.append(f"**Project**: {project_id}")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Reporter**: {self.agent_id}")
        lines.append("")
        lines.append("---")
        lines.append("")
        return lines

    def _generate_executive_summary(self, report_data: Dict) -> List[str]:
        """Generate executive summary section."""
        lines = []
        lines.append("## Executive Summary")
        lines.append("")

        task_stats = report_data.get("task_stats", {})
        total = task_stats.get("total", 0)
        completed = task_stats.get("completed", 0)

        if total > 0:
            completion_rate = (completed / total) * 100
            lines.append(f"- **Overall Progress**: {completion_rate:.1f}% ({completed}/{total} tasks completed)")

        in_progress = task_stats.get("in_progress", 0)
        if in_progress > 0:
            lines.append(f"- **Active Work**: {in_progress} tasks in progress")

        blocked = task_stats.get("blocked", 0)
        if blocked > 0:
            lines.append(f"- **Blockers**: {blocked} tasks blocked")

        sources = report_data.get("sources", [])
        if sources:
            lines.append(f"- **Data Sources**: {', '.join(sources)}")

        lines.append("")
        return lines

    def _generate_project_status_sections(self, report_data: Dict) -> List[str]:
        """Generate project status report sections."""
        lines = []

        # Task completion section
        lines.append("## Task Completion Status")
        lines.append("")
        task_stats = report_data.get("task_stats", {})

        lines.append("| Status | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Total | {task_stats.get('total', 0)} |")
        lines.append(f"| Completed | {task_stats.get('completed', 0)} |")
        lines.append(f"| In Progress | {task_stats.get('in_progress', 0)} |")
        lines.append(f"| Todo | {task_stats.get('todo', 0)} |")
        lines.append(f"| Blocked | {task_stats.get('blocked', 0)} |")
        lines.append("")

        # Progress visualization (ASCII bar chart)
        if self.include_charts:
            lines.extend(self._generate_progress_chart(task_stats))

        return lines

    def _generate_sprint_summary_sections(self, report_data: Dict) -> List[str]:
        """Generate sprint summary sections."""
        lines = []
        lines.append("## Sprint Summary")
        lines.append("")
        lines.append("_Sprint summary details would be generated here_")
        lines.append("")
        return lines

    def _generate_agent_activity_sections(self, report_data: Dict) -> List[str]:
        """Generate agent activity sections."""
        lines = []
        lines.append("## Agent Activity")
        lines.append("")

        agent_stats = report_data.get("agent_stats", {})
        agents_active = agent_stats.get("agents_active", 0)
        lines.append(f"- **Active Agents**: {agents_active}")
        lines.append("")

        return lines

    def _generate_quality_metrics_sections(self, report_data: Dict) -> List[str]:
        """Generate quality metrics sections."""
        lines = []
        lines.append("## Quality Metrics")
        lines.append("")
        lines.append("_Quality metrics would be generated here_")
        lines.append("")
        return lines

    def _generate_deployment_summary_sections(self, report_data: Dict) -> List[str]:
        """Generate deployment summary sections."""
        lines = []
        lines.append("## Deployment Summary")
        lines.append("")
        lines.append("_Deployment summary would be generated here_")
        lines.append("")
        return lines

    def _generate_task_completion_sections(self, report_data: Dict) -> List[str]:
        """Generate task completion sections."""
        lines = []
        lines.append("## Task Completion Analysis")
        lines.append("")
        lines.append("_Task completion analysis would be generated here_")
        lines.append("")
        return lines

    def _generate_progress_chart(self, task_stats: Dict) -> List[str]:
        """Generate ASCII progress chart."""
        lines = []
        lines.append("### Progress Visualization")
        lines.append("")
        lines.append("```")

        total = task_stats.get("total", 1)
        completed = task_stats.get("completed", 0)
        in_progress = task_stats.get("in_progress", 0)
        todo = task_stats.get("todo", 0)

        # Generate bar chart
        bar_width = 50
        completed_bar = int((completed / total) * bar_width) if total > 0 else 0
        in_progress_bar = int((in_progress / total) * bar_width) if total > 0 else 0
        todo_bar = int((todo / total) * bar_width) if total > 0 else 0

        lines.append(f"Completed   [{('█' * completed_bar).ljust(bar_width)}] {completed}/{total}")
        lines.append(f"In Progress [{('█' * in_progress_bar).ljust(bar_width)}] {in_progress}/{total}")
        lines.append(f"Todo        [{('█' * todo_bar).ljust(bar_width)}] {todo}/{total}")

        lines.append("```")
        lines.append("")

        return lines

    async def _generate_recommendations(self, report_data: Dict) -> List[str]:
        """Generate recommendations based on report data."""
        recommendations = []

        task_stats = report_data.get("task_stats", {})
        blocked = task_stats.get("blocked", 0)
        total = task_stats.get("total", 1)
        completed = task_stats.get("completed", 0)

        # Check for blockers
        if blocked > 0:
            recommendations.append(f"Address {blocked} blocked task(s) to unblock progress")

        # Check completion rate
        completion_rate = (completed / total) * 100 if total > 0 else 0
        if completion_rate < 50:
            recommendations.append("Consider allocating more resources to increase completion rate")
        elif completion_rate > 90:
            recommendations.append("Project is nearing completion - prepare for final verification")

        return recommendations

    def _generate_recommendations_section(self, recommendations: List[str]) -> List[str]:
        """Generate recommendations section."""
        lines = []
        lines.append("## Recommendations")
        lines.append("")

        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")

        lines.append("")
        return lines

    def _generate_report_footer(self) -> List[str]:
        """Generate report footer."""
        lines = []
        lines.append("---")
        lines.append("")
        lines.append(f"*Report generated by {self.agent_id} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        return lines

    def get_system_prompt(self) -> str:
        """Get system prompt for the Reporter Agent."""
        return f"""You are {self.agent_id}, a Reporter Agent in the Universal AI Development Platform.

Your role is to generate comprehensive, insightful reports about project status and agent activities.

**Responsibilities:**
1. Generate project status reports
2. Create sprint/milestone summaries
3. Summarize agent activities and performance
4. Report task completion statistics
5. Generate quality assurance metrics
6. Create deployment summaries
7. Produce executive summaries
8. Provide actionable recommendations

**Reporting Process:**
1. Determine report type needed
2. Gather data from all available sources (checklist, registry, memory)
3. Aggregate and analyze data
4. Generate report sections
5. Add visualizations (text-based charts)
6. Include actionable recommendations
7. Create executive summary
8. Save report and update checklist

**Report Types:**
- Project Status: Overall project health and progress
- Sprint Summary: Sprint goals, achievements, blockers
- Agent Activity: Agent performance and coordination
- Task Completion: Detailed task analysis
- Quality Metrics: Test coverage, code quality, issues
- Deployment Summary: Deployment history and status

**Report Best Practices:**
- Start with executive summary
- Use clear visualizations
- Provide actionable insights
- Include relevant metrics
- Add context and trends
- Highlight blockers and risks
- Provide recommendations
- Use consistent formatting

**Tools Available:**
- EnhancedChecklistManager: Task data
- ProjectRegistry: Project information
- TaskQueue: Queue statistics
- AgentMemory: Agent performance data
- MessageBus: Communication logs

Generate clear, actionable reports that help stakeholders make informed decisions."""

    def extract_patterns(self, result: Dict) -> List[str]:
        """
        Extract learnable patterns from report results.

        Args:
            result: Task execution result

        Returns:
            List of pattern descriptions
        """
        patterns = []

        if not result.get("success"):
            return patterns

        data = result.get("data", {})
        report_result = data.get("report_result", {})

        # Pattern: Report type
        report_type = report_result.get("report_type")
        if report_type:
            patterns.append(f"Report type: {report_type}")

        # Pattern: Sections generated
        sections = len(report_result.get("sections_generated", []))
        if sections > 0:
            patterns.append(f"Report sections: {sections}")

        # Pattern: Recommendations provided
        recommendations = len(report_result.get("recommendations", []))
        if recommendations > 0:
            patterns.append(f"Recommendations: {recommendations}")

        return patterns


# Example usage
async def example_usage():
    """Example of using the ReporterAgent."""
    from core.message_bus import MessageBus
    from pathlib import Path

    config = {
        "memory_dir": Path("./AGENT_MEMORY"),
        "projects_base_path": Path("./projects"),
        "report_format": "markdown",
        "include_charts": True,
        "include_recommendations": True
    }

    message_bus = MessageBus()

    agent = ReporterAgent(
        agent_id="reporter-001",
        config=config,
        message_bus=message_bus,
        claude_client=None  # Would be actual client in production
    )

    await agent.initialize()

    # Example task
    task = {
        "task_id": "queue-task-123",
        "project_id": "my-project",
        "checklist_task_id": 20,
        "type": "report",
        "metadata": {
            "description": "Generate project status report"
        }
    }

    result = await agent.run_task(task)
    print(f"Report result: {result}")

    await agent.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

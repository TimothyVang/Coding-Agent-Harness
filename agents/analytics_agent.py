"""
Analytics Agent
===============

Pattern analysis and insights agent for continuous improvement.

Responsibilities:
- Cross-agent pattern analysis
- Performance trend identification
- Bottleneck detection
- Process optimization recommendations
- Learning opportunity identification
- Success pattern extraction
- Failure pattern analysis
- Strategic insights generation
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter, defaultdict

from .base_agent import BaseAgent
from core.enhanced_checklist import EnhancedChecklistManager
from core.project_registry import ProjectRegistry
from core.task_queue import TaskQueue
from core.message_bus import MessageBus, MessageTypes
from core.agent_memory import AgentMemory


class AnalyticsAgent(BaseAgent):
    """
    Analytics Agent - Pattern Analysis and Strategic Insights

    Responsibilities:
    - Analyze patterns across all agent activities
    - Identify performance trends
    - Detect bottlenecks and inefficiencies
    - Recommend process optimizations
    - Identify learning opportunities
    - Extract success patterns
    - Analyze failure patterns
    - Generate strategic insights

    This is a meta-level agent that helps the entire system continuously improve.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[Any] = None
    ):
        """
        Initialize AnalyticsAgent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="analytics",
            config=config,
            message_bus=message_bus
        )
        self.client = claude_client

        # Analytics-specific configuration
        self.analysis_types = config.get("analysis_types", [
            "agent_performance",
            "task_patterns",
            "bottleneck_detection",
            "success_patterns",
            "failure_analysis",
            "optimization_opportunities"
        ])

        self.lookback_days = config.get("lookback_days", 30)  # Historical analysis period
        self.min_pattern_frequency = config.get("min_pattern_frequency", 3)  # Minimum occurrences to be a pattern
        self.trend_threshold = config.get("trend_threshold", 0.1)  # 10% change to be a trend

        print(f"[AnalyticsAgent] Initialized with ID: {self.agent_id}")
        print(f"  - Analysis types: {len(self.analysis_types)}")
        print(f"  - Lookback period: {self.lookback_days} days")
        print(f"  - Pattern threshold: {self.min_pattern_frequency} occurrences")

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute an analytics task.

        Process:
        1. Load task details from checklist
        2. Gather data from all agents and systems
        3. Analyze agent performance trends
        4. Identify task completion patterns
        5. Detect bottlenecks
        6. Extract success patterns
        7. Analyze failures
        8. Generate optimization recommendations
        9. Create insights report
        10. Update checklist

        Args:
            task: Task dict from queue with project_id, checklist_task_id

        Returns:
            Dict with success status and analytics results
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
            self.print_status(f"Analytics: {task_title}")

            # Analytics result tracking
            analytics_result = {
                "task_id": checklist_task_id,
                "timestamp": datetime.now().isoformat(),
                "analysis_period": {
                    "start": (datetime.now() - timedelta(days=self.lookback_days)).isoformat(),
                    "end": datetime.now().isoformat()
                },
                "insights": [],
                "recommendations": [],
                "patterns_identified": [],
                "trends": [],
                "bottlenecks": []
            }

            # Step 1: Load patterns from memory
            self.memory.load_patterns()

            # Step 2: Gather analytics data
            analytics_data = await self._gather_analytics_data(project_id, project_path)

            # Step 3: Analyze agent performance
            agent_performance = await self._analyze_agent_performance(analytics_data)
            if agent_performance.get("insights"):
                analytics_result["insights"].extend(agent_performance["insights"])
            if agent_performance.get("trends"):
                analytics_result["trends"].extend(agent_performance["trends"])

            # Step 4: Identify task patterns
            task_patterns = await self._identify_task_patterns(analytics_data)
            analytics_result["patterns_identified"].extend(task_patterns.get("patterns", []))

            # Step 5: Detect bottlenecks
            bottlenecks = await self._detect_bottlenecks(analytics_data)
            analytics_result["bottlenecks"] = bottlenecks.get("bottlenecks", [])

            # Step 6: Extract success patterns
            success_patterns = await self._extract_success_patterns(analytics_data)
            if success_patterns.get("patterns"):
                analytics_result["patterns_identified"].extend(success_patterns["patterns"])

            # Step 7: Analyze failures
            failure_analysis = await self._analyze_failures(analytics_data)
            if failure_analysis.get("insights"):
                analytics_result["insights"].extend(failure_analysis["insights"])

            # Step 8: Generate optimization recommendations
            recommendations = await self._generate_optimization_recommendations(
                agent_performance,
                task_patterns,
                bottlenecks,
                success_patterns,
                failure_analysis
            )
            analytics_result["recommendations"] = recommendations

            # Step 9: Create insights report
            insights_report = await self._create_insights_report(
                analytics_result,
                analytics_data
            )

            # Step 10: Update checklist
            if self.client:
                summary = f"Analytics complete: {len(analytics_result['insights'])} insights, {len(analytics_result['recommendations'])} recommendations"
                checklist.add_note(checklist_task_id, summary)

            return {
                "success": True,
                "data": {
                    "analytics_result": analytics_result,
                    "insights_report": insights_report,
                    "insights_count": len(analytics_result["insights"]),
                    "recommendations_count": len(analytics_result["recommendations"]),
                    "patterns_count": len(analytics_result["patterns_identified"]),
                    "bottlenecks_count": len(analytics_result["bottlenecks"])
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Analytics task execution failed: {str(e)}"
            }

    async def _gather_analytics_data(self, project_id: str, project_path: Path) -> Dict:
        """Gather comprehensive analytics data from all sources."""
        data = {
            "agent_memories": [],
            "task_data": {},
            "project_data": {},
            "queue_data": {},
            "timestamp": datetime.now().isoformat()
        }

        # Gather agent memory data
        memory_dir = self.config.get("memory_dir", Path.cwd() / "AGENT_MEMORY")
        if memory_dir.exists():
            for memory_file in memory_dir.glob("*.json"):
                try:
                    with open(memory_file, 'r') as f:
                        memory_data = json.load(f)
                        data["agent_memories"].append({
                            "agent_id": memory_file.stem,
                            "data": memory_data
                        })
                except Exception as e:
                    print(f"[Analytics] Error loading memory {memory_file}: {e}")

        # Gather task data
        try:
            checklist = EnhancedChecklistManager(project_path)
            tasks = checklist.get_all_tasks()
            data["task_data"] = {
                "tasks": tasks,
                "total": len(tasks),
                "by_status": self._group_by_status(tasks),
                "by_category": self._group_by_category(tasks)
            }
        except Exception as e:
            print(f"[Analytics] Error gathering task data: {e}")

        # Gather project registry data
        try:
            registry = ProjectRegistry()
            projects = registry.list_projects()
            current_project = next((p for p in projects if p["id"] == project_id), None)
            data["project_data"] = current_project or {}
        except Exception as e:
            print(f"[Analytics] Error gathering project data: {e}")

        return data

    def _group_by_status(self, tasks: List[Dict]) -> Dict:
        """Group tasks by status."""
        status_counts = Counter(t.get("status", "Unknown") for t in tasks)
        return dict(status_counts)

    def _group_by_category(self, tasks: List[Dict]) -> Dict:
        """Group tasks by category."""
        category_counts = Counter(t.get("category", "uncategorized") for t in tasks)
        return dict(category_counts)

    async def _analyze_agent_performance(self, analytics_data: Dict) -> Dict:
        """Analyze agent performance across all agents."""
        print("[Analytics] Analyzing agent performance...")

        performance = {
            "insights": [],
            "trends": [],
            "agent_stats": {}
        }

        agent_memories = analytics_data.get("agent_memories", [])

        # Analyze each agent
        for agent_memory in agent_memories:
            agent_id = agent_memory.get("agent_id")
            memory_data = agent_memory.get("data", {})

            # Extract statistics
            stats = memory_data.get("statistics", {})
            tasks_completed = stats.get("tasks_completed", 0)
            success_rate = stats.get("success_rate", 0.0)

            performance["agent_stats"][agent_id] = {
                "tasks_completed": tasks_completed,
                "success_rate": success_rate
            }

            # Generate insights
            if success_rate < 0.7:
                performance["insights"].append(f"{agent_id} has low success rate ({success_rate:.1%})")
            elif success_rate > 0.95:
                performance["insights"].append(f"{agent_id} has excellent success rate ({success_rate:.1%})")

        return performance

    async def _identify_task_patterns(self, analytics_data: Dict) -> Dict:
        """Identify patterns in task completion."""
        print("[Analytics] Identifying task patterns...")

        patterns = {
            "patterns": [],
            "common_categories": [],
            "completion_trends": {}
        }

        task_data = analytics_data.get("task_data", {})
        by_category = task_data.get("by_category", {})

        # Find most common task categories
        if by_category:
            sorted_categories = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
            patterns["common_categories"] = [cat for cat, count in sorted_categories[:5]]

            # Generate pattern insights
            for category, count in sorted_categories[:3]:
                if count >= self.min_pattern_frequency:
                    patterns["patterns"].append(f"Frequent {category} tasks: {count} occurrences")

        return patterns

    async def _detect_bottlenecks(self, analytics_data: Dict) -> Dict:
        """Detect bottlenecks in the development process."""
        print("[Analytics] Detecting bottlenecks...")

        bottlenecks = {
            "bottlenecks": [],
            "severity": {}
        }

        task_data = analytics_data.get("task_data", {})
        by_status = task_data.get("by_status", {})

        # Check for blocked tasks
        blocked = by_status.get("Blocked", 0)
        if blocked > 0:
            total = task_data.get("total", 1)
            blocked_percentage = (blocked / total) * 100
            severity = "high" if blocked_percentage > 10 else "medium"
            bottlenecks["bottlenecks"].append({
                "type": "blocked_tasks",
                "count": blocked,
                "percentage": blocked_percentage,
                "severity": severity,
                "description": f"{blocked} tasks blocked ({blocked_percentage:.1f}%)"
            })

        # Check for tasks stuck in progress
        in_progress = by_status.get("In Progress", 0)
        todo = by_status.get("Todo", 0)
        if in_progress > 0 and todo > 0:
            ratio = in_progress / (in_progress + todo)
            if ratio > 0.7:  # More than 70% in progress
                bottlenecks["bottlenecks"].append({
                    "type": "high_wip",
                    "ratio": ratio,
                    "severity": "medium",
                    "description": f"High work-in-progress ratio ({ratio:.1%})"
                })

        return bottlenecks

    async def _extract_success_patterns(self, analytics_data: Dict) -> Dict:
        """Extract patterns from successful tasks/agents."""
        print("[Analytics] Extracting success patterns...")

        success_patterns = {
            "patterns": [],
            "best_practices": []
        }

        # Analyze agent memories for successful patterns
        agent_memories = analytics_data.get("agent_memories", [])
        all_patterns = []

        for agent_memory in agent_memories:
            memory_data = agent_memory.get("data", {})
            patterns = memory_data.get("patterns", [])
            all_patterns.extend(patterns)

        # Find most common patterns
        if all_patterns:
            pattern_counts = Counter(all_patterns)
            for pattern, count in pattern_counts.most_common(10):
                if count >= self.min_pattern_frequency:
                    success_patterns["patterns"].append({
                        "pattern": pattern,
                        "frequency": count,
                        "type": "success"
                    })

        return success_patterns

    async def _analyze_failures(self, analytics_data: Dict) -> Dict:
        """Analyze failure patterns to identify improvements."""
        print("[Analytics] Analyzing failures...")

        failure_analysis = {
            "insights": [],
            "common_failures": [],
            "root_causes": []
        }

        # Analyze task failures
        task_data = analytics_data.get("task_data", {})
        tasks = task_data.get("tasks", [])
        failed_tasks = [t for t in tasks if t.get("status") == "Failed" or t.get("status") == "Blocked"]

        if failed_tasks:
            failure_rate = len(failed_tasks) / len(tasks) if tasks else 0
            if failure_rate > 0.1:  # More than 10% failure
                failure_analysis["insights"].append(f"High failure rate: {failure_rate:.1%}")

            # Analyze failure categories
            failure_categories = Counter(t.get("category", "unknown") for t in failed_tasks)
            for category, count in failure_categories.most_common(5):
                failure_analysis["common_failures"].append({
                    "category": category,
                    "count": count
                })

        return failure_analysis

    async def _generate_optimization_recommendations(
        self,
        agent_performance: Dict,
        task_patterns: Dict,
        bottlenecks: Dict,
        success_patterns: Dict,
        failure_analysis: Dict
    ) -> List[Dict]:
        """Generate actionable optimization recommendations."""
        print("[Analytics] Generating recommendations...")

        recommendations = []

        # Recommendations based on bottlenecks
        for bottleneck in bottlenecks.get("bottlenecks", []):
            if bottleneck["type"] == "blocked_tasks":
                recommendations.append({
                    "priority": "high",
                    "category": "bottleneck",
                    "title": "Address Blocked Tasks",
                    "description": f"Resolve {bottleneck['count']} blocked tasks to unblock progress",
                    "impact": "high"
                })
            elif bottleneck["type"] == "high_wip":
                recommendations.append({
                    "priority": "medium",
                    "category": "process",
                    "title": "Reduce Work-in-Progress",
                    "description": "Focus on completing existing tasks before starting new ones",
                    "impact": "medium"
                })

        # Recommendations based on success patterns
        success_pattern_list = success_patterns.get("patterns", [])
        if success_pattern_list:
            top_pattern = success_pattern_list[0] if success_pattern_list else None
            if top_pattern:
                recommendations.append({
                    "priority": "medium",
                    "category": "best_practice",
                    "title": "Apply Success Pattern",
                    "description": f"Pattern '{top_pattern.get('pattern')}' has been successful {top_pattern.get('frequency')} times",
                    "impact": "medium"
                })

        # Recommendations based on agent performance
        for agent_id, stats in agent_performance.get("agent_stats", {}).items():
            if stats.get("success_rate", 1.0) < 0.7:
                recommendations.append({
                    "priority": "high",
                    "category": "agent_performance",
                    "title": f"Investigate {agent_id} Performance",
                    "description": f"Success rate is {stats['success_rate']:.1%}, below 70% threshold",
                    "impact": "high"
                })

        # Recommendations based on failures
        failure_insights = failure_analysis.get("insights", [])
        if failure_insights:
            recommendations.append({
                "priority": "high",
                "category": "failure_mitigation",
                "title": "Reduce Failure Rate",
                "description": failure_insights[0],
                "impact": "high"
            })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))

        return recommendations

    async def _create_insights_report(self, analytics_result: Dict, analytics_data: Dict) -> str:
        """Create comprehensive insights report."""
        lines = []

        lines.append("# Analytics Insights Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().isoformat()}")
        lines.append(f"**Analyst**: {self.agent_id}")
        lines.append(f"**Analysis Period**: {self.lookback_days} days")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Executive summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"- **Insights Identified**: {len(analytics_result['insights'])}")
        lines.append(f"- **Patterns Found**: {len(analytics_result['patterns_identified'])}")
        lines.append(f"- **Bottlenecks Detected**: {len(analytics_result['bottlenecks'])}")
        lines.append(f"- **Recommendations**: {len(analytics_result['recommendations'])}")
        lines.append("")

        # Key insights
        if analytics_result.get("insights"):
            lines.append("## Key Insights")
            lines.append("")
            for i, insight in enumerate(analytics_result["insights"], 1):
                lines.append(f"{i}. {insight}")
            lines.append("")

        # Patterns identified
        if analytics_result.get("patterns_identified"):
            lines.append("## Patterns Identified")
            lines.append("")
            for pattern in analytics_result["patterns_identified"]:
                if isinstance(pattern, dict):
                    lines.append(f"- **{pattern.get('pattern')}** (frequency: {pattern.get('frequency')})")
                else:
                    lines.append(f"- {pattern}")
            lines.append("")

        # Bottlenecks
        if analytics_result.get("bottlenecks"):
            lines.append("## Bottlenecks")
            lines.append("")
            for bottleneck in analytics_result["bottlenecks"]:
                lines.append(f"### {bottleneck.get('description')}")
                lines.append(f"- **Type**: {bottleneck.get('type')}")
                lines.append(f"- **Severity**: {bottleneck.get('severity')}")
                lines.append("")

        # Recommendations
        if analytics_result.get("recommendations"):
            lines.append("## Recommendations")
            lines.append("")
            for i, rec in enumerate(analytics_result["recommendations"], 1):
                lines.append(f"### {i}. {rec.get('title')} [{rec.get('priority').upper()}]")
                lines.append(f"{rec.get('description')}")
                lines.append(f"- **Category**: {rec.get('category')}")
                lines.append(f"- **Impact**: {rec.get('impact')}")
                lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"*Generated by {self.agent_id}*")

        return "\n".join(lines)

    def get_system_prompt(self) -> str:
        """Get system prompt for the Analytics Agent."""
        return f"""You are {self.agent_id}, an Analytics Agent in the Universal AI Development Platform.

Your role is to analyze patterns, identify trends, and generate strategic insights for continuous improvement.

**Responsibilities:**
1. Analyze patterns across all agent activities
2. Identify performance trends
3. Detect bottlenecks and inefficiencies
4. Recommend process optimizations
5. Identify learning opportunities
6. Extract success patterns
7. Analyze failure patterns
8. Generate strategic insights

**Analytics Process:**
1. Gather comprehensive data from all sources
2. Analyze agent performance trends
3. Identify task completion patterns
4. Detect bottlenecks in the workflow
5. Extract success patterns from agent memories
6. Analyze failure patterns for root causes
7. Generate actionable optimization recommendations
8. Create comprehensive insights report
9. Update task with key findings

**Analysis Types:**
- Agent Performance: Success rates, task completion, efficiency
- Task Patterns: Common task types, completion trends
- Bottleneck Detection: Blocked tasks, high WIP, stuck progress
- Success Patterns: What works well, best practices
- Failure Analysis: Common failures, root causes
- Optimization Opportunities: Process improvements, resource allocation

**Key Metrics:**
- Task completion rate
- Agent success rate
- Bottleneck severity
- Pattern frequency
- Trend direction and magnitude
- Recommendation impact

**Tools Available:**
- EnhancedChecklistManager: Task data
- ProjectRegistry: Project information
- TaskQueue: Queue statistics
- AgentMemory: All agent memories for pattern analysis
- MessageBus: Communication logs

Learn from data to help the entire system continuously improve and become more efficient."""

    def extract_patterns(self, result: Dict) -> List[str]:
        """
        Extract learnable patterns from analytics results.

        Args:
            result: Task execution result

        Returns:
            List of pattern descriptions
        """
        patterns = []

        if not result.get("success"):
            return patterns

        data = result.get("data", {})
        analytics_result = data.get("analytics_result", {})

        # Pattern: Insights identified
        insights_count = len(analytics_result.get("insights", []))
        if insights_count > 0:
            patterns.append(f"Analytics insights: {insights_count}")

        # Pattern: Patterns found
        patterns_count = len(analytics_result.get("patterns_identified", []))
        if patterns_count > 0:
            patterns.append(f"Patterns identified: {patterns_count}")

        # Pattern: Bottlenecks detected
        bottlenecks_count = len(analytics_result.get("bottlenecks", []))
        if bottlenecks_count > 0:
            patterns.append(f"Bottlenecks detected: {bottlenecks_count}")

        # Pattern: Recommendations generated
        recs_count = len(analytics_result.get("recommendations", []))
        if recs_count > 0:
            patterns.append(f"Recommendations: {recs_count}")

        return patterns


# Example usage
async def example_usage():
    """Example of using the AnalyticsAgent."""
    from core.message_bus import MessageBus
    from pathlib import Path

    config = {
        "memory_dir": Path("./AGENT_MEMORY"),
        "projects_base_path": Path("./projects"),
        "lookback_days": 30,
        "min_pattern_frequency": 3
    }

    message_bus = MessageBus()

    agent = AnalyticsAgent(
        agent_id="analytics-001",
        config=config,
        message_bus=message_bus,
        claude_client=None  # Would be actual client in production
    )

    await agent.initialize()

    # Example task
    task = {
        "task_id": "queue-task-123",
        "project_id": "my-project",
        "checklist_task_id": 25,
        "type": "analytics",
        "metadata": {
            "description": "Analyze project patterns and generate insights"
        }
    }

    result = await agent.run_task(task)
    print(f"Analytics result: {result}")

    await agent.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

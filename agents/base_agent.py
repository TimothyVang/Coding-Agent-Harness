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
import json
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

    def print_status(self, message: str):
        """
        Print status message with agent ID prefix.

        Args:
            message: Status message to print
        """
        print(f"[{self.agent_id}] {message}")

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

    async def _query_context7(self, library_name: str, query: str) -> str:
        """
        Query Context7 for library documentation and best practices.

        This helper method enables agents to research libraries and patterns
        before implementation. Results are cached in agent memory.

        Args:
            library_name: Name of the library/framework to research
            query: Specific question or topic to research

        Returns:
            Formatted documentation string from Context7

        Note:
            Requires Context7 MCP server to be configured and CONTEXT7_API_KEY set
        """
        # Check if Context7 results are cached in memory
        cache_key = f"context7_{library_name}_{query[:50]}"
        cached = self.memory.data.get("context7_cache", {}).get(cache_key)

        if cached:
            print(f"[{self.agent_id}] Using cached Context7 result for {library_name}")
            return cached

        try:
            # Context7 MCP tools should be available through self.client
            # This is a placeholder for the actual MCP integration
            # In practice, the agent will use Context7 MCP tools directly

            # For now, we'll add a TODO marker for actual implementation
            result = f"""
# Context7 Research: {library_name}

Query: {query}

Note: Context7 integration pending. Agent should use Context7 MCP tools:
1. mcp__context7__resolve-library-id - to get library ID
2. mcp__context7__query-docs - to query documentation

This will be implemented when Claude client is available with MCP tools.
"""

            # Cache the result
            if "context7_cache" not in self.memory.data:
                self.memory.data["context7_cache"] = {}
            self.memory.data["context7_cache"][cache_key] = result
            self.memory.save()

            return result

        except Exception as e:
            print(f"[{self.agent_id}] Context7 query failed: {e}")
            return f"Context7 unavailable. Error: {e}"

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

    async def _analyze_codebase(self, project_path: Path) -> Dict:
        """
        Analyze codebase structure, patterns, and metrics.

        This helper method provides comprehensive codebase analysis for agents
        that need to understand code structure (RefactorAgent, DatabaseAgent, etc.)

        Args:
            project_path: Path to project directory

        Returns:
            Dict containing codebase analysis:
            - language: Primary language
            - framework: Detected framework
            - file_count: Total files analyzed
            - lines_of_code: Total LOC
            - complexity_score: Average complexity
            - patterns: Detected patterns
            - structure: Directory structure summary
        """
        analysis = {
            "language": "unknown",
            "framework": "unknown",
            "file_count": 0,
            "lines_of_code": 0,
            "complexity_score": 0.0,
            "patterns": [],
            "structure": {},
            "dependencies": []
        }

        try:
            # Detect language and framework
            if (project_path / "package.json").exists():
                analysis["language"] = "javascript/typescript"
                import json
                try:
                    pkg_data = json.loads((project_path / "package.json").read_text(encoding='utf-8'))
                    deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
                    analysis["dependencies"] = list(deps.keys())

                    if "react" in deps:
                        analysis["framework"] = "react"
                    elif "vue" in deps:
                        analysis["framework"] = "vue"
                    elif "next" in deps:
                        analysis["framework"] = "nextjs"
                    elif "express" in deps:
                        analysis["framework"] = "express"
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"[{self.agent_id}] Warning: Error parsing package.json: {e}")

            elif (project_path / "requirements.txt").exists() or (project_path / "pyproject.toml").exists():
                analysis["language"] = "python"

                if (project_path / "requirements.txt").exists():
                    req_content = (project_path / "requirements.txt").read_text(encoding='utf-8')
                    analysis["dependencies"] = [line.split('==')[0].split('>=')[0].strip()
                                               for line in req_content.split('\n') if line.strip()]

                    if "django" in req_content.lower():
                        analysis["framework"] = "django"
                    elif "flask" in req_content.lower():
                        analysis["framework"] = "flask"
                    elif "fastapi" in req_content.lower():
                        analysis["framework"] = "fastapi"

            elif (project_path / "go.mod").exists():
                analysis["language"] = "go"

            # Count files and lines of code
            code_extensions = {
                '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.cpp', '.c',
                '.rb', '.php', '.rs', '.swift', '.kt', '.scala'
            }

            total_lines = 0
            file_count = 0

            for ext in code_extensions:
                files = list(project_path.rglob(f"*{ext}"))
                file_count += len(files)

                for file_path in files[:100]:  # Limit to 100 files for performance
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        total_lines += len(lines)
                    except (IOError, OSError, UnicodeDecodeError) as e:
                        print(f"[{self.agent_id}] Warning: Error reading {file_path}: {e}")

            analysis["file_count"] = file_count
            analysis["lines_of_code"] = total_lines

            # Basic complexity estimation (lines per file)
            if file_count > 0:
                analysis["complexity_score"] = total_lines / file_count

            # Analyze directory structure
            structure = {}
            for item in project_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    structure[item.name] = len(list(item.rglob('*')))

            analysis["structure"] = structure

        except Exception as e:
            print(f"[{self.agent_id}] Error analyzing codebase: {e}")
            analysis["error"] = str(e)

        return analysis

    async def _detect_patterns(self, code: str, language: str = "python") -> list[Dict]:
        """
        Detect code patterns and anti-patterns in code snippet.

        Useful for RefactorAgent, ReviewerAgent, and code quality analysis.

        Args:
            code: Code snippet to analyze
            language: Programming language (python, javascript, etc.)

        Returns:
            List of detected patterns, each containing:
            - type: 'pattern' or 'anti-pattern'
            - name: Pattern name
            - description: What was detected
            - severity: LOW, MEDIUM, HIGH
            - line: Line number if applicable
        """
        patterns = []
        lines = code.split('\n')

        try:
            if language.lower() in ["python", "py"]:
                # Python-specific pattern detection

                # Long functions (more than 50 lines)
                if len(lines) > 50:
                    patterns.append({
                        "type": "anti-pattern",
                        "name": "Long Function",
                        "description": f"Function has {len(lines)} lines. Consider breaking into smaller functions.",
                        "severity": "MEDIUM",
                        "line": 1
                    })

                # Nested loops (potential O(n²) complexity)
                for i, line in enumerate(lines, 1):
                    if 'for ' in line or 'while ' in line:
                        indent = len(line) - len(line.lstrip())
                        # Check if there's another loop within next lines with higher indent
                        for j in range(i, min(i + 20, len(lines))):
                            next_line = lines[j]
                            next_indent = len(next_line) - len(next_line.lstrip())
                            if next_indent > indent and ('for ' in next_line or 'while ' in next_line):
                                patterns.append({
                                    "type": "anti-pattern",
                                    "name": "Nested Loop",
                                    "description": "Nested loops detected. Consider optimization.",
                                    "severity": "MEDIUM",
                                    "line": i
                                })
                                break

                # Multiple return statements
                return_count = sum(1 for line in lines if 'return ' in line)
                if return_count > 5:
                    patterns.append({
                        "type": "anti-pattern",
                        "name": "Multiple Returns",
                        "description": f"{return_count} return statements. Consider simplifying logic.",
                        "severity": "LOW",
                        "line": 0
                    })

                # TODO/FIXME comments
                for i, line in enumerate(lines, 1):
                    if 'TODO' in line or 'FIXME' in line:
                        patterns.append({
                            "type": "anti-pattern",
                            "name": "Technical Debt",
                            "description": "TODO/FIXME comment found.",
                            "severity": "LOW",
                            "line": i
                        })

            elif language.lower() in ["javascript", "js", "typescript", "ts"]:
                # JavaScript-specific patterns

                # Console.log in production code
                for i, line in enumerate(lines, 1):
                    if 'console.log' in line and 'debug' not in line.lower():
                        patterns.append({
                            "type": "anti-pattern",
                            "name": "Debug Statement",
                            "description": "console.log found. Remove before production.",
                            "severity": "LOW",
                            "line": i
                        })

                # Callback hell (more than 3 nested callbacks)
                max_indent = max((len(line) - len(line.lstrip())) // 2 for line in lines if line.strip())
                if max_indent > 6:
                    patterns.append({
                        "type": "anti-pattern",
                        "name": "Deep Nesting",
                        "description": f"Deep nesting detected (level {max_indent}). Consider async/await.",
                        "severity": "HIGH",
                        "line": 0
                    })

        except Exception as e:
            print(f"[{self.agent_id}] Error detecting patterns: {e}")

        return patterns

    async def _generate_recommendations(self, issues: list[Dict], context: Dict = None) -> list[Dict]:
        """
        Generate prioritized recommendations from detected issues.

        Takes a list of issues (from security scans, code analysis, etc.) and
        generates actionable, prioritized recommendations.

        Args:
            issues: List of issues, each containing severity, type, description
            context: Optional context about the codebase/project

        Returns:
            List of recommendations, each containing:
            - priority: HIGH, MEDIUM, LOW
            - category: security, performance, quality, etc.
            - title: Short recommendation title
            - description: Detailed recommendation
            - impact: Expected impact if implemented
            - effort: Estimated effort (hours)
        """
        recommendations = []

        try:
            # Group issues by severity and category
            high_severity = [i for i in issues if i.get('severity') == 'HIGH' or i.get('severity') == 'CRITICAL']
            medium_severity = [i for i in issues if i.get('severity') == 'MEDIUM']
            low_severity = [i for i in issues if i.get('severity') == 'LOW']

            # Generate recommendations for high severity issues first
            for issue in high_severity[:5]:  # Top 5 high severity
                recommendations.append({
                    "priority": "HIGH",
                    "category": issue.get('type', 'quality'),
                    "title": f"Fix: {issue.get('name', issue.get('title', 'Critical Issue'))}",
                    "description": issue.get('description', issue.get('message', '')),
                    "impact": "Prevents potential production issues",
                    "effort": 2  # hours
                })

            # Group medium severity by category
            security_issues = [i for i in medium_severity if 'security' in i.get('type', '').lower()]
            performance_issues = [i for i in medium_severity if 'performance' in i.get('type', '').lower()]

            if security_issues:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "security",
                    "title": f"Address {len(security_issues)} Security Issues",
                    "description": "Multiple security vulnerabilities detected. Review and patch.",
                    "impact": "Improves application security posture",
                    "effort": len(security_issues) * 0.5
                })

            if performance_issues:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "performance",
                    "title": f"Optimize {len(performance_issues)} Performance Bottlenecks",
                    "description": "Code optimization opportunities identified.",
                    "impact": "Improves application performance",
                    "effort": len(performance_issues) * 1
                })

            # Low priority cleanup
            if low_severity:
                recommendations.append({
                    "priority": "LOW",
                    "category": "quality",
                    "title": "Code Quality Improvements",
                    "description": f"{len(low_severity)} minor code quality issues. Good for tech debt sprint.",
                    "impact": "Improves code maintainability",
                    "effort": len(low_severity) * 0.25
                })

            # Sort by priority
            priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            recommendations.sort(key=lambda x: priority_order[x["priority"]])

        except Exception as e:
            print(f"[{self.agent_id}] Error generating recommendations: {e}")

        return recommendations

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id} type={self.agent_type} status={self.status}>"

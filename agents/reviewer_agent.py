"""
Reviewer Agent
==============

Code review agent that analyzes code quality, security, performance, and best practices.

Responsibilities:
- Code quality review (readability, maintainability, testability)
- Security vulnerability detection
- Performance issue identification
- Best practice validation
- Architectural consistency checks
- Providing actionable feedback
- Learning from review patterns
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_agent import BaseAgent
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus, MessageTypes
from core.agent_memory import AgentMemory


class ReviewerAgent(BaseAgent):
    """
    Reviewer Agent - Code Review and Quality Assessment

    Responsibilities:
    - Code review and quality checks
    - Best practice validation
    - Security vulnerability detection
    - Performance issue identification
    - Maintainability assessment
    - Providing actionable feedback

    This agent learns review patterns and improves over time.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[Any] = None  # ClaudeSDKClient type
    ):
        """
        Initialize ReviewerAgent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="reviewer",
            config=config,
            message_bus=message_bus
        )
        self.client = claude_client

        # Reviewer-specific configuration
        self.review_categories = config.get("review_categories", [
            "code_quality",
            "best_practices",
            "security",
            "performance",
            "maintainability",
            "documentation"
        ])

        self.severity_levels = config.get("severity_levels", ["critical", "high", "medium", "low", "info"])
        self.auto_approve_threshold = config.get("auto_approve_threshold", 95.0)  # % score
        self.create_blocking_for_critical = config.get("blocking_on_critical_issues", True)

        # Review checks configuration
        self.check_code_quality = config.get("check_code_quality", True)
        self.check_best_practices = config.get("check_best_practices", True)
        self.check_security = config.get("check_security", True)
        self.check_performance = config.get("check_performance", True)

        print(f"[ReviewerAgent] Initialized with ID: {self.agent_id}")
        print(f"  - Review categories: code_quality, security, performance, maintainability")
        print(f"  - Auto-approve threshold: {self.config.get('auto_approve_threshold', 90)}%")

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a code review task.

        Process:
        1. Load task details from checklist
        2. Identify changed files
        3. Review code quality (readability, maintainability)
        4. Check for security issues
        5. Verify best practices
        6. Check test coverage
        7. Generate review report
        8. Create subtasks for critical issues
        9. Update checklist with review results

        Args:
            task: Task dict from queue with project_id, checklist_task_id

        Returns:
            Dict with success status and review results
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
            self.print_status(f"Reviewing: {task_title}")

            # Review process
            review_result = {
                "task_id": checklist_task_id,
                "review_date": datetime.now().isoformat(),
                "issues_found": [],
                "suggestions": [],
                "quality_score": 0,
                "review_passed": False
            }

            # Step 1: Load patterns from memory
            self.memory.load_patterns()

            # Step 2: Load files to review
            files_info = await self._load_task_code(project_path, task_details)

            # Step 3: Check code quality
            if self.check_code_quality:
                quality_checks = await self._check_code_quality(task_details)
                review_result["quality_checks"] = quality_checks
                if quality_checks.get("readability", {}).get("issues"):
                    review_result["issues_found"].extend(quality_checks["readability"]["issues"])

            # Step 4: Check best practices
            if self.check_best_practices:
                best_practices = await self._check_best_practices(task_details)
                review_result["best_practices"] = best_practices
                if best_practices.get("violations"):
                    review_result["issues_found"].extend(best_practices["violations"])

            # Step 5: Check security issues
            if self.check_security:
                security_checks = await self._check_security(task_details)
                review_result["security_checks"] = security_checks
                if security_checks.get("vulnerabilities"):
                    review_result["issues_found"].extend(security_checks["vulnerabilities"])

            # Step 6: Check performance
            if self.check_performance:
                performance_checks = await self._check_performance(task_details)
                review_result["performance_checks"] = performance_checks
                if performance_checks.get("issues"):
                    review_result["issues_found"].extend(performance_checks["issues"])

            # Step 7: Calculate quality score
            quality_score = self._calculate_quality_score(review_result)
            review_result["quality_score"] = quality_score
            review_result["review_passed"] = quality_score >= self.auto_approve_threshold

            # Step 8: Generate review report
            review_report = await self._create_review_report(
                task_details=task_details,
                review_result=review_result,
                quality_checks=review_result.get("quality_checks", {}),
                best_practices=review_result.get("best_practices", {}),
                security_checks=review_result.get("security_checks", {}),
                performance_checks=review_result.get("performance_checks", {})
            )

            # Step 9: Update checklist with review results
            if self.client:
                approval_status = "APPROVED" if review_result["review_passed"] else "NEEDS CHANGES"
                checklist.add_note(
                    checklist_task_id,
                    f"Code review completed: {approval_status} (Score: {quality_score:.1f}/100)"
                )

                # Create blocking subtasks for critical issues
                critical_issues = [
                    issue for issue in review_result["issues_found"]
                    if issue.get("severity") == "critical"
                ]

                if critical_issues and self.create_blocking_for_critical:
                    for issue in critical_issues:
                        subtask_id = checklist.add_subtask(checklist_task_id, {
                            "title": f"Fix critical issue: {issue.get('description', 'Unknown')}",
                            "description": issue.get("details", ""),
                            "category": "bugfix",
                            "priority": "critical",
                            "blocking": True
                        })
                        print(f"[Reviewer] Created blocking subtask {subtask_id} for critical issue")

            return {
                "success": True,
                "data": {
                    "review_result": review_result,
                    "review_report": review_report,
                    "files_reviewed": files_info.get("files", []),
                    "total_lines_reviewed": files_info.get("total_lines", 0),
                    "quality_score": quality_score,
                    "approval_status": "approved" if review_result["review_passed"] else "needs_changes",
                    "critical_issues": len([
                        i for i in review_result["issues_found"]
                        if i.get("severity") == "critical"
                    ])
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Review task execution failed: {str(e)}"
            }

    def _calculate_quality_score(self, review_result: Dict) -> float:
        """Calculate overall quality score from review results."""
        # Simple scoring: start at 100, deduct for issues
        score = 100.0

        for issue in review_result.get("issues_found", []):
            severity = issue.get("severity", "medium")
            if severity == "critical":
                score -= 20
            elif severity == "high":
                score -= 10
            elif severity == "medium":
                score -= 5
            elif severity == "low":
                score -= 2

        return max(0.0, score)

    async def _load_task_code(self, project_path: Path, task_details: Dict) -> Dict:
        """Load code files related to the task."""
        # Get relevant files from task metadata or recent project changes
        files_reviewed = []

        # Check if task has file paths specified
        if "files" in task_details:
            for file_path in task_details.get("files", []):
                if Path(file_path).exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            files_reviewed.append({
                                "path": str(file_path),
                                "lines": len(content.split('\n')),
                                "size": len(content)
                            })
                    except Exception as e:
                        print(f"[Reviewer] Error reading {file_path}: {e}")

        return {"files": files_reviewed, "total_lines": sum(f["lines"] for f in files_reviewed)}

    async def _perform_code_review(self, task_details: Dict, files_info: Dict) -> Dict:
        """
        Perform comprehensive code review.

        Checks:
        - Code quality (readability, maintainability, complexity)
        - Best practices adherence
        - Security vulnerabilities
        - Performance issues
        - Test coverage adequacy
        - Documentation completeness
        """
        print(f"[Reviewer] Performing code review...")

        issues = []
        suggestions = []

        # TODO: With Claude client, perform actual review
        # For now, create structure for review results

        review_result = {
            "issues": issues,
            "suggestions": suggestions,
            "security_concerns": [],
            "performance_issues": [],
            "quality_score": 0.0,  # 0-100
            "approval_status": "pending"  # pending, approved, needs_changes, rejected
        }

        return review_result

    async def _check_code_quality(self, task_details: Dict) -> Dict:
        """
        Check code quality metrics.

        Metrics:
        - Readability (clear names, appropriate complexity)
        - Maintainability (modularity, documentation)
        - Testability (unit test coverage, test quality)
        - Consistency (follows project conventions)
        """
        quality_checks = {
            "readability": {"score": 0.0, "issues": []},
            "maintainability": {"score": 0.0, "issues": []},
            "testability": {"score": 0.0, "issues": []},
            "consistency": {"score": 0.0, "issues": []}
        }

        # TODO: Implement actual quality checks
        # - Complexity analysis
        # - Naming conventions
        # - Code duplication detection
        # - Comment coverage

        return quality_checks

    async def _check_best_practices(self, task_details: Dict) -> Dict:
        """
        Check adherence to best practices.

        Uses:
        - Agent memory for learned patterns
        - Context7 for framework-specific best practices
        """
        best_practice_results = {
            "violations": [],
            "recommendations": [],
            "patterns_followed": []
        }

        # Check memory for successful patterns
        title = task_details.get("title", "")
        category = task_details.get("category", "feature")

        patterns = self.memory.find_similar_patterns(f"review {title} {category}")
        if patterns:
            print(f"[Reviewer] Found {len(patterns)} similar review patterns in memory")
            # Use patterns to guide review

        # TODO: If Context7 client available, research best practices for the specific technology

        return best_practice_results

    async def _check_security(self, task_details: Dict) -> Dict:
        """
        Check for security vulnerabilities.

        Security checks:
        - Input validation
        - SQL injection
        - XSS vulnerabilities
        - Authentication/authorization issues
        - Sensitive data exposure
        - Dependency vulnerabilities
        """
        security_results = {
            "vulnerabilities": [],
            "severity_high": 0,
            "severity_medium": 0,
            "severity_low": 0,
            "recommendations": []
        }

        # TODO: Implement security scanning
        # - Static analysis
        # - Dependency audit
        # - Common vulnerability patterns

        return security_results

    async def _check_performance(self, task_details: Dict) -> Dict:
        """
        Check for performance issues.

        Performance checks:
        - Algorithmic complexity
        - Database query optimization
        - Memory usage
        - Network efficiency
        - Caching opportunities
        """
        performance_results = {
            "issues": [],
            "optimizations": [],
            "bottlenecks": []
        }

        # TODO: Implement performance analysis
        # - Complexity detection (O(n²) loops, etc.)
        # - N+1 query detection
        # - Large object allocations

        return performance_results

    async def _create_review_report(
        self,
        task_details: Dict,
        review_result: Dict,
        quality_checks: Dict,
        best_practices: Dict,
        security_checks: Dict,
        performance_checks: Dict
    ) -> str:
        """Create comprehensive review report."""
        report_lines = []

        report_lines.append("# Code Review Report")
        report_lines.append("")
        report_lines.append(f"**Task**: {task_details.get('title', 'N/A')}")
        report_lines.append(f"**Reviewer**: {self.agent_id}")
        report_lines.append(f"**Date**: {datetime.now().isoformat()}")
        report_lines.append("")

        # Overall assessment
        report_lines.append("## Overall Assessment")
        report_lines.append("")
        quality_score = review_result.get("quality_score", 0.0)
        approval_status = "APPROVED" if review_result.get("review_passed") else "NEEDS CHANGES"
        report_lines.append(f"**Approval Status**: {approval_status}")
        report_lines.append(f"**Quality Score**: {quality_score:.1f}/100")
        report_lines.append("")

        # Issues
        if review_result.get("issues_found"):
            report_lines.append("## Issues Found")
            report_lines.append("")
            for i, issue in enumerate(review_result["issues_found"], 1):
                report_lines.append(f"{i}. **{issue.get('type', 'Issue')}**: {issue.get('description', '')}")
                report_lines.append(f"   - Severity: {issue.get('severity', 'medium')}")
                report_lines.append(f"   - Location: {issue.get('location', 'N/A')}")
                report_lines.append("")

        # Suggestions
        if review_result.get("suggestions"):
            report_lines.append("## Suggestions")
            report_lines.append("")
            for i, suggestion in enumerate(review_result["suggestions"], 1):
                report_lines.append(f"{i}. {suggestion}")
                report_lines.append("")

        # Security
        if security_checks.get("vulnerabilities"):
            report_lines.append("## Security Concerns")
            report_lines.append("")
            report_lines.append(f"- High Severity: {security_checks.get('severity_high', 0)}")
            report_lines.append(f"- Medium Severity: {security_checks.get('severity_medium', 0)}")
            report_lines.append(f"- Low Severity: {security_checks.get('severity_low', 0)}")
            report_lines.append("")

        # Performance
        if performance_checks.get("issues"):
            report_lines.append("## Performance Issues")
            report_lines.append("")
            for issue in performance_checks["issues"]:
                report_lines.append(f"- {issue}")
                report_lines.append("")

        # Best practices
        if best_practices.get("violations"):
            report_lines.append("## Best Practice Violations")
            report_lines.append("")
            for violation in best_practices["violations"]:
                report_lines.append(f"- {violation}")
                report_lines.append("")

        report_lines.append("---")
        report_lines.append("")
        report_lines.append(f"*Generated by {self.agent_id} at {datetime.now().isoformat()}*")

        return "\n".join(report_lines)

    def get_system_prompt(self) -> str:
        """Get system prompt for the Reviewer Agent."""
        return f"""You are {self.agent_id}, a Reviewer Agent in the Universal AI Development Platform.

Your role is to perform comprehensive code reviews to ensure quality, security, and maintainability.

**Responsibilities:**
1. Review code for quality, readability, and maintainability
2. Check adherence to best practices and project conventions
3. Identify security vulnerabilities and potential exploits
4. Detect performance issues and optimization opportunities
5. Verify test coverage adequacy
6. Provide constructive feedback and actionable suggestions
7. Create detailed review reports
8. Learn from review patterns to improve future reviews

**Review Process:**
1. Identify all files changed in the task
2. Perform comprehensive code review
3. Check code quality metrics (readability, maintainability, testability)
4. Verify best practices adherence
5. Scan for security vulnerabilities
6. Check for performance issues
7. Generate detailed review report
8. Update task with review results
9. Create blocking subtasks for critical issues

**Quality Criteria:**
- Readability: Clear variable names, appropriate complexity
- Maintainability: Modular design, proper documentation
- Security: No vulnerabilities, proper validation
- Performance: Efficient algorithms, optimized queries
- Testing: Adequate coverage, quality tests
- Consistency: Follows project conventions

**Approval Guidelines:**
- Approved: No critical issues, high quality
- Needs Changes: Has issues that must be addressed
- Rejected: Critical security/quality issues

**Tools Available:**
- EnhancedChecklistManager: Task and subtask management
- AgentMemory: Learn from past reviews
- Context7: Research best practices
- MessageBus: Communicate with other agents

Learn from each review to improve future reviews. Extract patterns from successful reviews."""

    def extract_patterns(self, result: Dict) -> List[str]:
        """
        Extract learnable patterns from review results.

        Args:
            result: Task execution result

        Returns:
            List of pattern descriptions
        """
        patterns = []

        if not result.get("success"):
            return patterns

        data = result.get("data", {})
        review_result = data.get("review_result", {})

        # Pattern: Successful review
        quality_score = review_result.get("quality_score", 0.0)
        if quality_score >= 80.0:
            patterns.append(f"High-quality code review (score: {quality_score:.1f})")

        # Pattern: Common issues found
        issues = review_result.get("issues", [])
        if issues:
            issue_types = set(issue.get("type") for issue in issues)
            patterns.append(f"Common issues: {', '.join(issue_types)}")

        # Pattern: Security findings
        security = data.get("security_checks", {})
        if security.get("vulnerabilities"):
            patterns.append(f"Security vulnerabilities detected: {len(security['vulnerabilities'])}")

        # Pattern: Approval decision
        approval = review_result.get("approval_status")
        if approval:
            patterns.append(f"Review approval: {approval}")

        return patterns


# Example usage
async def example_usage():
    """Example of using the ReviewerAgent."""
    from core.message_bus import MessageBus
    from pathlib import Path

    config = {
        "memory_dir": Path("./AGENT_MEMORY"),
        "projects_base_path": Path("./projects"),
        "check_code_quality": True,
        "check_security": True,
        "check_performance": True,
        "min_quality_score": 70.0,
        "block_on_security_issues": True
    }

    message_bus = MessageBus()

    agent = ReviewerAgent(
        agent_id="reviewer-001",
        config=config,
        message_bus=message_bus,
        claude_client=None  # Would be actual client in production
    )

    await agent.initialize()

    # Example task
    task = {
        "task_id": "queue-task-123",
        "project_id": "my-project",
        "checklist_task_id": 5,
        "type": "review",
        "metadata": {
            "description": "Review authentication implementation"
        }
    }

    result = await agent.run_task(task)
    print(f"Review result: {result}")

    await agent.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

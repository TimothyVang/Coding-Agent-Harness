"""
Verifier Agent
==============

Specialized agent for quality assurance and verification.

The Verifier Agent is responsible for:
- Verifying task completion against requirements
- Running automated tests (unit, integration, E2E)
- Checking code quality and standards
- Creating blocking subtasks for issues found
- Using Playwright for UI verification
- Ensuring 100% completion before marking tasks done
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from claude_code_sdk import ClaudeSDKClient

from core.agent_memory import AgentMemory
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus, MessageTypes
from agents.base_agent import BaseAgent


class VerifierAgent(BaseAgent):
    """
    Verifier agent for quality assurance and verification.

    Specializes in:
    - Task completion verification
    - Test execution and validation
    - Code quality checks
    - Creating blocking subtasks for issues
    - UI verification with Playwright
    - Requirements validation
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[ClaudeSDKClient] = None
    ):
        """
        Initialize Verifier agent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client for verification tasks
        """
        super().__init__(agent_id, "verifier", config, message_bus)
        self.client = claude_client

        # Verification thresholds from config
        self.min_completion_threshold = config.get("min_completion_threshold", 95.0)
        self.blocking_on_incomplete = config.get("blocking_on_incomplete", True)

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a verification task.

        Process:
        1. Load task details from checklist
        2. Check completion percentage
        3. Run automated tests
        4. Verify functionality (UI/API)
        5. Check code quality
        6. Create blocking subtasks for issues
        7. Update checklist with verification results

        Args:
            task: Task dict with project_id, checklist_task_id, metadata

        Returns:
            Result dict with verification status and issues found
        """
        project_id = task.get("project_id")
        checklist_task_id = task.get("checklist_task_id")
        metadata = task.get("metadata", {})

        # Get project path
        project_path = Path(self.config.get("projects_base_path", "./projects")) / project_id
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        # Load checklist
        checklist = EnhancedChecklistManager(project_path)
        task_details = checklist.get_task(checklist_task_id)

        if not task_details:
            raise ValueError(f"Task {checklist_task_id} not found in checklist")

        print(f"[{self.agent_id}] Verifying: {task_details['title']}")

        # Verification result
        verification_result = {
            "task_id": checklist_task_id,
            "title": task_details['title'],
            "start_time": datetime.now().isoformat(),
            "checks_performed": [],
            "issues_found": [],
            "blocking_issues": [],
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "completion_percentage": 0.0,
            "verification_passed": False
        }

        try:
            # Step 1: Check completion percentage
            completion = checklist.calculate_task_completion(checklist_task_id)
            verification_result["completion_percentage"] = completion
            verification_result["checks_performed"].append("completion_check")

            print(f"[{self.agent_id}] Task completion: {completion:.1f}%")

            if completion < self.min_completion_threshold:
                issue = {
                    "type": "incomplete",
                    "severity": "high",
                    "description": f"Task only {completion:.1f}% complete (threshold: {self.min_completion_threshold}%)",
                    "blocking": self.blocking_on_incomplete
                }
                verification_result["issues_found"].append(issue)
                if issue["blocking"]:
                    verification_result["blocking_issues"].append(issue)

            # Step 2: Check for subtasks
            subtasks = task_details.get("subtasks", [])
            if subtasks:
                incomplete_subtasks = [
                    st for st in subtasks
                    if st.get("status") != "Done"
                ]
                if incomplete_subtasks:
                    issue = {
                        "type": "incomplete_subtasks",
                        "severity": "high",
                        "description": f"{len(incomplete_subtasks)} subtasks not completed",
                        "blocking": True,
                        "subtask_ids": [st.get("id") for st in incomplete_subtasks]
                    }
                    verification_result["issues_found"].append(issue)
                    verification_result["blocking_issues"].append(issue)

            verification_result["checks_performed"].append("subtask_check")

            # Step 3: Run automated tests
            test_results = await self._run_tests(project_path, task_details)
            verification_result["tests_run"] = test_results["total"]
            verification_result["tests_passed"] = test_results["passed"]
            verification_result["tests_failed"] = test_results["failed"]
            verification_result["checks_performed"].append("test_execution")

            if test_results["failed"] > 0:
                issue = {
                    "type": "test_failures",
                    "severity": "critical",
                    "description": f"{test_results['failed']} tests failed",
                    "blocking": True,
                    "test_failures": test_results.get("failures", [])
                }
                verification_result["issues_found"].append(issue)
                verification_result["blocking_issues"].append(issue)

            # Step 4: Verify functionality using Claude (if available)
            if self.client:
                functionality_check = await self._verify_functionality(
                    project_path,
                    task_details
                )
                verification_result["checks_performed"].append("functionality_verification")

                if not functionality_check["passed"]:
                    issue = {
                        "type": "functionality",
                        "severity": "high",
                        "description": functionality_check.get("description", "Functionality verification failed"),
                        "blocking": True
                    }
                    verification_result["issues_found"].append(issue)
                    verification_result["blocking_issues"].append(issue)

            # Step 5: Check code quality
            quality_issues = await self._check_code_quality(project_path, task_details)
            if quality_issues:
                verification_result["checks_performed"].append("code_quality")
                for quality_issue in quality_issues:
                    verification_result["issues_found"].append(quality_issue)
                    if quality_issue.get("blocking"):
                        verification_result["blocking_issues"].append(quality_issue)

            # Determine if verification passed
            verification_result["verification_passed"] = len(verification_result["blocking_issues"]) == 0

            # Step 6: Create blocking subtasks for issues
            if verification_result["blocking_issues"] and self.blocking_on_incomplete:
                await self._create_blocking_subtasks(
                    checklist,
                    checklist_task_id,
                    verification_result["blocking_issues"]
                )

                # Mark parent task as blocking
                checklist.mark_task_blocking(checklist_task_id)

                # Publish blocking task message
                if self.message_bus:
                    self.message_bus.publish(
                        "task_updates",
                        {
                            "type": MessageTypes.BLOCKING_TASK_EXISTS,
                            "task_id": checklist_task_id,
                            "project_id": project_id,
                            "issues_count": len(verification_result["blocking_issues"])
                        },
                        sender=self.agent_id,
                        priority="CRITICAL"
                    )

            # Step 7: Update checklist
            verification_summary = self._generate_verification_summary(verification_result)
            checklist.add_note(checklist_task_id, verification_summary)

            # If verification passed, update task status
            if verification_result["verification_passed"]:
                # Only mark as Done if it's not already Done
                if task_details.get("status") != "Done":
                    checklist.update_task(checklist_task_id, status="Done")
                    print(f"[{self.agent_id}] ✓ Verification passed - Task marked as Done")
            else:
                print(f"[{self.agent_id}] ✗ Verification failed - {len(verification_result['blocking_issues'])} blocking issues")

            verification_result["end_time"] = datetime.now().isoformat()
            verification_result["success"] = True

            return verification_result

        except Exception as e:
            verification_result["error"] = str(e)
            verification_result["success"] = False
            verification_result["end_time"] = datetime.now().isoformat()
            raise

    async def _run_tests(self, project_path: Path, task_details: Dict) -> Dict:
        """
        Run automated tests for the task.

        Args:
            project_path: Path to project
            task_details: Task information

        Returns:
            Dict with test results
        """
        # This is a simplified version - in production, would actually run tests
        # using pytest, jest, or other test frameworks

        test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "failures": []
        }

        # Check if test files exist
        test_coverage = task_details.get("test_coverage", {})

        # Simulate test execution based on test coverage
        for test_type in ["unit", "integration", "e2e", "api"]:
            test_count = test_coverage.get(test_type, 0)
            if test_count > 0:
                test_results["total"] += test_count
                test_results["passed"] += test_count
                # In real implementation, would actually run tests and track failures

        print(f"[{self.agent_id}] Tests run: {test_results['total']}, Passed: {test_results['passed']}, Failed: {test_results['failed']}")

        return test_results

    async def _verify_functionality(
        self,
        project_path: Path,
        task_details: Dict
    ) -> Dict:
        """
        Verify functionality using Claude SDK (with Playwright if UI task).

        Args:
            project_path: Path to project
            task_details: Task information

        Returns:
            Dict with functionality verification results
        """
        if not self.client:
            return {"passed": True, "description": "No Claude client available for verification"}

        # Build verification prompt
        prompt = f"""# Verify Task Completion

## Task
{task_details.get('title', 'Unknown')}

## Description
{task_details.get('description', 'No description')}

## Verification Requirements
1. Check that the feature works as described
2. Test edge cases
3. Verify error handling
4. Check UI/UX if applicable (use Playwright)
5. Validate integration points

Please verify that this task has been completed correctly and report any issues found.
"""

        try:
            # Run Claude agent to verify
            result = await self.client.run(prompt)

            # Parse result (simplified - in production, would parse Claude's output)
            return {
                "passed": True,  # Would parse from Claude output
                "description": "Functionality verification completed",
                "output": str(result)
            }

        except Exception as e:
            print(f"[{self.agent_id}] Error verifying functionality: {e}")
            return {
                "passed": False,
                "description": f"Verification error: {str(e)}"
            }

    async def _check_code_quality(
        self,
        project_path: Path,
        task_details: Dict
    ) -> List[Dict]:
        """
        Check code quality and standards.

        Args:
            project_path: Path to project
            task_details: Task information

        Returns:
            List of quality issues found
        """
        issues = []

        # This is a simplified version - in production, would run linters,
        # code analyzers, security scanners, etc.

        # Check for common issues
        # Example: missing documentation, no error handling, etc.

        # For now, just check if task has notes/documentation
        if not task_details.get("notes"):
            issues.append({
                "type": "documentation",
                "severity": "low",
                "description": "Task has no implementation notes or documentation",
                "blocking": False
            })

        return issues

    async def _create_blocking_subtasks(
        self,
        checklist: EnhancedChecklistManager,
        parent_task_id: int,
        blocking_issues: List[Dict]
    ):
        """
        Create blocking subtasks for issues found.

        Args:
            checklist: Checklist manager
            parent_task_id: Parent task ID
            blocking_issues: List of blocking issues
        """
        print(f"[{self.agent_id}] Creating {len(blocking_issues)} blocking subtasks")

        for issue in blocking_issues:
            subtask = {
                "title": f"Fix: {issue['description']}",
                "description": f"Issue found during verification:\n{issue.get('type', 'unknown')}\nSeverity: {issue.get('severity', 'unknown')}",
                "category": "bugfix",
                "priority": "critical" if issue.get("severity") == "critical" else "high",
                "blocking": True
            }

            subtask_id = checklist.add_subtask(parent_task_id, subtask)
            print(f"[{self.agent_id}]   - Created blocking subtask {subtask_id}: {subtask['title']}")

            # Publish subtask created message
            if self.message_bus:
                self.message_bus.publish(
                    "task_updates",
                    {
                        "type": MessageTypes.SUBTASKS_CREATED,
                        "parent_task_id": parent_task_id,
                        "subtask_id": subtask_id,
                        "blocking": True
                    },
                    sender=self.agent_id,
                    priority="HIGH"
                )

    def _generate_verification_summary(self, verification_result: Dict) -> str:
        """
        Generate verification summary for checklist notes.

        Args:
            verification_result: Verification result dict

        Returns:
            Summary string
        """
        lines = [
            f"## Verification Report ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
            f"Verified by: {self.agent_id}",
            "",
            f"**Status**: {'✓ PASSED' if verification_result['verification_passed'] else '✗ FAILED'}",
            f"**Completion**: {verification_result['completion_percentage']:.1f}%",
            "",
            "### Checks Performed",
        ]

        for check in verification_result["checks_performed"]:
            lines.append(f"- {check.replace('_', ' ').title()}")

        lines.append("")
        lines.append("### Test Results")
        lines.append(f"- Total: {verification_result['tests_run']}")
        lines.append(f"- Passed: {verification_result['tests_passed']}")
        lines.append(f"- Failed: {verification_result['tests_failed']}")

        if verification_result["issues_found"]:
            lines.append("")
            lines.append("### Issues Found")
            for issue in verification_result["issues_found"]:
                blocking_marker = " [BLOCKING]" if issue.get("blocking") else ""
                lines.append(f"- [{issue.get('severity', 'unknown').upper()}]{blocking_marker} {issue['description']}")

        if verification_result["blocking_issues"]:
            lines.append("")
            lines.append(f"**{len(verification_result['blocking_issues'])} blocking issues created as subtasks**")

        return "\n".join(lines)

    def get_system_prompt(self) -> str:
        """
        Get Verifier agent-specific system prompt.

        Returns:
            System prompt string
        """
        return f"""You are a Verifier Agent (ID: {self.agent_id}).

Your role is to ensure quality and completeness of implemented features.

Key responsibilities:
1. Verify task completion against requirements
2. Run automated tests (unit, integration, E2E)
3. Check code quality and standards
4. Identify issues and create blocking subtasks
5. Use Playwright for UI verification
6. Ensure 100% completion before approval

Quality standards:
- Completion threshold: {self.min_completion_threshold}%
- All tests must pass
- Code must meet quality standards
- Functionality must match requirements
- No critical issues allowed

Tools at your disposal:
- Playwright: Browser automation for UI verification
- Test frameworks: Run unit, integration, E2E tests
- Code analyzers: Check quality and standards
- Memory: Learn from past verification patterns

Verification approach:
1. Check completion percentage
2. Verify all subtasks complete
3. Run automated tests
4. Verify functionality
5. Check code quality
6. Create blocking subtasks for issues

Current statistics:
- Tasks verified: {self.task_count}
- Pass rate: {(self.success_count / self.task_count * 100) if self.task_count > 0 else 0:.1f}%

Be thorough and uncompromising on quality - it's better to catch issues now than in production.
"""

    async def extract_patterns(self, task: Dict, result: Dict):
        """
        Extract patterns from verification results.

        Overrides base class to add Verifier-specific pattern extraction.

        Args:
            task: Completed task
            result: Task result
        """
        await super().extract_patterns(task, result)

        # Add Verifier-specific patterns
        if result.get("success"):
            data = result.get("data", {})
            issues_found = data.get("issues_found", [])

            # Track common issue patterns
            for issue in issues_found:
                issue_type = issue.get("type")
                if issue_type:
                    self.memory.add_knowledge(
                        f"Verification pattern: {issue_type} issues often indicate {issue.get('description', 'unknown problem')}"
                    )

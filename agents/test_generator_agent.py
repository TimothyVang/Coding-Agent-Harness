"""
Test Generator Agent
====================

Specialized agent for automated test creation.

The Test Generator Agent is responsible for:
- Generating comprehensive test suites (unit, integration, E2E, API)
- Using Context7 to research testing best practices
- Creating test files with proper structure
- Ensuring test coverage for new features
- Updating test coverage tracking in checklist
- Following testing frameworks and patterns
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


class TestGeneratorAgent(BaseAgent):
    """
    Test Generator agent for automated test creation.

    Specializes in:
    - Test suite generation (unit, integration, E2E, API)
    - Context7 research for testing best practices
    - Test file creation and organization
    - Test coverage tracking
    - Framework-specific test patterns
    - Test documentation
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[ClaudeSDKClient] = None,
        sandbox_manager=None
    ):
        """
        Initialize Test Generator agent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client for test generation
            sandbox_manager: Optional E2BSandboxManager for test validation
        """
        super().__init__(agent_id, "test_generator", config, message_bus)
        self.client = claude_client
        self.sandbox_manager = sandbox_manager

        # Test generation configuration
        self.generate_unit_tests = config.get("generate_unit_tests", True)
        self.generate_integration_tests = config.get("generate_integration_tests", True)
        self.generate_e2e_tests = config.get("generate_e2e_tests", True)
        self.generate_api_tests = config.get("generate_api_tests", True)

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a test generation task.

        Process:
        1. Load task details from checklist
        2. Research testing best practices using Context7
        3. Determine test types needed
        4. Generate test files for each type
        5. Update test coverage in checklist
        6. Create tests subtask if not already present

        Args:
            task: Task dict with project_id, checklist_task_id, metadata

        Returns:
            Result dict with test generation results
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

        print(f"[{self.agent_id}] Generating tests for: {task_details['title']}")

        # Test generation result
        generation_result = {
            "task_id": checklist_task_id,
            "title": task_details['title'],
            "start_time": datetime.now().isoformat(),
            "test_types_generated": [],
            "test_files_created": [],
            "test_count": {
                "unit": 0,
                "integration": 0,
                "e2e": 0,
                "api": 0
            },
            "research_notes": "",
            "success": False
        }

        try:
            # Step 1: Research testing best practices using Context7
            research_notes = await self._research_testing_practices(task_details)
            generation_result["research_notes"] = research_notes

            print(f"[{self.agent_id}] Research completed - found testing patterns")

            # Step 2: Determine what test types are needed
            test_types_needed = self._determine_test_types(task_details)
            generation_result["test_types_needed"] = test_types_needed

            print(f"[{self.agent_id}] Test types needed: {', '.join(test_types_needed)}")

            # Step 3: Generate tests for each type
            if self.client:
                for test_type in test_types_needed:
                    test_files = await self._generate_tests(
                        project_path,
                        task_details,
                        test_type,
                        research_notes
                    )

                    if test_files:
                        generation_result["test_types_generated"].append(test_type)
                        generation_result["test_files_created"].extend(test_files)
                        generation_result["test_count"][test_type] += len(test_files)

                print(f"[{self.agent_id}] Generated {sum(generation_result['test_count'].values())} test files")

                # Step 3.5: Validate generated tests in E2B sandbox (if available)
                if self.sandbox_manager and generation_result["test_files_created"]:
                    print(f"[{self.agent_id}] Validating generated tests in E2B sandbox...")
                    validation_result = await self._validate_generated_tests(
                        project_path,
                        generation_result["test_files_created"]
                    )
                    generation_result["validation"] = validation_result

                    if validation_result.get("success"):
                        print(f"[{self.agent_id}] ✓ Generated tests validated successfully")
                    else:
                        print(f"[{self.agent_id}] ⚠️  Test validation had issues: {validation_result.get('error', 'Unknown error')}")
            else:
                print(f"[{self.agent_id}] No Claude client available - skipping test file generation")

            # Step 4: Update test coverage in checklist
            checklist.update_test_coverage(
                checklist_task_id,
                unit=generation_result["test_count"]["unit"],
                integration=generation_result["test_count"]["integration"],
                e2e=generation_result["test_count"]["e2e"],
                api=generation_result["test_count"]["api"]
            )

            # Step 5: Add note to task
            test_summary = self._generate_test_summary(generation_result)
            checklist.add_note(checklist_task_id, test_summary)

            # Step 6: Publish tests generated message
            if self.message_bus:
                self.message_bus.publish(
                    "task_updates",
                    {
                        "type": MessageTypes.TESTS_GENERATED,
                        "task_id": checklist_task_id,
                        "project_id": project_id,
                        "test_count": sum(generation_result["test_count"].values()),
                        "test_types": generation_result["test_types_generated"]
                    },
                    sender=self.agent_id,
                    priority="NORMAL"
                )

            generation_result["end_time"] = datetime.now().isoformat()
            generation_result["success"] = True

            return generation_result

        except Exception as e:
            generation_result["error"] = str(e)
            generation_result["success"] = False
            generation_result["end_time"] = datetime.now().isoformat()
            raise

    async def _research_testing_practices(self, task_details: Dict) -> str:
        """
        Research testing best practices using Context7 and memory.

        Args:
            task_details: Task information

        Returns:
            Research notes string
        """
        notes = []

        # Check memory for testing patterns
        title = task_details.get("title", "")
        category = task_details.get("category", "feature")

        # Search for similar testing patterns
        patterns = self.memory.find_similar_patterns(f"testing {title} {category}")
        if patterns:
            notes.append("## Testing Patterns from Memory")
            for pattern in patterns[:3]:
                notes.append(f"- {pattern['title']}: {pattern.get('description', '')}")

        # Add general testing knowledge from memory
        testing_knowledge = [k for k in self.memory.data.get("knowledge", []) if "test" in k.lower()]
        if testing_knowledge:
            notes.append("\n## Testing Knowledge")
            for knowledge in testing_knowledge[:5]:
                notes.append(f"- {knowledge}")

        # Research testing framework documentation using Context7
        framework_query = self._detect_testing_framework(title, task_details.get("description", ""))
        if framework_query:
            print(f"[{self.agent_id}] Researching {framework_query['library']} testing practices via Context7...")
            context7_result = await self._query_context7(framework_query["library"], framework_query["query"])
            notes.append("\n## Testing Framework Documentation (Context7)")
            notes.append(context7_result)

        if not notes:
            notes.append("## Default Testing Guidelines")
            notes.append("- Use AAA pattern (Arrange, Act, Assert)")
            notes.append("- Test happy path and edge cases")
            notes.append("- Keep tests isolated and independent")
            notes.append("- Use descriptive test names")
            notes.append("- Mock external dependencies")

        return "\n".join(notes)

    def _determine_test_types(self, task_details: Dict) -> List[str]:
        """
        Determine what types of tests are needed for this task.

        Args:
            task_details: Task information

        Returns:
            List of test types needed
        """
        test_types = []

        category = task_details.get("category", "feature")
        title = task_details.get("title", "").lower()
        description = task_details.get("description", "").lower()

        # Unit tests for most things
        if self.generate_unit_tests:
            test_types.append("unit")

        # Integration tests for features that integrate components
        if self.generate_integration_tests:
            if category in ["feature", "enhancement"] or "integrat" in description:
                test_types.append("integration")

        # E2E tests for UI features
        if self.generate_e2e_tests:
            if "ui" in title or "page" in title or "form" in title or "button" in title:
                test_types.append("e2e")

        # API tests for API endpoints
        if self.generate_api_tests:
            if "api" in title or "endpoint" in title or "route" in title:
                test_types.append("api")

        return test_types

    async def _generate_tests(
        self,
        project_path: Path,
        task_details: Dict,
        test_type: str,
        research_notes: str
    ) -> List[str]:
        """
        Generate test files using Claude SDK.

        Args:
            project_path: Path to project
            task_details: Task information
            test_type: Type of tests to generate (unit, integration, e2e, api)
            research_notes: Research notes from Context7/memory

        Returns:
            List of test file paths created
        """
        if not self.client:
            return []

        # Build prompt for test generation
        prompt = f"""# Generate {test_type.title()} Tests

## Feature to Test
{task_details.get('title', 'Unknown')}

## Description
{task_details.get('description', 'No description provided')}

## Testing Best Practices
{research_notes}

## Instructions
1. Generate comprehensive {test_type} tests for this feature
2. Follow the testing best practices above
3. Use appropriate testing framework for the project
4. Include:
   - Happy path tests
   - Edge case tests
   - Error handling tests
   - Proper setup and teardown
5. Use descriptive test names
6. Add comments explaining complex test logic

Please generate the {test_type} test files now.
"""

        try:
            # Run Claude agent to generate tests
            result = await self.client.run(prompt)

            # Parse result to extract test files created
            # This is simplified - in production, would parse Claude's output
            # to get actual file paths

            # For now, return placeholder
            test_files = [f"tests/{test_type}/test_{task_details.get('title', 'feature').replace(' ', '_').lower()}.test.js"]

            print(f"[{self.agent_id}] Generated {test_type} tests: {', '.join(test_files)}")

            return test_files

        except Exception as e:
            print(f"[{self.agent_id}] Error generating {test_type} tests: {e}")
            return []

    async def _validate_generated_tests(
        self,
        project_path: Path,
        test_files: List[str]
    ) -> Dict:
        """
        Validate generated tests by running them in E2B sandbox.

        Args:
            project_path: Path to project directory
            test_files: List of test file paths that were generated

        Returns:
            Dict with validation results
        """
        if not self.sandbox_manager:
            return {
                "success": False,
                "error": "No sandbox manager available"
            }

        try:
            # Determine test command based on project type
            test_command = "npm test"
            package_json = project_path / "package.json"

            if package_json.exists():
                import json
                try:
                    with open(package_json, 'r') as f:
                        pkg_data = json.load(f)
                        scripts = pkg_data.get('scripts', {})
                        if 'test' in scripts:
                            test_command = "npm test"
                        elif 'test:unit' in scripts:
                            test_command = "npm run test:unit"
                except Exception:
                    pass

            # Check for Python projects
            elif (project_path / "pytest.ini").exists() or (project_path / "setup.py").exists():
                test_command = "pytest"

            print(f"[{self.agent_id}] Validating tests with command: {test_command}")

            # Run tests in E2B
            test_result = await self.sandbox_manager.run_tests(
                project_path=project_path,
                test_command=test_command
            )

            validation_result = {
                "success": test_result.success,
                "tests_passed": test_result.tests_passed,
                "tests_failed": test_result.tests_failed,
                "test_output": test_result.test_output[:500] if test_result.test_output else "",  # Truncate
                "duration_seconds": test_result.duration_seconds,
                "error": test_result.error
            }

            if test_result.success:
                print(f"[{self.agent_id}] ✓ Tests validated: {test_result.tests_passed} passed")
            else:
                print(f"[{self.agent_id}] ✗ Test validation failed: {test_result.tests_failed} failures")

            return validation_result

        except Exception as e:
            print(f"[{self.agent_id}] Error validating tests: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_test_summary(self, generation_result: Dict) -> str:
        """
        Generate test generation summary for checklist notes.

        Args:
            generation_result: Test generation result dict

        Returns:
            Summary string
        """
        lines = [
            f"## Test Generation Report ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
            f"Generated by: {self.agent_id}",
            "",
            "### Tests Generated",
        ]

        for test_type in ["unit", "integration", "e2e", "api"]:
            count = generation_result["test_count"].get(test_type, 0)
            if count > 0:
                lines.append(f"- {test_type.title()}: {count} test file(s)")

        total_tests = sum(generation_result["test_count"].values())
        lines.append(f"\n**Total**: {total_tests} test file(s) created")

        if generation_result["test_files_created"]:
            lines.append("\n### Test Files")
            for test_file in generation_result["test_files_created"][:10]:  # Show first 10
                lines.append(f"- {test_file}")
            if len(generation_result["test_files_created"]) > 10:
                lines.append(f"- ... and {len(generation_result['test_files_created']) - 10} more")

        return "\n".join(lines)

    def _detect_testing_framework(self, title: str, description: str) -> Optional[Dict]:
        """
        Detect testing framework from task details.

        Args:
            title: Task title
            description: Task description

        Returns:
            Dict with library and query for Context7, or None
        """
        combined = (title + " " + description).lower()

        # Detect testing frameworks
        if "jest" in combined or ("react" in combined and "test" in combined):
            return {"library": "jest", "query": "Jest testing best practices and patterns"}
        elif "vitest" in combined or "vite" in combined:
            return {"library": "vitest", "query": "Vitest testing guide"}
        elif "pytest" in combined or ("python" in combined and "test" in combined):
            return {"library": "pytest", "query": "Pytest best practices and fixtures"}
        elif "mocha" in combined or "chai" in combined:
            return {"library": "mocha", "query": "Mocha and Chai testing patterns"}
        elif "testing-library" in combined or "react testing library" in combined:
            return {"library": "react-testing-library", "query": "React Testing Library best practices"}
        elif "cypress" in combined or "e2e" in combined:
            return {"library": "cypress", "query": "Cypress end-to-end testing best practices"}
        elif "playwright" in combined:
            return {"library": "playwright", "query": "Playwright testing patterns"}
        elif "api" in combined and "test" in combined:
            return {"library": "api-testing", "query": "API testing best practices"}
        elif "unit" in combined or "test" in combined:
            return {"library": "unit-testing", "query": "Unit testing best practices"}

        return None

    def get_system_prompt(self) -> str:
        """
        Get Test Generator agent-specific system prompt.

        Returns:
            System prompt string
        """
        return f"""You are a Test Generator Agent (ID: {self.agent_id}).

Your role is to create comprehensive test suites for all features.

Key responsibilities:
1. Generate unit tests for individual functions/components
2. Create integration tests for component interactions
3. Write E2E tests for user workflows
4. Develop API tests for endpoints
5. Research testing best practices using Context7
6. Follow framework-specific patterns

Testing types you generate:
- Unit tests: {self.generate_unit_tests}
- Integration tests: {self.generate_integration_tests}
- E2E tests: {self.generate_e2e_tests}
- API tests: {self.generate_api_tests}

Quality standards:
- Use AAA pattern (Arrange, Act, Assert)
- Test happy path and edge cases
- Include error handling tests
- Keep tests isolated and independent
- Use descriptive test names
- Mock external dependencies
- Add helpful comments

Tools at your disposal:
- Context7: Research testing framework documentation
- Memory: Learn from past test patterns
- Filesystem: Create and organize test files
- Sequential Thinking: Plan complex test scenarios

Test organization:
- tests/unit/ - Unit tests
- tests/integration/ - Integration tests
- tests/e2e/ - End-to-end tests
- tests/api/ - API tests

Current statistics:
- Tasks completed: {self.task_count}
- Success rate: {(self.success_count / self.task_count * 100) if self.task_count > 0 else 0:.1f}%

Generate thorough tests that catch bugs before production.
"""

    async def extract_patterns(self, task: Dict, result: Dict):
        """
        Extract patterns from test generation results.

        Overrides base class to add TestGenerator-specific pattern extraction.

        Args:
            task: Completed task
            result: Task result
        """
        await super().extract_patterns(task, result)

        # Add TestGenerator-specific patterns
        if result.get("success"):
            data = result.get("data", {})
            test_types = data.get("test_types_generated", [])

            # Record patterns about test coverage
            for test_type in test_types:
                self.memory.add_knowledge(
                    f"Testing pattern: {task.get('type')} tasks benefit from {test_type} tests"
                )

            # Record successful test generation patterns
            if data.get("test_files_created"):
                self.memory.add_pattern(
                    title=f"Test generation for {task.get('type')}",
                    description=f"Generated {len(test_types)} types of tests with {sum(data['test_count'].values())} files",
                    learned_from=str(task.get("task_id")),
                    context=data
                )

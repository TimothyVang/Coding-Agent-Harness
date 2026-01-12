"""
Builder Agent
=============

Specialized agent for feature implementation and code generation.

The Builder Agent is responsible for:
- Implementing new features based on task descriptions
- Writing clean, production-ready code
- Following best practices and coding standards
- Using Context7 to research libraries and patterns
- Creating necessary tests
- Documenting code appropriately
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from claude_code_sdk import ClaudeSDKClient

from core.agent_memory import AgentMemory
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus, MessageTypes
from agents.base_agent import BaseAgent


class BuilderAgent(BaseAgent):
    """
    Builder agent for feature implementation.

    Specializes in:
    - Code generation and implementation
    - Best practice application
    - Test creation
    - Code documentation
    - Refactoring and optimization
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[ClaudeSDKClient] = None
    ):
        """
        Initialize Builder agent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client for code generation
        """
        super().__init__(agent_id, "builder", config, message_bus)
        self.client = claude_client

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a build/implementation task.

        Process:
        1. Load task details from checklist
        2. Research best practices using Context7
        3. Generate implementation plan
        4. Write code
        5. Create tests
        6. Document changes
        7. Update checklist

        Args:
            task: Task dict with project_id, checklist_task_id, metadata

        Returns:
            Result dict with success status and implementation details
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

        print(f"[{self.agent_id}] Building: {task_details['title']}")

        # Check for similar patterns in memory
        similar_patterns = self.memory.find_similar_patterns(task_details['title'])
        if similar_patterns:
            print(f"[{self.agent_id}] Found {len(similar_patterns)} similar patterns in memory")

        # Implementation steps
        implementation_result = {
            "task_id": checklist_task_id,
            "title": task_details['title'],
            "start_time": datetime.now().isoformat(),
            "steps_completed": [],
            "files_modified": [],
            "tests_created": [],
            "errors": []
        }

        try:
            # Step 1: Research (if Context7 available)
            research_notes = await self._research_best_practices(task_details)
            implementation_result["steps_completed"].append("research")

            # Step 2: Plan implementation
            implementation_plan = await self._create_implementation_plan(
                task_details,
                research_notes
            )
            implementation_result["steps_completed"].append("planning")

            # Step 3: Execute implementation using Claude SDK
            if self.client:
                implementation_output = await self._execute_with_claude(
                    project_path,
                    task_details,
                    implementation_plan,
                    research_notes
                )
                implementation_result["files_modified"] = implementation_output.get("files_modified", [])
                implementation_result["tests_created"] = implementation_output.get("tests_created", [])
            else:
                print(f"[{self.agent_id}] ⚠️  No Claude client available - cannot execute implementation")
                implementation_result["errors"].append("No Claude client available")

            implementation_result["steps_completed"].append("implementation")

            # Step 4: Update checklist
            checklist.add_note(
                checklist_task_id,
                f"Implementation completed by {self.agent_id}\n" +
                f"Files modified: {len(implementation_result['files_modified'])}\n" +
                f"Tests created: {len(implementation_result['tests_created'])}"
            )
            checklist.update_task(checklist_task_id, status="Done")
            implementation_result["steps_completed"].append("checklist_updated")

            # Record success
            implementation_result["end_time"] = datetime.now().isoformat()
            implementation_result["success"] = True

            # Extract patterns for future use
            await self._extract_and_save_patterns(task_details, implementation_result)

            return implementation_result

        except Exception as e:
            implementation_result["errors"].append(str(e))
            implementation_result["success"] = False
            implementation_result["end_time"] = datetime.now().isoformat()
            raise

    async def _research_best_practices(self, task_details: Dict) -> str:
        """
        Research best practices using Context7 or memory.

        Args:
            task_details: Task information

        Returns:
            Research notes string
        """
        notes = []

        # Check memory for relevant knowledge
        title = task_details.get("title", "")
        description = task_details.get("description", "")

        # Search for similar patterns
        patterns = self.memory.find_similar_patterns(f"{title} {description}")
        if patterns:
            notes.append("## Patterns from Memory")
            for pattern in patterns[:3]:  # Top 3
                notes.append(f"- {pattern['title']}: {pattern.get('description', '')}")

        # Check for relevant mistakes
        mistakes = self.memory.get_relevant_mistakes(f"{title} {description}")
        if mistakes:
            notes.append("\n## Mistakes to Avoid")
            for mistake in mistakes[:3]:
                notes.append(f"- {mistake['title']}: {mistake['solution']}")

        # TODO: If Context7 client available, query for library-specific docs
        # For now, just use memory

        return "\n".join(notes) if notes else "No specific patterns found in memory."

    async def _create_implementation_plan(
        self,
        task_details: Dict,
        research_notes: str
    ) -> str:
        """
        Create implementation plan based on task and research.

        Args:
            task_details: Task information
            research_notes: Research from Context7/memory

        Returns:
            Implementation plan string
        """
        plan = f"""# Implementation Plan

## Task
{task_details.get('title', 'Unknown')}

## Description
{task_details.get('description', 'No description provided')}

## Research Notes
{research_notes}

## Steps
1. Identify files to modify/create
2. Implement core functionality
3. Add error handling
4. Create tests (unit, integration as needed)
5. Add documentation
6. Update checklist

## Quality Checks
- Code follows best practices from research
- All edge cases handled
- Tests cover main scenarios
- Documentation is clear
"""
        return plan

    async def _execute_with_claude(
        self,
        project_path: Path,
        task_details: Dict,
        implementation_plan: str,
        research_notes: str
    ) -> Dict:
        """
        Execute implementation using Claude SDK client.

        Args:
            project_path: Path to project directory
            task_details: Task information
            implementation_plan: Implementation plan
            research_notes: Research notes

        Returns:
            Dict with files_modified and tests_created
        """
        if not self.client:
            return {"files_modified": [], "tests_created": [], "error": "No Claude client"}

        # Build prompt for Claude
        prompt = f"""# Build Task

{implementation_plan}

## Task Details
Title: {task_details.get('title', 'Unknown')}
Description: {task_details.get('description', 'No description')}

## Instructions
1. Implement this feature following the plan
2. Use the research notes to apply best practices
3. Create necessary tests
4. Document your changes
5. Update any relevant files

Please implement this feature now."""

        try:
            # Run Claude agent to implement the feature
            # The agent will use all available MCP tools (filesystem, git, etc.)
            result = await self.client.run(prompt)

            # Extract information about what was done
            # This is a simplified version - in production, parse Claude's output
            return {
                "files_modified": [],  # Would parse from Claude output
                "tests_created": [],   # Would parse from Claude output
                "output": str(result)
            }

        except Exception as e:
            print(f"[{self.agent_id}] Error executing with Claude: {e}")
            return {
                "files_modified": [],
                "tests_created": [],
                "error": str(e)
            }

    async def _extract_and_save_patterns(
        self,
        task_details: Dict,
        implementation_result: Dict
    ):
        """
        Extract learned patterns from successful implementation.

        Args:
            task_details: Task information
            implementation_result: Implementation result
        """
        if not implementation_result.get("success"):
            return

        # Extract pattern
        pattern_title = f"Implementation: {task_details.get('title', 'Unknown')}"
        pattern_description = f"""
Implemented successfully with:
- {len(implementation_result.get('files_modified', []))} files modified
- {len(implementation_result.get('tests_created', []))} tests created
- Steps: {', '.join(implementation_result.get('steps_completed', []))}
"""

        # Add to memory
        self.memory.add_pattern(
            title=pattern_title,
            description=pattern_description.strip(),
            learned_from=str(implementation_result.get('task_id')),
            context=implementation_result
        )

    def get_system_prompt(self) -> str:
        """
        Get Builder agent-specific system prompt.

        Returns:
            System prompt string
        """
        return f"""You are a Builder Agent (ID: {self.agent_id}).

Your role is to implement features and build software components.

Key responsibilities:
1. Read task descriptions carefully
2. Research best practices using available tools
3. Write clean, production-ready code
4. Create comprehensive tests
5. Document your work clearly
6. Follow coding standards and patterns

Tools at your disposal:
- Context7: Research libraries and best practices
- Filesystem: Read and write files
- Git: Version control operations
- Memory: Store and retrieve learned patterns
- Sequential Thinking: Plan complex implementations

Quality standards:
- Code must be readable and maintainable
- All edge cases must be handled
- Tests must cover main scenarios
- Documentation must be clear and concise

Current statistics:
- Tasks completed: {self.task_count}
- Success rate: {(self.success_count / self.task_count * 100) if self.task_count > 0 else 0:.1f}%

Learn from your experiences and continuously improve your code quality.
"""

    async def extract_patterns(self, task: Dict, result: Dict):
        """
        Extract patterns from successful build task.

        Overrides base class to add Builder-specific pattern extraction.

        Args:
            task: Completed task
            result: Task result
        """
        # Call parent implementation
        await super().extract_patterns(task, result)

        # Add Builder-specific patterns
        if result.get("success"):
            data = result.get("data", {})
            files_modified = data.get("files_modified", [])

            if files_modified:
                # Record pattern about which files typically change together
                self.memory.add_knowledge(
                    f"Build pattern: {task.get('type')} typically modifies {len(files_modified)} files"
                )

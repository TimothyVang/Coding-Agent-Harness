"""
Architect Agent
===============

Specialized agent for feature planning and architectural design.

The Architect Agent is responsible for:
- Analyzing requirements and breaking them down into tasks
- Researching architecture patterns using Context7
- Creating detailed implementation plans
- Designing component interactions and data flows
- Making architectural decisions (patterns, libraries, approaches)
- Creating subtasks for complex features
- Documenting architectural decisions
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


class ArchitectAgent(BaseAgent):
    """
    Architect agent for feature planning and design.

    Specializes in:
    - Requirements analysis
    - Architecture research (Context7)
    - Implementation planning
    - Task breakdown and subtask creation
    - Component design
    - Pattern selection
    - Architectural decision documentation
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[ClaudeSDKClient] = None
    ):
        """
        Initialize Architect agent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client for architecture tasks
        """
        super().__init__(agent_id, "architect", config, message_bus)
        self.client = claude_client

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute an architecture/planning task.

        Process:
        1. Load task details from checklist
        2. Analyze requirements
        3. Research architecture patterns using Context7
        4. Design component interactions
        5. Make architectural decisions
        6. Create implementation plan
        7. Break down into subtasks
        8. Document decisions in checklist

        Args:
            task: Task dict with project_id, checklist_task_id, metadata

        Returns:
            Result dict with architecture plan and subtasks created
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

        print(f"[{self.agent_id}] Planning: {task_details['title']}")

        # Architecture result
        architecture_result = {
            "task_id": checklist_task_id,
            "title": task_details['title'],
            "start_time": datetime.now().isoformat(),
            "architecture_research": "",
            "implementation_plan": "",
            "architectural_decisions": [],
            "subtasks_created": [],
            "components_designed": [],
            "patterns_recommended": [],
            "success": False
        }

        try:
            # Step 1: Analyze requirements
            requirements_analysis = await self._analyze_requirements(task_details)
            architecture_result["requirements_analysis"] = requirements_analysis

            print(f"[{self.agent_id}] Requirements analyzed - complexity: {requirements_analysis.get('complexity', 'unknown')}")

            # Step 2: Research architecture patterns using Context7 and memory
            architecture_research = await self._research_architecture(task_details, requirements_analysis)
            architecture_result["architecture_research"] = architecture_research

            print(f"[{self.agent_id}] Architecture research completed")

            # Step 3: Design components and interactions
            component_design = await self._design_components(
                task_details,
                requirements_analysis,
                architecture_research
            )
            architecture_result["components_designed"] = component_design.get("components", [])
            architecture_result["interactions"] = component_design.get("interactions", [])

            print(f"[{self.agent_id}] Designed {len(architecture_result['components_designed'])} components")

            # Step 4: Make architectural decisions
            decisions = await self._make_architectural_decisions(
                task_details,
                requirements_analysis,
                architecture_research
            )
            architecture_result["architectural_decisions"] = decisions
            architecture_result["patterns_recommended"] = [d.get("pattern") for d in decisions if d.get("pattern")]

            print(f"[{self.agent_id}] Made {len(decisions)} architectural decisions")

            # Step 5: Create implementation plan
            implementation_plan = await self._create_implementation_plan(
                task_details,
                requirements_analysis,
                component_design,
                decisions
            )
            architecture_result["implementation_plan"] = implementation_plan

            # Step 6: Break down into subtasks (if complex)
            if requirements_analysis.get("complexity") in ["medium", "high", "very_high"]:
                subtasks = await self._create_subtasks(
                    checklist,
                    checklist_task_id,
                    task_details,
                    requirements_analysis,
                    component_design
                )
                architecture_result["subtasks_created"] = subtasks

                print(f"[{self.agent_id}] Created {len(subtasks)} subtasks")

                # Publish subtasks created message
                if self.message_bus and subtasks:
                    self.message_bus.publish(
                        "task_updates",
                        {
                            "type": MessageTypes.SUBTASKS_CREATED,
                            "parent_task_id": checklist_task_id,
                            "subtask_count": len(subtasks),
                            "blocking": False
                        },
                        sender=self.agent_id,
                        priority="NORMAL"
                    )

            # Step 7: Document architecture in checklist
            architecture_doc = self._generate_architecture_documentation(architecture_result)
            checklist.add_note(checklist_task_id, architecture_doc)

            # Update task status to In Progress (ready for builder)
            checklist.update_task(checklist_task_id, status="In Progress")

            architecture_result["end_time"] = datetime.now().isoformat()
            architecture_result["success"] = True

            return architecture_result

        except Exception as e:
            architecture_result["error"] = str(e)
            architecture_result["success"] = False
            architecture_result["end_time"] = datetime.now().isoformat()
            raise

    async def _analyze_requirements(self, task_details: Dict) -> Dict:
        """
        Analyze requirements to determine complexity and scope.

        Args:
            task_details: Task information

        Returns:
            Requirements analysis dict
        """
        title = task_details.get("title", "")
        description = task_details.get("description", "")
        category = task_details.get("category", "feature")

        # Determine complexity based on keywords and description length
        complexity = "low"

        # High complexity indicators
        high_complexity_keywords = ["authentication", "payment", "integration", "api", "database", "migration"]
        medium_complexity_keywords = ["form", "dashboard", "list", "detail", "search", "filter"]

        combined_text = (title + " " + description).lower()

        if any(keyword in combined_text for keyword in high_complexity_keywords):
            complexity = "high"
        elif any(keyword in combined_text for keyword in medium_complexity_keywords):
            complexity = "medium"
        elif len(description) > 200:
            complexity = "medium"

        # Determine scope
        scope_indicators = {
            "frontend": ["ui", "page", "component", "button", "form", "display"],
            "backend": ["api", "endpoint", "server", "database", "model"],
            "fullstack": ["integrate", "connect", "full", "complete"],
            "infrastructure": ["deploy", "ci/cd", "docker", "kubernetes"]
        }

        scope = []
        for scope_type, keywords in scope_indicators.items():
            if any(keyword in combined_text for keyword in keywords):
                scope.append(scope_type)

        if not scope:
            scope = ["unknown"]

        return {
            "complexity": complexity,
            "scope": scope,
            "estimated_subtasks": self._estimate_subtask_count(complexity),
            "requires_research": complexity in ["medium", "high"],
            "requires_design": complexity in ["high"],
            "key_challenges": self._identify_challenges(combined_text)
        }

    def _estimate_subtask_count(self, complexity: str) -> int:
        """Estimate number of subtasks based on complexity."""
        estimates = {
            "low": 0,
            "medium": 3,
            "high": 5,
            "very_high": 8
        }
        return estimates.get(complexity, 0)

    def _identify_challenges(self, text: str) -> List[str]:
        """Identify potential challenges from text."""
        challenges = []

        challenge_keywords = {
            "Security": ["security", "authentication", "authorization", "auth"],
            "Performance": ["performance", "scale", "optimization", "cache"],
            "Integration": ["integrate", "third-party", "api", "external"],
            "Data consistency": ["transaction", "consistency", "sync"],
            "User experience": ["ux", "usability", "user experience"]
        }

        for challenge_name, keywords in challenge_keywords.items():
            if any(keyword in text for keyword in keywords):
                challenges.append(challenge_name)

        return challenges

    async def _research_architecture(self, task_details: Dict, requirements: Dict) -> str:
        """
        Research architecture patterns using Context7 and memory.

        Args:
            task_details: Task information
            requirements: Requirements analysis

        Returns:
            Architecture research notes
        """
        notes = []

        # Check memory for similar patterns
        title = task_details.get("title", "")
        patterns = self.memory.find_similar_patterns(f"architecture {title}")

        if patterns:
            notes.append("## Architecture Patterns from Memory")
            for pattern in patterns[:3]:
                notes.append(f"- {pattern['title']}: {pattern.get('description', '')}")

        # Add general architecture knowledge
        arch_knowledge = [k for k in self.memory.data.get("knowledge", []) if "architecture" in k.lower() or "pattern" in k.lower()]
        if arch_knowledge:
            notes.append("\n## Architecture Knowledge")
            for knowledge in arch_knowledge[:5]:
                notes.append(f"- {knowledge}")

        # TODO: Use Context7 to research specific architecture patterns
        # For example: "Microservices architecture best practices", "React state management patterns"

        # Add recommendations based on requirements
        if requirements.get("complexity") == "high":
            notes.append("\n## Recommendations for High Complexity")
            notes.append("- Break down into smaller, testable components")
            notes.append("- Use established patterns (MVC, MVVM, etc.)")
            notes.append("- Plan for scalability and maintainability")
            notes.append("- Consider separation of concerns")

        if "fullstack" in requirements.get("scope", []):
            notes.append("\n## Full-Stack Considerations")
            notes.append("- Define clear API contracts")
            notes.append("- Plan data flow between frontend and backend")
            notes.append("- Consider error handling at all layers")

        return "\n".join(notes) if notes else "No specific architecture patterns found."

    async def _design_components(
        self,
        task_details: Dict,
        requirements: Dict,
        architecture_research: str
    ) -> Dict:
        """
        Design components and their interactions.

        Args:
            task_details: Task information
            requirements: Requirements analysis
            architecture_research: Research notes

        Returns:
            Component design dict
        """
        components = []
        interactions = []

        complexity = requirements.get("complexity")
        scope = requirements.get("scope", [])

        # Design components based on scope
        if "frontend" in scope or "fullstack" in scope:
            components.append({
                "name": "UI Component",
                "type": "frontend",
                "responsibilities": ["User interface", "User input handling", "Display logic"]
            })

        if "backend" in scope or "fullstack" in scope:
            components.append({
                "name": "API Service",
                "type": "backend",
                "responsibilities": ["Business logic", "Data validation", "API endpoints"]
            })

            components.append({
                "name": "Data Model",
                "type": "backend",
                "responsibilities": ["Data schema", "Database operations", "Data validation"]
            })

        # Define interactions
        if len(components) > 1:
            interactions.append({
                "from": "UI Component",
                "to": "API Service",
                "type": "HTTP Request",
                "description": "User actions trigger API calls"
            })

            interactions.append({
                "from": "API Service",
                "to": "Data Model",
                "description": "Service layer uses data model for persistence"
            })

        return {
            "components": components,
            "interactions": interactions
        }

    async def _make_architectural_decisions(
        self,
        task_details: Dict,
        requirements: Dict,
        architecture_research: str
    ) -> List[Dict]:
        """
        Make key architectural decisions.

        Args:
            task_details: Task information
            requirements: Requirements analysis
            architecture_research: Research notes

        Returns:
            List of architectural decisions
        """
        decisions = []

        # Decision on architecture pattern
        if requirements.get("complexity") == "high":
            decisions.append({
                "decision": "Use layered architecture",
                "pattern": "Layered Architecture",
                "rationale": "High complexity requires clear separation of concerns",
                "alternatives_considered": ["Flat structure", "Monolithic"]
            })

        # Decision on state management (for frontend)
        if "frontend" in requirements.get("scope", []):
            decisions.append({
                "decision": "Use React Context for state management",
                "pattern": "Context API",
                "rationale": "Appropriate for medium-complexity state needs",
                "alternatives_considered": ["Redux", "MobX", "Zustand"]
            })

        # Decision on API design (for backend)
        if "backend" in requirements.get("scope", []):
            decisions.append({
                "decision": "Use RESTful API design",
                "pattern": "REST",
                "rationale": "Standard, well-understood, easy to consume",
                "alternatives_considered": ["GraphQL", "gRPC"]
            })

        return decisions

    async def _create_implementation_plan(
        self,
        task_details: Dict,
        requirements: Dict,
        component_design: Dict,
        decisions: List[Dict]
    ) -> str:
        """
        Create detailed implementation plan.

        Args:
            task_details: Task information
            requirements: Requirements analysis
            component_design: Component design
            decisions: Architectural decisions

        Returns:
            Implementation plan as markdown string
        """
        lines = [
            "# Implementation Plan",
            "",
            f"## Feature: {task_details.get('title')}",
            "",
            f"**Complexity**: {requirements.get('complexity')}",
            f"**Scope**: {', '.join(requirements.get('scope', []))}",
            "",
            "## Architecture Decisions",
            ""
        ]

        for decision in decisions:
            lines.append(f"### {decision['decision']}")
            lines.append(f"- **Pattern**: {decision.get('pattern', 'N/A')}")
            lines.append(f"- **Rationale**: {decision['rationale']}")
            lines.append("")

        lines.extend([
            "## Components",
            ""
        ])

        for component in component_design.get("components", []):
            lines.append(f"### {component['name']} ({component['type']})")
            lines.append("**Responsibilities**:")
            for resp in component.get("responsibilities", []):
                lines.append(f"- {resp}")
            lines.append("")

        lines.extend([
            "## Implementation Steps",
            "1. Set up component structure",
            "2. Implement core logic",
            "3. Add error handling",
            "4. Create unit tests",
            "5. Integration testing",
            "6. Documentation",
            "",
            "## Quality Checklist",
            "- [ ] All components implemented",
            "- [ ] Tests passing",
            "- [ ] Documentation updated",
            "- [ ] Code reviewed",
            ""
        ])

        return "\n".join(lines)

    async def _create_subtasks(
        self,
        checklist: EnhancedChecklistManager,
        parent_task_id: int,
        task_details: Dict,
        requirements: Dict,
        component_design: Dict
    ) -> List[int]:
        """
        Create subtasks for complex features.

        Args:
            checklist: Checklist manager
            parent_task_id: Parent task ID
            task_details: Task information
            requirements: Requirements analysis
            component_design: Component design

        Returns:
            List of created subtask IDs
        """
        subtask_ids = []

        # Create subtasks based on components
        for component in component_design.get("components", []):
            subtask = {
                "title": f"Implement {component['name']}",
                "description": "\n".join([
                    f"Component type: {component['type']}",
                    "Responsibilities:",
                    *[f"- {resp}" for resp in component.get("responsibilities", [])]
                ]),
                "category": "implementation",
                "priority": "high"
            }

            subtask_id = checklist.add_subtask(parent_task_id, subtask)
            subtask_ids.append(subtask_id)

            print(f"[{self.agent_id}]   - Created subtask {subtask_id}: {subtask['title']}")

        # Add testing subtask
        test_subtask = {
            "title": "Create comprehensive tests",
            "description": "Generate unit, integration, and E2E tests",
            "category": "testing",
            "priority": "high"
        }
        test_subtask_id = checklist.add_subtask(parent_task_id, test_subtask)
        subtask_ids.append(test_subtask_id)

        print(f"[{self.agent_id}]   - Created test subtask {test_subtask_id}")

        return subtask_ids

    def _generate_architecture_documentation(self, architecture_result: Dict) -> str:
        """
        Generate architecture documentation for checklist notes.

        Args:
            architecture_result: Architecture result dict

        Returns:
            Documentation string
        """
        lines = [
            f"## Architecture Plan ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
            f"Designed by: {self.agent_id}",
            ""
        ]

        # Requirements
        if architecture_result.get("requirements_analysis"):
            req = architecture_result["requirements_analysis"]
            lines.extend([
                "### Requirements Analysis",
                f"- Complexity: {req.get('complexity', 'unknown')}",
                f"- Scope: {', '.join(req.get('scope', []))}",
                f"- Estimated subtasks: {req.get('estimated_subtasks', 0)}",
                ""
            ])

        # Components
        if architecture_result.get("components_designed"):
            lines.append("### Components Designed")
            for component in architecture_result["components_designed"]:
                lines.append(f"- {component['name']} ({component['type']})")
            lines.append("")

        # Architectural decisions
        if architecture_result.get("architectural_decisions"):
            lines.append("### Architectural Decisions")
            for decision in architecture_result["architectural_decisions"]:
                lines.append(f"- {decision['decision']}")
                lines.append(f"  Pattern: {decision.get('pattern', 'N/A')}")
            lines.append("")

        # Subtasks
        if architecture_result.get("subtasks_created"):
            lines.append(f"### Subtasks Created: {len(architecture_result['subtasks_created'])}")
            lines.append("")

        lines.append("### Next Steps")
        lines.append("1. Builder agent will implement each component")
        lines.append("2. Test Generator will create test suites")
        lines.append("3. Verifier will ensure completion")
        lines.append("4. Reviewer will review code quality")

        return "\n".join(lines)

    def get_system_prompt(self) -> str:
        """
        Get Architect agent-specific system prompt.

        Returns:
            System prompt string
        """
        return f"""You are an Architect Agent (ID: {self.agent_id}).

Your role is to plan and design features before implementation.

Key responsibilities:
1. Analyze requirements and determine complexity
2. Research architecture patterns using Context7
3. Design components and their interactions
4. Make informed architectural decisions
5. Create detailed implementation plans
6. Break complex features into subtasks
7. Document architectural decisions

Architecture principles:
- Separation of concerns
- Modularity and reusability
- Scalability and maintainability
- Clear component boundaries
- Well-defined interfaces
- Consider future extensibility

Tools at your disposal:
- Context7: Research architecture patterns and best practices
- Memory: Learn from past architectural decisions
- Sequential Thinking: Plan complex architectures systematically
- Checklist: Create subtasks for complex features

Decision-making approach:
1. Understand requirements thoroughly
2. Research relevant patterns
3. Consider multiple approaches
4. Document rationale for decisions
5. Plan for testing and verification

Current statistics:
- Tasks planned: {self.task_count}
- Success rate: {(self.success_count / self.task_count * 100) if self.task_count > 0 else 0:.1f}%

Good architecture prevents problems later - think ahead and plan thoroughly.
"""

    async def extract_patterns(self, task: Dict, result: Dict):
        """
        Extract patterns from architecture results.

        Overrides base class to add Architect-specific pattern extraction.

        Args:
            task: Completed task
            result: Task result
        """
        await super().extract_patterns(task, result)

        # Add Architect-specific patterns
        if result.get("success"):
            data = result.get("data", {})
            decisions = data.get("architectural_decisions", [])

            # Record architectural patterns used
            for decision in decisions:
                pattern = decision.get("pattern")
                if pattern:
                    self.memory.add_knowledge(
                        f"Architecture pattern: {pattern} works well for {decision.get('decision', 'unknown use case')}"
                    )

            # Record component design patterns
            components = data.get("components_designed", [])
            if components:
                self.memory.add_pattern(
                    title=f"Component design for {task.get('type')}",
                    description=f"Designed {len(components)} components with clear responsibilities",
                    learned_from=str(task.get("task_id")),
                    context={"components": components}
                )

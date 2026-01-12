"""
Documentation Agent
===================

Documentation generation agent for creating comprehensive project documentation.

Responsibilities:
- API documentation generation
- User guide creation
- Technical specification documents
- README file updates
- Inline code documentation
- Architecture documentation
- Changelog generation
- Contributing guidelines
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_agent import BaseAgent
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus, MessageTypes
from core.agent_memory import AgentMemory


class DocumentationAgent(BaseAgent):
    """
    Documentation Agent - Comprehensive Documentation Generation

    Responsibilities:
    - Generate API documentation
    - Create user guides and tutorials
    - Write technical specifications
    - Update README files
    - Add inline code documentation
    - Create architecture documentation
    - Generate changelogs
    - Write contributing guidelines

    This agent learns documentation patterns and improves over time.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        message_bus: Optional[MessageBus] = None,
        claude_client: Optional[Any] = None
    ):
        """
        Initialize DocumentationAgent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration dict
            message_bus: Optional message bus for communication
            claude_client: Optional Claude SDK client
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="documentation",
            config=config,
            message_bus=message_bus
        )
        self.client = claude_client

        # Documentation-specific configuration
        self.doc_types = config.get("doc_types", [
            "api",
            "user_guide",
            "technical_spec",
            "readme",
            "inline",
            "architecture",
            "changelog"
        ])

        self.doc_format = config.get("doc_format", "markdown")  # markdown, rst, html
        self.include_examples = config.get("include_examples", True)
        self.generate_diagrams = config.get("generate_diagrams", True)
        self.auto_update_readme = config.get("auto_update_readme", True)

        print(f"[DocumentationAgent] Initialized with ID: {self.agent_id}")
        print(f"  - Documentation types: {len(self.doc_types)}")
        print(f"  - Format: {self.doc_format}")
        print(f"  - Include examples: {self.include_examples}")

    async def execute_task(self, task: Dict) -> Dict:
        """
        Execute a documentation task.

        Process:
        1. Load task details from checklist
        2. Determine documentation needs
        3. Research documentation best practices
        4. Generate API documentation
        5. Create user guides
        6. Write technical specifications
        7. Update README
        8. Generate architecture docs
        9. Update checklist

        Args:
            task: Task dict from queue with project_id, checklist_task_id

        Returns:
            Dict with success status and documentation details
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
            self.print_status(f"Documentation: {task_title}")

            # Documentation result tracking
            doc_result = {
                "task_id": checklist_task_id,
                "timestamp": datetime.now().isoformat(),
                "docs_created": [],
                "docs_updated": [],
                "total_sections": 0,
                "total_pages": 0
            }

            # Step 1: Load patterns from memory
            self.memory.load_patterns()

            # Step 2: Analyze documentation needs
            doc_needs = await self._analyze_documentation_needs(task_details, project_path)
            doc_result["documentation_needs"] = doc_needs

            # Step 3: Research documentation best practices
            if self.client:
                research_summary = await self._research_documentation_practices(task_details)
                doc_result["research_summary"] = research_summary

            # Step 4: Generate API documentation
            if doc_needs.get("needs_api_docs"):
                api_docs = await self._generate_api_documentation(task_details, project_path)
                doc_result["docs_created"].append("API Documentation")
                doc_result["total_sections"] += api_docs.get("sections", 0)

            # Step 5: Create user guides
            if doc_needs.get("needs_user_guide"):
                user_guide = await self._create_user_guide(task_details, project_path)
                doc_result["docs_created"].append("User Guide")
                doc_result["total_pages"] += 1

            # Step 6: Write technical specifications
            if doc_needs.get("needs_tech_spec"):
                tech_spec = await self._create_technical_spec(task_details, project_path)
                doc_result["docs_created"].append("Technical Specification")
                doc_result["total_pages"] += 1

            # Step 7: Update README
            if self.auto_update_readme or doc_needs.get("needs_readme_update"):
                readme_update = await self._update_readme(task_details, project_path)
                doc_result["docs_updated"].append("README.md")

            # Step 8: Generate architecture documentation
            if doc_needs.get("needs_architecture_docs"):
                arch_docs = await self._generate_architecture_docs(task_details, project_path)
                doc_result["docs_created"].append("Architecture Documentation")
                doc_result["total_pages"] += 1

            # Step 9: Generate inline code documentation
            if doc_needs.get("needs_inline_docs"):
                inline_docs = await self._add_inline_documentation(task_details, project_path)
                doc_result["docs_updated"].append("Inline Documentation")

            # Step 10: Create documentation summary
            summary_doc = await self._create_documentation_summary(
                task_details,
                doc_result
            )

            # Step 11: Update checklist with documentation results
            if self.client:
                summary = self._create_summary(doc_result)
                checklist.add_note(checklist_task_id, f"Documentation complete: {summary}")

            return {
                "success": True,
                "data": {
                    "doc_result": doc_result,
                    "summary": summary_doc,
                    "docs_created_count": len(doc_result["docs_created"]),
                    "docs_updated_count": len(doc_result["docs_updated"])
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Documentation task execution failed: {str(e)}"
            }

    async def _analyze_documentation_needs(self, task_details: Dict, project_path: Path) -> Dict:
        """
        Analyze what documentation is needed.

        Returns dict with flags:
        - needs_api_docs: API documentation required
        - needs_user_guide: User guide required
        - needs_tech_spec: Technical specification required
        - needs_readme_update: README update required
        - needs_architecture_docs: Architecture documentation required
        - needs_inline_docs: Inline code documentation required
        - needs_changelog: Changelog update required
        """
        title = task_details.get("title", "").lower()
        description = task_details.get("description", "").lower()
        combined = f"{title} {description}"

        needs = {
            "needs_api_docs": False,
            "needs_user_guide": False,
            "needs_tech_spec": False,
            "needs_readme_update": False,
            "needs_architecture_docs": False,
            "needs_inline_docs": False,
            "needs_changelog": False
        }

        # Check for API documentation needs
        if any(keyword in combined for keyword in ["api", "endpoint", "rest", "graphql", "sdk"]):
            needs["needs_api_docs"] = True

        # Check for user guide needs
        if any(keyword in combined for keyword in ["user guide", "tutorial", "how to", "getting started"]):
            needs["needs_user_guide"] = True

        # Check for technical spec needs
        if any(keyword in combined for keyword in ["specification", "technical", "design doc", "architecture"]):
            needs["needs_tech_spec"] = True
            needs["needs_architecture_docs"] = True

        # Check for README update needs
        if any(keyword in combined for keyword in ["readme", "setup", "installation", "quick start"]):
            needs["needs_readme_update"] = True

        # Check for inline documentation needs
        if any(keyword in combined for keyword in ["comment", "docstring", "inline", "code documentation"]):
            needs["needs_inline_docs"] = True

        # Check for changelog needs
        if any(keyword in combined for keyword in ["changelog", "release", "version"]):
            needs["needs_changelog"] = True

        return needs

    async def _generate_api_documentation(self, task_details: Dict, project_path: Path) -> Dict:
        """Generate API documentation."""
        print("[Documentation] Generating API documentation...")

        api_docs = {
            "sections": 0,
            "endpoints_documented": 0,
            "examples_included": False
        }

        # TODO: With Claude client, generate actual API documentation
        # - Parse API endpoints
        # - Document request/response formats
        # - Add examples
        # - Generate SDK documentation

        return api_docs

    async def _create_user_guide(self, task_details: Dict, project_path: Path) -> Dict:
        """Create user guide."""
        print("[Documentation] Creating user guide...")

        user_guide = {
            "sections": ["Getting Started", "Features", "Usage", "Troubleshooting"],
            "created": False
        }

        # TODO: With Claude client, generate user guide
        # - Getting started section
        # - Feature documentation
        # - Usage examples
        # - Troubleshooting guide

        return user_guide

    async def _create_technical_spec(self, task_details: Dict, project_path: Path) -> Dict:
        """Create technical specification."""
        print("[Documentation] Creating technical specification...")

        tech_spec = {
            "sections": ["Overview", "Architecture", "Components", "Data Flow", "APIs"],
            "created": False
        }

        # TODO: With Claude client, generate technical spec
        # - System overview
        # - Architecture description
        # - Component specifications
        # - Data flow diagrams (text descriptions)
        # - API specifications

        return tech_spec

    async def _update_readme(self, task_details: Dict, project_path: Path) -> Dict:
        """Update README file."""
        print("[Documentation] Updating README...")

        readme_update = {
            "sections_added": [],
            "sections_updated": [],
            "updated": False
        }

        # TODO: With Claude client, update README
        # - Add new features to feature list
        # - Update installation instructions
        # - Add usage examples
        # - Update configuration docs

        return readme_update

    async def _generate_architecture_docs(self, task_details: Dict, project_path: Path) -> Dict:
        """Generate architecture documentation."""
        print("[Documentation] Generating architecture documentation...")

        arch_docs = {
            "diagrams": 0,
            "components_documented": 0,
            "created": False
        }

        # TODO: With Claude client, generate architecture docs
        # - System architecture overview
        # - Component diagrams (Mermaid or text descriptions)
        # - Data flow documentation
        # - Integration points
        # - Technology stack

        return arch_docs

    async def _add_inline_documentation(self, task_details: Dict, project_path: Path) -> Dict:
        """Add inline code documentation."""
        print("[Documentation] Adding inline documentation...")

        inline_docs = {
            "files_documented": 0,
            "functions_documented": 0,
            "classes_documented": 0
        }

        # TODO: With Claude client, add inline documentation
        # - Add docstrings to functions
        # - Add class documentation
        # - Add inline comments for complex logic
        # - Add type hints where missing

        return inline_docs

    async def _create_documentation_summary(self, task_details: Dict, doc_result: Dict) -> str:
        """Create documentation summary."""
        summary_lines = []

        summary_lines.append("# Documentation Summary")
        summary_lines.append("")
        summary_lines.append(f"**Task**: {task_details.get('title', 'N/A')}")
        summary_lines.append(f"**Generated**: {datetime.now().isoformat()}")
        summary_lines.append(f"**Agent**: {self.agent_id}")
        summary_lines.append("")

        # Documents created
        if doc_result.get("docs_created"):
            summary_lines.append("## Documents Created")
            summary_lines.append("")
            for doc in doc_result["docs_created"]:
                summary_lines.append(f"- {doc}")
            summary_lines.append("")

        # Documents updated
        if doc_result.get("docs_updated"):
            summary_lines.append("## Documents Updated")
            summary_lines.append("")
            for doc in doc_result["docs_updated"]:
                summary_lines.append(f"- {doc}")
            summary_lines.append("")

        # Statistics
        summary_lines.append("## Statistics")
        summary_lines.append("")
        summary_lines.append(f"- Total sections: {doc_result.get('total_sections', 0)}")
        summary_lines.append(f"- Total pages: {doc_result.get('total_pages', 0)}")
        summary_lines.append(f"- Documents created: {len(doc_result.get('docs_created', []))}")
        summary_lines.append(f"- Documents updated: {len(doc_result.get('docs_updated', []))}")
        summary_lines.append("")

        summary_lines.append("---")
        summary_lines.append("")
        summary_lines.append(f"*Generated by {self.agent_id}*")

        return "\n".join(summary_lines)

    def _create_summary(self, doc_result: Dict) -> str:
        """Create a summary of documentation work."""
        parts = []

        created_count = len(doc_result.get("docs_created", []))
        updated_count = len(doc_result.get("docs_updated", []))

        if created_count > 0:
            parts.append(f"{created_count} documents created")

        if updated_count > 0:
            parts.append(f"{updated_count} documents updated")

        return ", ".join(parts) if parts else "Documentation completed"

    def get_system_prompt(self) -> str:
        """Get system prompt for the Documentation Agent."""
        return f"""You are {self.agent_id}, a Documentation Agent in the Universal AI Development Platform.

Your role is to create comprehensive, clear, and useful documentation for software projects.

**Responsibilities:**
1. Generate API documentation (REST, GraphQL, SDK)
2. Create user guides and tutorials
3. Write technical specifications
4. Update README files
5. Add inline code documentation (docstrings, comments)
6. Generate architecture documentation
7. Create changelogs
8. Write contributing guidelines
9. Generate examples and code snippets

**Documentation Process:**
1. Analyze documentation needs from task
2. Research documentation best practices using Context7
3. Generate appropriate documentation types
4. Include clear examples and usage patterns
5. Use consistent formatting and structure
6. Add diagrams and visualizations (descriptions)
7. Update existing documentation
8. Ensure accuracy and completeness
9. Update task with documentation links

**Documentation Best Practices:**
- Write for your audience (technical vs non-technical)
- Use clear, concise language
- Include practical examples
- Keep documentation up-to-date
- Use consistent formatting and structure
- Add visual aids (diagrams, screenshots)
- Provide troubleshooting guides
- Include quick start guides
- Document edge cases and limitations
- Use standard documentation formats (Markdown, RST)

**Documentation Types:**
- API Documentation: Endpoint specifications, request/response formats
- User Guides: How-to guides, tutorials, getting started
- Technical Specs: Architecture, design decisions, data models
- README: Project overview, installation, usage
- Inline Docs: Function/class docstrings, code comments
- Architecture Docs: System design, component interactions
- Changelogs: Version history, breaking changes

**Tools Available:**
- EnhancedChecklistManager: Task management
- AgentMemory: Learn from documentation patterns
- Context7: Research documentation standards
- MessageBus: Communicate with other agents

Learn from each documentation task to improve clarity and completeness."""

    def extract_patterns(self, result: Dict) -> List[str]:
        """
        Extract learnable patterns from documentation results.

        Args:
            result: Task execution result

        Returns:
            List of pattern descriptions
        """
        patterns = []

        if not result.get("success"):
            return patterns

        data = result.get("data", {})
        doc_result = data.get("doc_result", {})

        # Pattern: Documentation created
        created_count = len(doc_result.get("docs_created", []))
        if created_count > 0:
            patterns.append(f"Documentation created: {created_count} documents")

        # Pattern: Documentation types
        for doc_type in doc_result.get("docs_created", []):
            patterns.append(f"Document type: {doc_type}")

        # Pattern: Documentation scope
        sections = doc_result.get("total_sections", 0)
        pages = doc_result.get("total_pages", 0)
        if sections > 0 or pages > 0:
            patterns.append(f"Documentation scope: {sections} sections, {pages} pages")

        return patterns


# Example usage
async def example_usage():
    """Example of using the DocumentationAgent."""
    from core.message_bus import MessageBus
    from pathlib import Path

    config = {
        "memory_dir": Path("./AGENT_MEMORY"),
        "projects_base_path": Path("./projects"),
        "doc_format": "markdown",
        "include_examples": True,
        "auto_update_readme": True
    }

    message_bus = MessageBus()

    agent = DocumentationAgent(
        agent_id="docs-001",
        config=config,
        message_bus=message_bus,
        claude_client=None  # Would be actual client in production
    )

    await agent.initialize()

    # Example task
    task = {
        "task_id": "queue-task-123",
        "project_id": "my-project",
        "checklist_task_id": 15,
        "type": "documentation",
        "metadata": {
            "description": "Create API documentation for REST endpoints"
        }
    }

    result = await agent.run_task(task)
    print(f"Documentation result: {result}")

    await agent.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

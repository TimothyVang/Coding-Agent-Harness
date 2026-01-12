"""
Integration Tests for Phase 4 Agents
=====================================

Tests the DevOpsAgent, DocumentationAgent, ReporterAgent, and AnalyticsAgent functionality.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.devops_agent import DevOpsAgent
from agents.documentation_agent import DocumentationAgent
from agents.reporter_agent import ReporterAgent
from agents.analytics_agent import AnalyticsAgent
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus


async def test_devops_agent_initialization():
    """Test that DevOpsAgent initializes correctly."""
    print("\n" + "="*60)
    print("TEST: DevOps Agent Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
            "use_containers": True,
            "enable_monitoring": True
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = DevOpsAgent(
            agent_id="devops-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent.initialize()

        assert agent.agent_id == "devops-test-001"
        assert agent.agent_type == "devops"
        assert agent.status == "idle"
        assert agent.use_containers == True

        print("[PASS] DevOps agent initialized successfully")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Use containers: {agent.use_containers}")
        print(f"   Enable monitoring: {agent.enable_monitoring}")

        await agent.cleanup()


async def test_documentation_agent_initialization():
    """Test that DocumentationAgent initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Documentation Agent Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
            "doc_format": "markdown",
            "include_examples": True
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = DocumentationAgent(
            agent_id="docs-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent.initialize()

        assert agent.agent_id == "docs-test-001"
        assert agent.agent_type == "documentation"
        assert agent.status == "idle"
        assert agent.doc_format == "markdown"

        print("[PASS] Documentation agent initialized successfully")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Format: {agent.doc_format}")
        print(f"   Include examples: {agent.include_examples}")

        await agent.cleanup()


async def test_reporter_agent_initialization():
    """Test that ReporterAgent initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Reporter Agent Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
            "report_format": "markdown",
            "include_recommendations": True
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = ReporterAgent(
            agent_id="reporter-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent.initialize()

        assert agent.agent_id == "reporter-test-001"
        assert agent.agent_type == "reporter"
        assert agent.status == "idle"
        assert agent.report_format == "markdown"

        print("[PASS] Reporter agent initialized successfully")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Format: {agent.report_format}")
        print(f"   Include recommendations: {agent.include_recommendations}")

        await agent.cleanup()


async def test_analytics_agent_initialization():
    """Test that AnalyticsAgent initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Analytics Agent Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
            "lookback_days": 30,
            "min_pattern_frequency": 3
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = AnalyticsAgent(
            agent_id="analytics-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent.initialize()

        assert agent.agent_id == "analytics-test-001"
        assert agent.agent_type == "analytics"
        assert agent.status == "idle"
        assert agent.lookback_days == 30

        print("[PASS] Analytics agent initialized successfully")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Lookback period: {agent.lookback_days} days")
        print(f"   Pattern threshold: {agent.min_pattern_frequency}")

        await agent.cleanup()


async def test_devops_infrastructure_analysis():
    """Test that DevOps can analyze infrastructure needs."""
    print("\n" + "="*60)
    print("TEST: DevOps Agent - Infrastructure Analysis")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects"
        }

        agent = DevOpsAgent(
            agent_id="devops-test-002",
            config=config,
            message_bus=None,
            claude_client=None
        )

        await agent.initialize()

        # Test case 1: Docker containerization
        task1 = {
            "title": "Set up Docker containers",
            "description": "Create Docker configuration for the application",
            "category": "infrastructure"
        }
        project_path = temp_path / "test-project"
        project_path.mkdir(parents=True)
        needs1 = await agent._analyze_infrastructure_needs(task1, project_path)
        print(f"[PASS] Container needs detected: {needs1.get('needs_containers')}")
        assert needs1.get("needs_containers") == True

        # Test case 2: CI/CD pipeline
        task2 = {
            "title": "Set up GitHub Actions CI/CD",
            "description": "Create automated deployment pipeline",
            "category": "devops"
        }
        needs2 = await agent._analyze_infrastructure_needs(task2, project_path)
        print(f"[PASS] CI/CD needs detected: {needs2.get('needs_cicd')}")
        assert needs2.get("needs_cicd") == True

        # Test case 3: Cloud deployment
        task3 = {
            "title": "Deploy to AWS Lambda",
            "description": "Set up serverless deployment",
            "category": "deployment"
        }
        needs3 = await agent._analyze_infrastructure_needs(task3, project_path)
        print(f"[PASS] Cloud needs detected: {needs3.get('needs_cloud')}")
        assert needs3.get("needs_cloud") == True
        assert needs3.get("platform") == "aws"

        await agent.cleanup()


async def test_documentation_needs_analysis():
    """Test that Documentation can analyze documentation needs."""
    print("\n" + "="*60)
    print("TEST: Documentation Agent - Needs Analysis")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects"
        }

        agent = DocumentationAgent(
            agent_id="docs-test-002",
            config=config,
            message_bus=None,
            claude_client=None
        )

        await agent.initialize()

        project_path = temp_path / "test-project"
        project_path.mkdir(parents=True)

        # Test case 1: API documentation
        task1 = {
            "title": "Document REST API endpoints",
            "description": "Create API documentation",
            "category": "documentation"
        }
        needs1 = await agent._analyze_documentation_needs(task1, project_path)
        print(f"[PASS] API docs needed: {needs1.get('needs_api_docs')}")
        assert needs1.get("needs_api_docs") == True

        # Test case 2: User guide
        task2 = {
            "title": "Write getting started guide",
            "description": "Create user guide for new users",
            "category": "documentation"
        }
        needs2 = await agent._analyze_documentation_needs(task2, project_path)
        print(f"[PASS] User guide needed: {needs2.get('needs_user_guide')}")
        assert needs2.get("needs_user_guide") == True

        # Test case 3: README update
        task3 = {
            "title": "Update README with new features",
            "description": "Add installation and setup instructions",
            "category": "documentation"
        }
        needs3 = await agent._analyze_documentation_needs(task3, project_path)
        print(f"[PASS] README update needed: {needs3.get('needs_readme_update')}")
        assert needs3.get("needs_readme_update") == True

        await agent.cleanup()


async def test_reporter_report_type_determination():
    """Test that Reporter can determine report type."""
    print("\n" + "="*60)
    print("TEST: Reporter Agent - Report Type Determination")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects"
        }

        agent = ReporterAgent(
            agent_id="reporter-test-002",
            config=config,
            message_bus=None,
            claude_client=None
        )

        await agent.initialize()

        # Test case 1: Sprint summary
        task1 = {"title": "Generate sprint summary report", "description": "Summarize sprint achievements"}
        type1 = await agent._determine_report_type(task1)
        print(f"[PASS] Sprint report type: {type1}")
        assert type1 == "sprint_summary"

        # Test case 2: Quality metrics
        task2 = {"title": "Quality metrics report", "description": "Analyze code quality"}
        type2 = await agent._determine_report_type(task2)
        print(f"[PASS] Quality report type: {type2}")
        assert type2 == "quality_metrics"

        # Test case 3: Project status (default)
        task3 = {"title": "Status update", "description": "Overall project status"}
        type3 = await agent._determine_report_type(task3)
        print(f"[PASS] Status report type: {type3}")
        assert type3 == "project_status"

        await agent.cleanup()


async def test_analytics_pattern_identification():
    """Test that Analytics can identify patterns."""
    print("\n" + "="*60)
    print("TEST: Analytics Agent - Pattern Identification")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects"
        }

        agent = AnalyticsAgent(
            agent_id="analytics-test-002",
            config=config,
            message_bus=None,
            claude_client=None
        )

        await agent.initialize()

        # Create mock analytics data
        analytics_data = {
            "task_data": {
                "tasks": [
                    {"status": "Done", "category": "feature"},
                    {"status": "Done", "category": "feature"},
                    {"status": "Done", "category": "bugfix"},
                    {"status": "In Progress", "category": "feature"},
                    {"status": "Todo", "category": "documentation"}
                ],
                "total": 5,
                "by_category": {
                    "feature": 3,
                    "bugfix": 1,
                    "documentation": 1
                }
            }
        }

        # Test pattern identification
        patterns = await agent._identify_task_patterns(analytics_data)
        print(f"[PASS] Patterns identified: {len(patterns.get('patterns', []))}")
        print(f"[PASS] Common categories: {patterns.get('common_categories', [])}")
        assert "feature" in patterns.get("common_categories", [])

        await agent.cleanup()


async def test_all_agents_system_prompts():
    """Test that all Phase 4 agents have proper system prompts."""
    print("\n" + "="*60)
    print("TEST: Phase 4 Agents - System Prompts")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects"
        }

        agents_to_test = [
            (DevOpsAgent, "devops-test-003", ["DevOps Agent", "infrastructure", "deployment"]),
            (DocumentationAgent, "docs-test-003", ["Documentation Agent", "documentation", "api"]),
            (ReporterAgent, "reporter-test-003", ["Reporter Agent", "report", "status"]),
            (AnalyticsAgent, "analytics-test-003", ["Analytics Agent", "pattern", "insights"])
        ]

        for AgentClass, agent_id, keywords in agents_to_test:
            agent = AgentClass(
                agent_id=agent_id,
                config=config,
                message_bus=None,
                claude_client=None
            )

            await agent.initialize()

            prompt = agent.get_system_prompt()

            print(f"\n[PASS] {AgentClass.__name__} system prompt generated")
            print(f"   Length: {len(prompt)} characters")

            # Verify key elements
            for keyword in keywords:
                assert keyword.lower() in prompt.lower(), f"Missing keyword: {keyword}"

            print(f"[PASS] {AgentClass.__name__} prompt contains all required elements")

            await agent.cleanup()


async def run_all_tests():
    """Run all integration tests."""
    print("\n" + "#"*60)
    print("# PHASE 4 AGENTS INTEGRATION TESTS")
    print("#"*60)

    tests = [
        ("DevOps Initialization", test_devops_agent_initialization),
        ("Documentation Initialization", test_documentation_agent_initialization),
        ("Reporter Initialization", test_reporter_agent_initialization),
        ("Analytics Initialization", test_analytics_agent_initialization),
        ("DevOps Infrastructure Analysis", test_devops_infrastructure_analysis),
        ("Documentation Needs Analysis", test_documentation_needs_analysis),
        ("Reporter Type Determination", test_reporter_report_type_determination),
        ("Analytics Pattern Identification", test_analytics_pattern_identification),
        ("System Prompts", test_all_agents_system_prompts),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            await test_func()
            results.append((test_name, "PASSED", None))
        except Exception as e:
            results.append((test_name, "FAILED", str(e)))
            import traceback
            traceback.print_exc()

    # Print summary
    print("\n" + "#"*60)
    print("# TEST SUMMARY")
    print("#"*60)

    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")

    for test_name, status, error in results:
        symbol = "[PASS]" if status == "PASSED" else "[FAIL]"
        print(f"{symbol} {test_name}: {status}")
        if error:
            print(f"   Error: {error}")

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[WARN]  {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

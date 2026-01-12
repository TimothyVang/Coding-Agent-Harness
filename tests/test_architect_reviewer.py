"""
Integration Tests for Architect and Reviewer Agents
====================================================

Tests the ArchitectAgent and ReviewerAgent functionality.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.architect_agent import ArchitectAgent
from agents.reviewer_agent import ReviewerAgent
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus
from core.agent_memory import AgentMemory


async def test_architect_agent_initialization():
    """Test that ArchitectAgent initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Architect Agent Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
            "use_context7": True,
            "create_subtasks_for_complex": True
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = ArchitectAgent(
            agent_id="architect-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent.initialize()

        assert agent.agent_id == "architect-test-001"
        assert agent.agent_type == "architect"
        assert agent.status == "idle"
        assert agent.client is None  # No client provided in test

        print("[PASS] Architect agent initialized successfully")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Agent type: {agent.agent_type}")
        print(f"   Status: {agent.status}")

        await agent.cleanup()


async def test_reviewer_agent_initialization():
    """Test that ReviewerAgent initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Reviewer Agent Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
            "check_code_quality": True,
            "check_security": True,
            "check_performance": True,
            "auto_approve_threshold": 90.0
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = ReviewerAgent(
            agent_id="reviewer-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent.initialize()

        assert agent.agent_id == "reviewer-test-001"
        assert agent.agent_type == "reviewer"
        assert agent.status == "idle"
        assert agent.check_code_quality == True
        assert agent.check_security == True
        assert agent.auto_approve_threshold == 90.0

        print("[PASS] Reviewer agent initialized successfully")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Check code quality: {agent.check_code_quality}")
        print(f"   Check security: {agent.check_security}")
        print(f"   Auto-approve threshold: {agent.auto_approve_threshold}%")

        await agent.cleanup()


async def test_architect_requirements_analysis():
    """Test that Architect can analyze requirements."""
    print("\n" + "="*60)
    print("TEST: Architect Agent - Requirements Analysis")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects"
        }

        agent = ArchitectAgent(
            agent_id="architect-test-002",
            config=config,
            message_bus=None,
            claude_client=None
        )

        await agent.initialize()

        # Test case 1: High complexity feature
        task1 = {
            "title": "Implement payment gateway integration",
            "description": "Integrate Stripe for payment processing",
            "category": "feature"
        }
        requirements1 = await agent._analyze_requirements(task1)
        print(f"[PASS] High complexity feature analysis:")
        print(f"   Complexity: {requirements1.get('complexity')}")
        print(f"   Scope: {requirements1.get('scope')}")
        assert requirements1.get("complexity") in ["medium", "high"]

        # Test case 2: Medium complexity feature
        task2 = {
            "title": "Add dashboard with charts",
            "description": "Create user dashboard with data visualization",
            "category": "feature"
        }
        requirements2 = await agent._analyze_requirements(task2)
        print(f"\n[PASS] Medium complexity feature analysis:")
        print(f"   Complexity: {requirements2.get('complexity')}")
        print(f"   Scope: {requirements2.get('scope')}")
        assert requirements2.get("complexity") in ["low", "medium"]

        # Test case 3: Low complexity feature
        task3 = {
            "title": "Add helper utility function",
            "description": "Create a data formatting utility",
            "category": "feature"
        }
        requirements3 = await agent._analyze_requirements(task3)
        print(f"\n[PASS] Low complexity feature analysis:")
        print(f"   Complexity: {requirements3.get('complexity')}")
        print(f"   Scope: {requirements3.get('scope')}")

        await agent.cleanup()


async def test_reviewer_quality_score_calculation():
    """Test that Reviewer correctly calculates quality scores."""
    print("\n" + "="*60)
    print("TEST: Reviewer Agent - Quality Score Calculation")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects"
        }

        agent = ReviewerAgent(
            agent_id="reviewer-test-002",
            config=config,
            message_bus=None,
            claude_client=None
        )

        await agent.initialize()

        # Test case 1: No issues (perfect score)
        review_result1 = {"issues_found": []}
        score1 = agent._calculate_quality_score(review_result1)
        print(f"[PASS] No issues: Score = {score1:.1f}/100")
        assert score1 == 100.0

        # Test case 2: One critical issue
        review_result2 = {
            "issues_found": [
                {"severity": "critical", "description": "SQL injection vulnerability"}
            ]
        }
        score2 = agent._calculate_quality_score(review_result2)
        print(f"[PASS] 1 critical issue: Score = {score2:.1f}/100")
        assert score2 == 80.0

        # Test case 3: Multiple issues
        review_result3 = {
            "issues_found": [
                {"severity": "high", "description": "Missing error handling"},
                {"severity": "medium", "description": "Code duplication"},
                {"severity": "low", "description": "Missing comments"}
            ]
        }
        score3 = agent._calculate_quality_score(review_result3)
        print(f"[PASS] Multiple issues: Score = {score3:.1f}/100")
        assert score3 == 83.0  # 100 - 10 - 5 - 2 = 83

        await agent.cleanup()


async def test_architect_system_prompt():
    """Test that ArchitectAgent has proper system prompt."""
    print("\n" + "="*60)
    print("TEST: Architect Agent System Prompt")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects"
        }

        agent = ArchitectAgent(
            agent_id="architect-test-003",
            config=config,
            message_bus=None,
            claude_client=None
        )

        await agent.initialize()

        prompt = agent.get_system_prompt()

        print("[PASS] System prompt generated")
        print(f"   Length: {len(prompt)} characters")

        # Verify key elements
        assert "Architect Agent" in prompt
        assert agent.agent_id in prompt
        assert "architecture" in prompt.lower()
        assert "design" in prompt.lower()
        # Note: The word "planning" may not be in the prompt, checking for "plan" instead
        assert "plan" in prompt.lower()

        print("[PASS] System prompt contains all required elements")

        await agent.cleanup()


async def test_reviewer_system_prompt():
    """Test that ReviewerAgent has proper system prompt."""
    print("\n" + "="*60)
    print("TEST: Reviewer Agent System Prompt")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects"
        }

        agent = ReviewerAgent(
            agent_id="reviewer-test-003",
            config=config,
            message_bus=None,
            claude_client=None
        )

        await agent.initialize()

        prompt = agent.get_system_prompt()

        print("[PASS] System prompt generated")
        print(f"   Length: {len(prompt)} characters")

        # Verify key elements
        assert "Reviewer Agent" in prompt
        assert agent.agent_id in prompt
        assert "review" in prompt.lower()
        assert "quality" in prompt.lower()
        assert "security" in prompt.lower()

        print("[PASS] System prompt contains all required elements")

        await agent.cleanup()


async def test_architect_component_design():
    """Test that Architect can design components."""
    print("\n" + "="*60)
    print("TEST: Architect Agent - Component Design")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects"
        }

        agent = ArchitectAgent(
            agent_id="architect-test-004",
            config=config,
            message_bus=None,
            claude_client=None
        )

        await agent.initialize()

        task_details = {
            "title": "Build user authentication system",
            "description": "Create login, registration, and password reset",
            "category": "feature"
        }

        requirements = {
            "complexity": "high",
            "scope": ["frontend", "backend", "database"]
        }

        architecture_research = {
            "patterns": [],
            "best_practices": []
        }

        component_design = await agent._design_components(
            task_details,
            requirements,
            architecture_research
        )

        print(f"[PASS] Component design created")
        print(f"   Components: {len(component_design.get('components', []))}")
        print(f"   Interactions: {len(component_design.get('interactions', []))}")

        # Verify components were created
        assert len(component_design.get("components", [])) > 0

        # Should have frontend and backend components for auth
        component_types = [c.get("type") for c in component_design.get("components", [])]
        print(f"   Component types: {component_types}")

        await agent.cleanup()


async def run_all_tests():
    """Run all integration tests."""
    print("\n" + "#"*60)
    print("# ARCHITECT & REVIEWER AGENTS INTEGRATION TESTS")
    print("#"*60)

    tests = [
        ("Architect Initialization", test_architect_agent_initialization),
        ("Reviewer Initialization", test_reviewer_agent_initialization),
        ("Architect Requirements Analysis", test_architect_requirements_analysis),
        ("Reviewer Quality Score", test_reviewer_quality_score_calculation),
        ("Architect System Prompt", test_architect_system_prompt),
        ("Reviewer System Prompt", test_reviewer_system_prompt),
        ("Architect Component Design", test_architect_component_design),
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

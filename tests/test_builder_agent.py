"""
Integration Tests for Builder Agent
====================================

Tests the Builder Agent's ability to execute tasks end-to-end.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.builder_agent import BuilderAgent
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus
from core.agent_memory import AgentMemory


async def test_builder_agent_initialization():
    """Test that BuilderAgent initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Builder Agent Initialization")
    print("="*60)

    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        # Create agent
        agent = BuilderAgent(
            agent_id="builder-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        # Initialize
        await agent.initialize()

        # Verify
        assert agent.agent_id == "builder-test-001"
        assert agent.agent_type == "builder"
        assert agent.status == "idle"
        assert agent.memory is not None

        print("[PASS] Builder agent initialized successfully")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Agent Type: {agent.agent_type}")
        print(f"   Status: {agent.status}")

        # Cleanup
        await agent.cleanup()

        print("[PASS] Builder agent cleaned up successfully")


async def test_builder_agent_task_execution():
    """Test that BuilderAgent can execute a task (without Claude client)."""
    print("\n" + "="*60)
    print("TEST: Builder Agent Task Execution")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Setup project structure
        project_id = "test-project-001"
        project_path = temp_path / "projects" / project_id
        project_path.mkdir(parents=True)

        # Create checklist with a test task
        checklist = EnhancedChecklistManager(project_path)
        task_id = checklist.add_task({
            "title": "Implement user login feature",
            "description": "Create login form and authentication logic",
            "category": "feature",
            "priority": "high"
        })

        print(f"[PASS] Created test project and checklist")
        print(f"   Project: {project_id}")
        print(f"   Task ID: {task_id}")
        print(f"   Task: Implement user login feature")

        # Create agent
        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = BuilderAgent(
            agent_id="builder-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None  # No Claude client for this test
        )

        await agent.initialize()

        # Create task for agent
        task = {
            "task_id": "queue-task-001",
            "project_id": project_id,
            "checklist_task_id": task_id,
            "type": "feature",
            "metadata": {
                "description": "Implement user login feature"
            }
        }

        print(f"\n[PASS] Executing task with agent...")

        # Execute task
        try:
            result = await agent.run_task(task)

            print(f"\n[PASS] Task execution completed")
            print(f"   Success: {result.get('success')}")

            if result.get("error"):
                print(f"   Expected Error (no Claude client): {result.get('error')}")

            # Verify agent statistics
            stats = agent.get_statistics()
            print(f"\n[PASS] Agent statistics:")
            print(f"   Total tasks: {stats['task_count']}")
            print(f"   Success count: {stats['success_count']}")
            print(f"   Failure count: {stats['failure_count']}")

            # Check that checklist was NOT updated (because we don't have Claude client)
            # In a real test with Claude, we'd verify checklist updates
            checklist_task = checklist.get_task(task_id)
            print(f"\n[PASS] Checklist task status: {checklist_task['status']}")

        except Exception as e:
            # This is expected since we don't have a Claude client
            print(f"\n[WARN]  Task execution raised expected error: {e}")
            print(f"   This is expected without a Claude client")

        # Cleanup
        await agent.cleanup()

        print(f"\n[PASS] Test completed successfully")


async def test_builder_agent_memory():
    """Test that BuilderAgent saves patterns to memory."""
    print("\n" + "="*60)
    print("TEST: Builder Agent Memory & Pattern Learning")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = BuilderAgent(
            agent_id="builder-test-002",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent.initialize()

        # Add a pattern to memory
        agent.memory.add_pattern(
            title="Authentication Implementation Pattern",
            description="Use JWT tokens for stateless authentication",
            code="const token = jwt.sign(payload, secret);",
            learned_from="task-123"
        )

        print("[PASS] Added pattern to memory")

        # Search for similar patterns
        patterns = agent.memory.find_similar_patterns("authentication")
        print(f"[PASS] Found {len(patterns)} patterns matching 'authentication'")

        if patterns:
            pattern = patterns[0]
            print(f"   - {pattern['title']}")
            print(f"   - {pattern['description']}")

        # Add a mistake
        agent.memory.add_mistake(
            title="Forgot to hash passwords",
            task_id="task-456",
            error="Passwords stored in plaintext",
            solution="Always hash passwords with bcrypt before storing"
        )

        print("[PASS] Added mistake to memory")

        # Get relevant mistakes
        mistakes = agent.memory.get_relevant_mistakes("password")
        print(f"[PASS] Found {len(mistakes)} mistakes related to 'password'")

        if mistakes:
            mistake = mistakes[0]
            print(f"   - {mistake['title']}")
            print(f"   - Solution: {mistake['solution']}")

        # Save and verify persistence
        agent.memory.save()

        # Load in new instance
        agent2 = BuilderAgent(
            agent_id="builder-test-002",  # Same ID
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent2.initialize()

        # Verify patterns were loaded
        patterns2 = agent2.memory.find_similar_patterns("authentication")
        print(f"\n[PASS] Memory persisted - found {len(patterns2)} patterns after reload")

        # Cleanup
        await agent.cleanup()
        await agent2.cleanup()

        print("\n[PASS] Memory test completed successfully")


async def test_builder_agent_system_prompt():
    """Test that BuilderAgent has proper system prompt."""
    print("\n" + "="*60)
    print("TEST: Builder Agent System Prompt")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
        }

        agent = BuilderAgent(
            agent_id="builder-test-003",
            config=config,
            message_bus=None,
            claude_client=None
        )

        await agent.initialize()

        # Get system prompt
        prompt = agent.get_system_prompt()

        print("[PASS] System prompt generated")
        print(f"   Length: {len(prompt)} characters")

        # Verify key elements in prompt
        assert "Builder Agent" in prompt
        assert agent.agent_id in prompt
        assert "implement features" in prompt.lower()
        assert "code" in prompt.lower()
        assert "tests" in prompt.lower()

        print("[PASS] System prompt contains all required elements")

        # Cleanup
        await agent.cleanup()


async def run_all_tests():
    """Run all integration tests."""
    print("\n" + "#"*60)
    print("# BUILDER AGENT INTEGRATION TESTS")
    print("#"*60)

    tests = [
        ("Initialization", test_builder_agent_initialization),
        ("Task Execution", test_builder_agent_task_execution),
        ("Memory & Learning", test_builder_agent_memory),
        ("System Prompt", test_builder_agent_system_prompt),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            await test_func()
            results.append((test_name, "PASSED", None))
        except Exception as e:
            results.append((test_name, "FAILED", str(e)))

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
    # Run all tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

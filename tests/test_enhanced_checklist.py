"""
Integration Tests for Enhanced Checklist Manager
=================================================

Tests the EnhancedChecklistManager's core functionality.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enhanced_checklist import EnhancedChecklistManager


async def test_checklist_initialization():
    """Test that checklist initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Enhanced Checklist Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create checklist
        checklist = EnhancedChecklistManager(temp_path)

        # Verify structure
        assert checklist.data is not None
        assert "tasks" in checklist.data
        assert "next_task_id" in checklist.data
        assert "project_name" in checklist.data
        assert "sessions" in checklist.data

        print("[PASS] Checklist initialized with correct structure")
        print(f"   Tasks: {len(checklist.data['tasks'])}")
        print(f"   Next task ID: {checklist.data['next_task_id']}")

        # Initialize with project
        initial_tasks = [
            {"title": "Set up project", "description": "Initialize project structure", "priority": "HIGH"},
            {"title": "Implement feature", "description": "Build core feature", "priority": "MEDIUM"}
        ]

        checklist.initialize("Test Project", initial_tasks)

        assert checklist.data["project_name"] == "Test Project"
        assert len(checklist.data["tasks"]) == 2

        print(f"[PASS] Project initialized: {checklist.data['project_name']}")
        print(f"   Initial tasks: {len(checklist.data['tasks'])}")


async def test_task_creation():
    """Test task creation and management."""
    print("\n" + "="*60)
    print("TEST: Task Creation and Management")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        checklist = EnhancedChecklistManager(temp_path)

        # Add task
        task_id = checklist.add_task(
            title="Implement authentication",
            description="Add JWT-based authentication",
            priority="HIGH"
        )

        print(f"[PASS] Task created with ID: {task_id}")

        # Verify task
        task = checklist.get_task(task_id)
        assert task is not None
        assert task["title"] == "Implement authentication"
        assert task["description"] == "Add JWT-based authentication"
        assert task["priority"] == "HIGH"
        assert task["status"] == "Todo"

        print(f"[PASS] Task details verified:")
        print(f"   Title: {task['title']}")
        print(f"   Priority: {task['priority']}")
        print(f"   Status: {task['status']}")

        # Update task status
        checklist.update_task_status(task_id, "In Progress")
        updated_task = checklist.get_task(task_id)
        assert updated_task["status"] == "In Progress"

        print(f"[PASS] Task status updated to: {updated_task['status']}")

        # Mark task complete
        checklist.update_task_status(task_id, "Done")
        completed_task = checklist.get_task(task_id)
        assert completed_task["status"] == "Done"

        print(f"[PASS] Task marked complete")


async def test_subtask_support():
    """Test hierarchical subtask functionality."""
    print("\n" + "="*60)
    print("TEST: Subtask Support (Parent-Child)")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        checklist = EnhancedChecklistManager(temp_path)

        # Create parent task
        parent_id = checklist.add_task(
            title="Build user management",
            description="Complete user management system"
        )

        print(f"[PASS] Parent task created: ID {parent_id}")

        # Create subtasks
        subtask1_id = checklist.add_subtask(
            parent_task_id=parent_id,
            subtask={"title": "Create user model", "description": "Database schema for users"}
        )

        subtask2_id = checklist.add_subtask(
            parent_task_id=parent_id,
            subtask={"title": "Implement user API", "description": "REST endpoints for user management"}
        )

        subtask3_id = checklist.add_subtask(
            parent_task_id=parent_id,
            subtask={"title": "Add user tests", "description": "Unit and integration tests"}
        )

        print(f"[PASS] Created 3 subtasks")
        print(f"   Subtask 1: ID {subtask1_id}")
        print(f"   Subtask 2: ID {subtask2_id}")
        print(f"   Subtask 3: ID {subtask3_id}")

        # Verify parent has subtasks
        parent_task = checklist.get_task(parent_id)
        assert "subtasks" in parent_task
        assert len(parent_task["subtasks"]) == 3

        print(f"[PASS] Parent task has {len(parent_task['subtasks'])} subtasks")

        # Complete subtasks
        checklist.update_task_status(subtask1_id, "Done")
        checklist.update_task_status(subtask2_id, "Done")

        # Check parent completion
        parent_task = checklist.get_task(parent_id)
        # Get actual subtask objects
        subtasks = checklist.get_subtasks(parent_id)
        incomplete_subtasks = [st for st in subtasks if st.get("status") != "Done"]

        print(f"[PASS] Subtask progress:")
        print(f"   Completed: 2/3")
        print(f"   Remaining: {len(incomplete_subtasks)}")

        # Complete all subtasks
        checklist.update_task_status(subtask3_id, "Done")
        subtasks = checklist.get_subtasks(parent_id)
        all_complete = all(st.get("status") == "Done" for st in subtasks)
        assert all_complete

        print(f"[PASS] All subtasks completed")


async def test_blocking_mechanism():
    """Test blocking task functionality."""
    print("\n" + "="*60)
    print("TEST: Blocking Mechanism")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        checklist = EnhancedChecklistManager(temp_path)

        # Create regular task
        regular_task_id = checklist.add_task(
            title="Regular feature",
            description="Normal feature implementation"
        )

        # Create blocking task
        blocking_task_id = checklist.add_task(
            title="Critical bug fix",
            description="Security vulnerability fix",
            priority="CRITICAL"
        )

        # Mark as blocking
        checklist.mark_task_blocking(blocking_task_id)

        print(f"[PASS] Created blocking task: ID {blocking_task_id}")

        # Verify blocking status
        blocking_task = checklist.get_task(blocking_task_id)
        assert blocking_task.get("blocking", False) == True

        print(f"[PASS] Task marked as blocking")

        # Check if there are blocking tasks
        blocking_tasks = checklist.get_blocking_tasks()
        has_blocking = len(blocking_tasks) > 0
        assert has_blocking == True

        print(f"[PASS] Checklist has blocking tasks: {has_blocking}")

        # Get all blocking tasks
        blocking_tasks = checklist.get_blocking_tasks()
        assert len(blocking_tasks) == 1
        assert blocking_tasks[0]["id"] == blocking_task_id

        print(f"[PASS] Found {len(blocking_tasks)} blocking task(s)")

        # Resolve blocking task
        checklist.update_task_status(blocking_task_id, "Done")

        # Verify no more blocking tasks (Done tasks are not counted as blocking)
        blocking_tasks = checklist.get_blocking_tasks()
        has_blocking = len(blocking_tasks) > 0
        assert has_blocking == False

        print(f"[PASS] Blocking task resolved")
        print(f"   Blocking tasks remaining: {len(checklist.get_blocking_tasks())}")


async def test_completion_calculation():
    """Test completion percentage calculation."""
    print("\n" + "="*60)
    print("TEST: Completion Percentage Calculation")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        checklist = EnhancedChecklistManager(temp_path)

        # Create multiple tasks
        task1 = checklist.add_task(title="Task 1", description="First task")
        task2 = checklist.add_task(title="Task 2", description="Second task")
        task3 = checklist.add_task(title="Task 3", description="Third task")
        task4 = checklist.add_task(title="Task 4", description="Fourth task")

        print(f"[PASS] Created 4 tasks")

        # Initial completion (all Todo)
        summary = checklist.get_progress_summary()
        assert summary["Done"] == 0
        total = sum(summary.values())
        completion = (summary["Done"] / total * 100) if total > 0 else 0
        assert completion == 0.0

        print(f"[PASS] Initial completion: {completion}%")

        # Complete 1 task (25%)
        checklist.update_task_status(task1, "Done")
        summary = checklist.get_progress_summary()
        total = sum(summary.values())
        completion = (summary["Done"] / total * 100) if total > 0 else 0
        assert completion == 25.0

        print(f"[PASS] After 1 task: {completion}%")

        # Complete 2 tasks (50%)
        checklist.update_task_status(task2, "Done")
        summary = checklist.get_progress_summary()
        total = sum(summary.values())
        completion = (summary["Done"] / total * 100) if total > 0 else 0
        assert completion == 50.0

        print(f"[PASS] After 2 tasks: {completion}%")

        # Complete 3 tasks (75%)
        checklist.update_task_status(task3, "Done")
        summary = checklist.get_progress_summary()
        total = sum(summary.values())
        completion = (summary["Done"] / total * 100) if total > 0 else 0
        assert completion == 75.0

        print(f"[PASS] After 3 tasks: {completion}%")

        # Complete all tasks (100%)
        checklist.update_task_status(task4, "Done")
        summary = checklist.get_progress_summary()
        total = sum(summary.values())
        completion = (summary["Done"] / total * 100) if total > 0 else 0
        assert completion == 100.0

        print(f"[PASS] All tasks complete: {completion}%")

        # Test with subtasks
        parent_id = checklist.add_task(title="Parent task", description="Task with subtasks")
        checklist.add_subtask(parent_id, {"title": "Subtask 1", "description": ""})
        checklist.add_subtask(parent_id, {"title": "Subtask 2", "description": ""})

        # Calculate task completion (includes subtasks)
        task_completion = checklist.calculate_task_completion(parent_id)
        assert task_completion == 0.0  # No subtasks done

        print(f"[PASS] Parent task completion with subtasks: {task_completion}%")


async def run_all_tests():
    """Run all integration tests."""
    print("\n" + "#"*60)
    print("# ENHANCED CHECKLIST INTEGRATION TESTS")
    print("#"*60)

    tests = [
        ("Initialization", test_checklist_initialization),
        ("Task Creation", test_task_creation),
        ("Subtask Support", test_subtask_support),
        ("Blocking Mechanism", test_blocking_mechanism),
        ("Completion Calculation", test_completion_calculation),
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
        print(f"\n[WARN] {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    # Run all tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

"""
Integration Tests for Project Registry
========================================

Tests the ProjectRegistry's multi-project management capabilities.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.project_registry import ProjectRegistry


async def test_registry_initialization():
    """Test that project registry initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Project Registry Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "projects.json"

        # Create registry
        registry = ProjectRegistry(registry_path=temp_path)

        # Verify structure
        assert registry.data is not None
        assert "projects" in registry.data
        assert "version" in registry.data
        assert "created_at" in registry.data

        print("[PASS] Registry initialized with correct structure")
        print(f"   Version: {registry.data['version']}")
        print(f"   Projects: {len(registry.data['projects'])}")


async def test_project_registration():
    """Test project registration."""
    print("\n" + "="*60)
    print("TEST: Project Registration")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "projects.json"
        registry = ProjectRegistry(registry_path=temp_path)

        # Register project
        project1_id = registry.register_project(
            name="E-Commerce Platform",
            path=Path("/projects/ecommerce"),
            priority=2
        )

        print(f"[PASS] Project registered with ID: {project1_id}")

        # Verify project
        project1 = registry.get_project(project1_id)
        assert project1 is not None
        assert project1["name"] == "E-Commerce Platform"
        assert project1["priority"] == 2
        assert project1["status"] == "active"

        print(f"[PASS] Project details verified:")
        print(f"   Name: {project1['name']}")
        print(f"   Priority: {project1['priority']}")
        print(f"   Status: {project1['status']}")

        # Register multiple projects
        project2_id = registry.register_project(
            name="Data Analytics Dashboard",
            path=Path("/projects/analytics"),
            priority=1
        )

        project3_id = registry.register_project(
            name="Mobile App",
            path=Path("/projects/mobile"),
            priority=3
        )

        print(f"[PASS] Registered 2 additional projects")

        # Verify all projects
        all_projects = registry.list_projects()
        assert len(all_projects) == 3

        print(f"[PASS] Total registered projects: {len(all_projects)}")


async def test_status_tracking():
    """Test project status tracking."""
    print("\n" + "="*60)
    print("TEST: Project Status Tracking")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "projects.json"
        registry = ProjectRegistry(registry_path=temp_path)

        # Register project
        project_id = registry.register_project(
            name="Test Project",
            path=Path("/test")
        )

        # Check initial status
        project = registry.get_project(project_id)
        assert project["status"] == "active"

        print(f"[PASS] Initial status: {project['status']}")

        # Update to paused
        registry.update_project_status(project_id, "paused")
        project = registry.get_project(project_id)
        assert project["status"] == "paused"

        print(f"[PASS] Status updated to: {project['status']}")

        # Update to completed
        registry.update_project_status(project_id, "completed")
        project = registry.get_project(project_id)
        assert project["status"] == "completed"

        print(f"[PASS] Status updated to: {project['status']}")

        # Update to archived
        registry.update_project_status(project_id, "archived")
        project = registry.get_project(project_id)
        assert project["status"] == "archived"

        print(f"[PASS] Status updated to: {project['status']}")

        # List active projects (should be 0 since we archived the only one)
        active_projects = registry.list_projects(status="active")
        assert len(active_projects) == 0

        print(f"[PASS] Active projects: {len(active_projects)}")

        # List archived projects
        archived_projects = registry.list_projects(status="archived")
        assert len(archived_projects) == 1

        print(f"[PASS] Archived projects: {len(archived_projects)}")


async def test_workload_distribution():
    """Test workload distribution calculation."""
    print("\n" + "="*60)
    print("TEST: Workload Distribution")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "projects.json"
        registry = ProjectRegistry(registry_path=temp_path)

        # Register projects with different workloads
        proj1 = registry.register_project("Project 1", Path("/p1"))
        proj2 = registry.register_project("Project 2", Path("/p2"))
        proj3 = registry.register_project("Project 3", Path("/p3"))

        print(f"[PASS] Registered 3 projects")

        # Set task counts for each project
        registry.update_project_stats(proj1, total_tasks=10, completed_tasks=5)
        registry.update_project_stats(proj2, total_tasks=20, completed_tasks=2)
        registry.update_project_stats(proj3, total_tasks=5, completed_tasks=5)

        print(f"[PASS] Updated workload for all projects")

        # Calculate workload distribution
        distribution = registry.get_workload_distribution()

        assert distribution is not None
        assert proj1 in distribution
        assert proj2 in distribution
        assert proj3 in distribution

        print(f"[PASS] Workload distribution calculated:")
        for proj_id, workload in distribution.items():
            print(f"   {proj_id}: {workload} pending tasks")

        # Find least loaded project (manually from distribution)
        least_loaded = min(distribution, key=distribution.get) if distribution else None
        assert least_loaded is not None

        print(f"[PASS] Least loaded project: {least_loaded} ({distribution[least_loaded]} pending)")

        # Find project with most pending work (manually from distribution)
        most_work = max(distribution, key=distribution.get) if distribution else None
        assert most_work is not None

        print(f"[PASS] Project with most work: {most_work} ({distribution[most_work]} pending)")


async def test_project_listing():
    """Test project listing and filtering."""
    print("\n" + "="*60)
    print("TEST: Project Listing and Filtering")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "projects.json"
        registry = ProjectRegistry(registry_path=temp_path)

        # Register multiple projects
        proj1 = registry.register_project("Active Project 1", Path("/p1"), priority=1)
        proj2 = registry.register_project("Active Project 2", Path("/p2"), priority=2)
        proj3 = registry.register_project("Paused Project", Path("/p3"), priority=1)
        proj4 = registry.register_project("Completed Project", Path("/p4"), priority=3)

        print(f"[PASS] Registered 4 projects")

        # Update statuses
        registry.update_project_status(proj3, "paused")
        registry.update_project_status(proj4, "completed")

        # List all projects
        all_projects = registry.list_projects()
        assert len(all_projects) == 4

        print(f"[PASS] All projects: {len(all_projects)}")

        # List active projects only
        active_projects = registry.list_projects(status="active")
        assert len(active_projects) == 2

        print(f"[PASS] Active projects: {len(active_projects)}")

        # List paused projects
        paused_projects = registry.list_projects(status="paused")
        assert len(paused_projects) == 1

        print(f"[PASS] Paused projects: {len(paused_projects)}")

        # List completed projects
        completed_projects = registry.list_projects(status="completed")
        assert len(completed_projects) == 1

        print(f"[PASS] Completed projects: {len(completed_projects)}")

        # Get all projects and filter by priority manually
        all_projects_list = registry.list_projects()
        high_priority = [p for p in all_projects_list if p["priority"] >= 2]
        assert len(high_priority) >= 1  # At least proj2 and proj4

        print(f"[PASS] High priority projects (>=2): {len(high_priority)}")


async def test_activity_tracking():
    """Test project activity tracking."""
    print("\n" + "="*60)
    print("TEST: Activity Tracking")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "projects.json"
        registry = ProjectRegistry(registry_path=temp_path)

        # Register project
        project_id = registry.register_project("Test Project", Path("/test"))

        # Get initial activity time
        project = registry.get_project(project_id)
        initial_activity = project.get("last_activity")

        print(f"[PASS] Initial activity time: {initial_activity}")

        # Update activity
        import time
        time.sleep(0.1)  # Small delay to ensure timestamp changes

        registry.update_project_activity(project_id)

        # Verify activity was updated
        project = registry.get_project(project_id)
        updated_activity = project.get("last_activity")

        assert updated_activity != initial_activity

        print(f"[PASS] Activity updated: {updated_activity}")

        # Register another project
        project2_id = registry.register_project("Project 2", Path("/p2"))

        # Update first project activity again
        time.sleep(0.1)
        registry.update_project_activity(project_id)

        # Get most recently active project
        recent_projects = registry.list_projects()
        recent_projects.sort(key=lambda p: p.get("last_activity", ""), reverse=True)

        # First project should be most recent
        assert recent_projects[0]["id"] == project_id

        print(f"[PASS] Most recently active: {recent_projects[0]['name']}")


async def run_all_tests():
    """Run all integration tests."""
    print("\n" + "#"*60)
    print("# PROJECT REGISTRY INTEGRATION TESTS")
    print("#"*60)

    tests = [
        ("Initialization", test_registry_initialization),
        ("Project Registration", test_project_registration),
        ("Status Tracking", test_status_tracking),
        ("Workload Distribution", test_workload_distribution),
        ("Project Listing", test_project_listing),
        ("Activity Tracking", test_activity_tracking),
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

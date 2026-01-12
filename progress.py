"""
Progress Tracking Utilities
===========================

Functions for tracking and displaying progress of the autonomous coding agent.
Progress is tracked via local checklist system (.project_checklist.json).
"""

from pathlib import Path
from checklist_manager import ChecklistManager, CHECKLIST_FILE


def is_checklist_initialized(project_dir: Path) -> bool:
    """
    Check if project checklist has been initialized.

    Args:
        project_dir: Directory to check

    Returns:
        True if checklist exists and is initialized
    """
    checklist_path = project_dir / CHECKLIST_FILE
    if not checklist_path.exists():
        return False

    manager = ChecklistManager(project_dir)
    return manager.is_initialized()


def print_session_header(session_num: int, is_initializer: bool) -> None:
    """Print a formatted header for the session."""
    session_type = "INITIALIZER" if is_initializer else "CODING AGENT"

    print("\n" + "=" * 70)
    print(f"  SESSION {session_num}: {session_type}")
    print("=" * 70)
    print()


def print_progress_summary(project_dir: Path) -> None:
    """
    Print a summary of current progress from the local checklist.
    """
    if not is_checklist_initialized(project_dir):
        print("\nProgress: Checklist not yet initialized")
        return

    manager = ChecklistManager(project_dir)
    summary = manager.get_progress_summary()
    total_tasks = sum(summary.values())

    print(f"\nProject Checklist Status:")
    print(f"  Total tasks: {total_tasks}")
    print(f"  ✓ Done: {summary['Done']}")
    print(f"  ⚙ In Progress: {summary['In Progress']}")
    print(f"  ☐ Todo: {summary['Todo']}")

    # Show next task if available
    next_task = manager.get_next_task()
    if next_task:
        print(f"\n  Next task: #{next_task['id']} - {next_task['title']}")


def print_checklist_table(project_dir: Path) -> None:
    """
    Print a detailed table of all tasks in the checklist.
    """
    if not is_checklist_initialized(project_dir):
        print("Checklist not initialized yet.")
        return

    manager = ChecklistManager(project_dir)
    tasks = manager.get_all_tasks()

    if not tasks:
        print("No tasks in checklist.")
        return

    print("\n" + "=" * 100)
    print("PROJECT TASK CHECKLIST")
    print("=" * 100)
    print(f"{'ID':<4} {'Status':<15} {'Title':<60} {'Notes':<15}")
    print("-" * 100)

    for task in tasks:
        task_id = f"#{task['id']}"
        status_emoji = {
            'Done': '✓',
            'In Progress': '⚙',
            'Todo': '☐'
        }.get(task['status'], '?')
        status = f"{status_emoji} {task['status']}"
        title = task['title'][:58] + "..." if len(task['title']) > 58 else task['title']
        notes_count = len(task['notes'])
        notes = f"{notes_count} note(s)" if notes_count > 0 else ""

        print(f"{task_id:<4} {status:<15} {title:<60} {notes:<15}")

    print("-" * 100)
    print()

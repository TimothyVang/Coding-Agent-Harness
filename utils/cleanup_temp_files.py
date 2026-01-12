"""
Automated Temporary File Cleanup Utility
=========================================

Removes leftover tmpclaude-* files and other temp artifacts from the project directory.
These files are created by Claude Code SDK sessions and can accumulate over time.
"""

import os
import glob
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List


def cleanup_temp_files(
    project_dir: Path,
    patterns: List[str],
    older_than_hours: int = 24,
    dry_run: bool = False
) -> Dict:
    """
    Clean up temporary files matching specified patterns.

    Args:
        project_dir: Root project directory to search in
        patterns: List of glob patterns (e.g., ['tmpclaude-*', '*.tmp'])
        older_than_hours: Only delete files older than this many hours
        dry_run: If True, report what would be deleted without actually deleting

    Returns:
        Dictionary with cleanup results:
        {
            "deleted": int,           # Number of files successfully deleted
            "failed": int,            # Number of files that failed to delete
            "skipped": int,           # Number of files skipped (too recent)
            "freed_bytes": int,       # Total bytes freed
            "files": List[str]        # List of deleted file paths
        }
    """
    deleted = 0
    failed = 0
    skipped = 0
    freed_bytes = 0
    deleted_files = []

    cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

    print(f"[Cleanup] Scanning for temporary files in: {project_dir}")
    print(f"[Cleanup] Patterns: {patterns}")
    print(f"[Cleanup] Deleting files older than {older_than_hours} hours "
          f"(before {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')})")

    if dry_run:
        print("[Cleanup] DRY RUN MODE - No files will be deleted")

    for pattern in patterns:
        # Search in project directory only (not recursive)
        search_pattern = str(project_dir / pattern)

        for file_path_str in glob.glob(search_pattern):
            file_path = Path(file_path_str)

            # Skip directories
            if file_path.is_dir():
                continue

            try:
                file_stat = os.stat(file_path)
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                file_size = file_stat.st_size

                # Check if file is old enough to delete
                if file_time >= cutoff_time:
                    skipped += 1
                    continue

                # Delete file (or simulate in dry run mode)
                if dry_run:
                    print(f"[Cleanup] Would delete: {file_path.name} "
                          f"({file_size} bytes, modified {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
                    deleted += 1
                    freed_bytes += file_size
                    deleted_files.append(str(file_path))
                else:
                    os.remove(file_path)
                    deleted += 1
                    freed_bytes += file_size
                    deleted_files.append(str(file_path))

            except PermissionError as e:
                print(f"[Cleanup] Permission denied: {file_path.name} - {e}")
                failed += 1
            except FileNotFoundError:
                # File was deleted between glob and removal - not an error
                pass
            except Exception as e:
                print(f"[Cleanup] Failed to delete {file_path.name}: {e}")
                failed += 1

    # Print summary
    print(f"\n[Cleanup] Summary:")
    print(f"  - Deleted: {deleted} files")
    print(f"  - Failed: {failed} files")
    print(f"  - Skipped (too recent): {skipped} files")
    print(f"  - Space freed: {freed_bytes:,} bytes ({freed_bytes / 1024:.2f} KB)")

    return {
        "deleted": deleted,
        "failed": failed,
        "skipped": skipped,
        "freed_bytes": freed_bytes,
        "files": deleted_files
    }


def cleanup_claude_tmp_files(project_dir: Path = None, dry_run: bool = False) -> Dict:
    """
    Convenience function to clean up Claude-specific temporary files.

    Args:
        project_dir: Root project directory (defaults to current working directory)
        dry_run: If True, report what would be deleted without actually deleting

    Returns:
        Dictionary with cleanup results
    """
    if project_dir is None:
        project_dir = Path.cwd()

    patterns = [
        "tmpclaude-*-cwd",
        "tmpclaude-*",
        "*.tmp"
    ]

    return cleanup_temp_files(
        project_dir=project_dir,
        patterns=patterns,
        older_than_hours=24,
        dry_run=dry_run
    )


def main():
    """Command-line interface for cleanup utility."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up temporary files from Claude Code SDK sessions"
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory to clean (default: current directory)"
    )
    parser.add_argument(
        "--pattern",
        action="append",
        dest="patterns",
        help="File pattern to match (can be specified multiple times)"
    )
    parser.add_argument(
        "--older-than",
        type=int,
        default=24,
        help="Only delete files older than this many hours (default: 24)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )

    args = parser.parse_args()

    # Use default Claude temp patterns if none specified
    patterns = args.patterns or ["tmpclaude-*-cwd", "tmpclaude-*", "*.tmp"]

    result = cleanup_temp_files(
        project_dir=args.project_dir,
        patterns=patterns,
        older_than_hours=args.older_than,
        dry_run=args.dry_run
    )

    # Exit with error code if any failures occurred
    return 1 if result["failed"] > 0 else 0


if __name__ == "__main__":
    exit(main())

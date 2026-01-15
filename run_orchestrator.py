#!/usr/bin/env python3
"""
Orchestrator Launcher for Rust-DFIR
====================================

Launches the multi-agent orchestrator with E2B sandbox protection.

Usage:
    python run_orchestrator.py

Environment Requirements:
    - E2B_API_KEY in .env (required for sandbox execution)
    - CLAUDE_CODE_OAUTH_TOKEN in .env (required for Claude SDK)
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def main():
    """Launch the orchestrator with Rust-DFIR project."""
    print("\n" + "=" * 60)
    print("  RUST-DFIR MULTI-AGENT ORCHESTRATOR")
    print("=" * 60)

    # Import after dotenv load
    from orchestrator import AgentOrchestrator

    # Configuration
    project_name = "Rust-DFIR"
    project_path = Path(r"C:\Users\newbi\Desktop\PUG Projects\Rust-DFIR")
    spec_file = Path(__file__).parent / "prompts" / "dfir_spec.txt"

    # Validate paths
    if not project_path.exists():
        print(f"[ERROR] Project path not found: {project_path}")
        return 1

    if not spec_file.exists():
        print(f"[ERROR] Spec file not found: {spec_file}")
        return 1

    print(f"\nProject: {project_name}")
    print(f"Path: {project_path}")
    print(f"Spec: {spec_file}")
    print("\nSecurity: E2B sandbox ENABLED (Fix 1)")
    print("         Shell injection protected (Fix 2)")
    print("         File locking enabled (Fix 5)")
    print("\n" + "-" * 60)

    # Create and configure orchestrator
    orchestrator = AgentOrchestrator()

    project_id = orchestrator.register_project(
        name=project_name,
        path=project_path,
        spec_file=spec_file,
        priority=1
    )

    print(f"\nRegistered project ID: {project_id}")
    print("\nStarting orchestrator...")
    print("Press Ctrl+C to stop\n")
    print("=" * 60 + "\n")

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        print("\n\nShutting down orchestrator...")
        await orchestrator.stop()
        print("Orchestrator stopped.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)

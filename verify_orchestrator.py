"""
Verification Script for Orchestrator Integration
=================================================

Verifies that all 12 agents are properly integrated into the orchestrator.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import AgentOrchestrator


async def verify_orchestrator():
    """Verify orchestrator has all 12 agents."""
    print("\n" + "="*70)
    print("ORCHESTRATOR INTEGRATION VERIFICATION")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
            "max_concurrent_agents": 12
        }

        # Create orchestrator
        print("\n[1/3] Creating orchestrator...")
        orchestrator = AgentOrchestrator(config=config)

        # Initialize agent pool
        print("[2/3] Initializing agent pool...")
        await orchestrator._initialize_agent_pool()

        # Verify all agents
        print("[3/3] Verifying agents...")

        expected_agent_types = [
            "architect", "builder", "test_generator", "verifier", "reviewer",
            "devops", "documentation", "reporter", "analytics",
            "refactor", "database", "ui_design"
        ]

        print(f"\n   Expected agent types: {len(expected_agent_types)}")
        print(f"   Registered agents: {len(orchestrator.agents)}")

        # Check each expected type
        agent_types_found = set()
        for agent_id, agent in orchestrator.agents.items():
            agent_types_found.add(agent.agent_type)
            print(f"   [OK] {agent_id}: {agent.agent_type} (status: {agent.status})")

        # Verify all types present
        missing_types = set(expected_agent_types) - agent_types_found
        extra_types = agent_types_found - set(expected_agent_types)

        print("\n" + "="*70)
        print("VERIFICATION RESULTS")
        print("="*70)

        if not missing_types and not extra_types:
            print("[SUCCESS] All 12 agent types are properly integrated!")
            print(f"   - Total agents: {len(orchestrator.agents)}")
            print(f"   - All expected types present: {len(agent_types_found)}")
            print(f"   - Agent types available: {', '.join(sorted(agent_types_found))}")
            success = True
        else:
            print("[FAILURE] Agent integration issues detected")
            if missing_types:
                print(f"   - Missing types: {', '.join(missing_types)}")
            if extra_types:
                print(f"   - Extra types: {', '.join(extra_types)}")
            success = False

        print("="*70)

        # Cleanup
        await orchestrator.stop()

        return success


if __name__ == "__main__":
    success = asyncio.run(verify_orchestrator())
    sys.exit(0 if success else 1)

"""
Integration Tests for Phase 5 Agents
=====================================

Tests the RefactorAgent, DatabaseAgent, and UIDesignAgent functionality.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.refactor_agent import RefactorAgent
from agents.database_agent import DatabaseAgent
from agents.ui_design_agent import UIDesignAgent
from core.enhanced_checklist import EnhancedChecklistManager
from core.message_bus import MessageBus


async def test_refactor_agent_initialization():
    """Test that RefactorAgent initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Refactor Agent Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
            "complexity_threshold": 10,
            "function_length_threshold": 50,
            "enable_auto_refactor": False
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = RefactorAgent(
            agent_id="refactor-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent.initialize()

        assert agent.agent_id == "refactor-test-001"
        assert agent.agent_type == "refactor"
        assert agent.status == "idle"
        assert agent.complexity_threshold == 10
        assert agent.function_length_threshold == 50

        print("[PASS] Refactor agent initialized successfully")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Complexity threshold: {agent.complexity_threshold}")
        print(f"   Function length threshold: {agent.function_length_threshold}")

        await agent.cleanup()


async def test_refactor_agent_system_prompt():
    """Test that RefactorAgent generates proper system prompt."""
    print("\n" + "="*60)
    print("TEST: Refactor Agent System Prompt")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "complexity_threshold": 10,
            "function_length_threshold": 50
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = RefactorAgent(
            agent_id="refactor-test-002",
            config=config,
            message_bus=message_bus
        )

        await agent.initialize()
        prompt = agent.get_system_prompt()

        assert "RefactorAgent" in prompt or "refactor-test-002" in prompt
        assert "code quality" in prompt.lower() or "refactor" in prompt.lower()
        assert "complexity" in prompt.lower()

        print("[PASS] Refactor agent system prompt generated correctly")
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Contains 'complexity': {('complexity' in prompt.lower())}")

        await agent.cleanup()


async def test_database_agent_initialization():
    """Test that DatabaseAgent initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Database Agent Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
            "supported_databases": ["postgresql", "mysql", "mongodb"],
            "enable_normalization": True,
            "enable_indexes": True
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = DatabaseAgent(
            agent_id="database-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent.initialize()

        assert agent.agent_id == "database-test-001"
        assert agent.agent_type == "database"
        assert agent.status == "idle"
        assert "postgresql" in agent.supported_databases
        assert agent.enable_normalization_checks == True

        print("[PASS] Database agent initialized successfully")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Supported databases: {len(agent.supported_databases)}")
        print(f"   Normalization enabled: {agent.enable_normalization_checks}")

        await agent.cleanup()


async def test_database_agent_system_prompt():
    """Test that DatabaseAgent generates proper system prompt."""
    print("\n" + "="*60)
    print("TEST: Database Agent System Prompt")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "supported_databases": ["postgresql", "mysql"]
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = DatabaseAgent(
            agent_id="database-test-002",
            config=config,
            message_bus=message_bus
        )

        await agent.initialize()
        prompt = agent.get_system_prompt()

        assert "DatabaseAgent" in prompt or "database-test-002" in prompt
        assert "schema" in prompt.lower() or "database" in prompt.lower()
        assert "postgresql" in prompt.lower() or "mysql" in prompt.lower()

        print("[PASS] Database agent system prompt generated correctly")
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Contains 'schema': {('schema' in prompt.lower())}")

        await agent.cleanup()


async def test_ui_design_agent_initialization():
    """Test that UIDesignAgent initializes correctly."""
    print("\n" + "="*60)
    print("TEST: UI Design Agent Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "projects_base_path": temp_path / "projects",
            "supported_frameworks": ["react", "vue", "angular"],
            "wcag_level": "AA",
            "enable_playwright": True
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = UIDesignAgent(
            agent_id="uidesign-test-001",
            config=config,
            message_bus=message_bus,
            claude_client=None
        )

        await agent.initialize()

        assert agent.agent_id == "uidesign-test-001"
        assert agent.agent_type == "ui_design"
        assert agent.status == "idle"
        assert "react" in agent.supported_frameworks
        assert agent.wcag_level == "AA"
        assert agent.enable_playwright == True

        print("[PASS] UI Design agent initialized successfully")
        print(f"   Agent ID: {agent.agent_id}")
        print(f"   Supported frameworks: {len(agent.supported_frameworks)}")
        print(f"   WCAG level: {agent.wcag_level}")
        print(f"   Playwright enabled: {agent.enable_playwright}")

        await agent.cleanup()


async def test_ui_design_agent_system_prompt():
    """Test that UIDesignAgent generates proper system prompt."""
    print("\n" + "="*60)
    print("TEST: UI Design Agent System Prompt")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "wcag_level": "AA",
            "supported_frameworks": ["react", "vue"]
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = UIDesignAgent(
            agent_id="uidesign-test-002",
            config=config,
            message_bus=message_bus
        )

        await agent.initialize()
        prompt = agent.get_system_prompt()

        assert "UIDesignAgent" in prompt or "uidesign-test-002" in prompt
        assert "accessibility" in prompt.lower() or "wcag" in prompt.lower()
        assert "react" in prompt.lower() or "vue" in prompt.lower()

        print("[PASS] UI Design agent system prompt generated correctly")
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Contains 'accessibility': {('accessibility' in prompt.lower())}")

        await agent.cleanup()


async def test_refactor_agent_code_smell_detection():
    """Test RefactorAgent can extract functions from code."""
    print("\n" + "="*60)
    print("TEST: Refactor Agent Code Smell Detection")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
            "function_length_threshold": 5  # Low threshold for testing
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = RefactorAgent(
            agent_id="refactor-test-003",
            config=config,
            message_bus=message_bus
        )

        await agent.initialize()

        # Test code with a long function
        test_code = """
def long_function():
    # Line 1
    # Line 2
    # Line 3
    # Line 4
    # Line 5
    # Line 6
    # Line 7
    # Line 8
    # Line 9
    # Line 10
    pass
"""

        functions = agent._extract_functions(test_code, "python")

        assert len(functions) >= 1
        assert any(f["name"] == "long_function" for f in functions)

        print("[PASS] Refactor agent code smell detection works")
        print(f"   Functions found: {len(functions)}")
        print(f"   Test function detected: {any(f['name'] == 'long_function' for f in functions)}")

        await agent.cleanup()


async def test_database_agent_orm_detection():
    """Test DatabaseAgent can detect database configurations."""
    print("\n" + "="*60)
    print("TEST: Database Agent ORM Detection")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = DatabaseAgent(
            agent_id="database-test-003",
            config=config,
            message_bus=message_bus
        )

        await agent.initialize()

        # Create fake Prisma schema
        project_path = temp_path / "test_project"
        project_path.mkdir(exist_ok=True)
        prisma_dir = project_path / "prisma"
        prisma_dir.mkdir(exist_ok=True)

        prisma_schema = prisma_dir / "schema.prisma"
        prisma_schema.write_text("""
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id Int @id @default(autoincrement())
  name String
}
""", encoding='utf-8')

        db_config = await agent._detect_database_config(project_path)

        assert db_config["orm"] == "prisma"
        assert db_config["database_type"] == "postgresql"
        assert len(db_config["schema_files"]) > 0

        print("[PASS] Database agent ORM detection works")
        print(f"   ORM detected: {db_config['orm']}")
        print(f"   Database type: {db_config['database_type']}")
        print(f"   Schema files found: {len(db_config['schema_files'])}")

        await agent.cleanup()


async def test_ui_design_agent_framework_detection():
    """Test UIDesignAgent can detect UI frameworks."""
    print("\n" + "="*60)
    print("TEST: UI Design Agent Framework Detection")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        config = {
            "memory_dir": temp_path / "memory",
        }

        message_bus = MessageBus(bus_path=temp_path / "messages")

        agent = UIDesignAgent(
            agent_id="uidesign-test-003",
            config=config,
            message_bus=message_bus
        )

        await agent.initialize()

        # Create fake React project
        project_path = temp_path / "test_project"
        project_path.mkdir(exist_ok=True)

        package_json = project_path / "package.json"
        package_json.write_text("""
{
  "name": "test-project",
  "dependencies": {
    "react": "^18.0.0",
    "tailwindcss": "^3.0.0"
  }
}
""", encoding='utf-8')

        ui_config = await agent._detect_ui_framework(project_path)

        assert ui_config["framework"] == "react"
        assert ui_config["styling"] == "tailwind"

        print("[PASS] UI Design agent framework detection works")
        print(f"   Framework detected: {ui_config['framework']}")
        print(f"   Styling detected: {ui_config['styling']}")

        await agent.cleanup()


async def run_all_tests():
    """Run all Phase 5 agent tests."""
    print("\n" + "="*70)
    print("RUNNING PHASE 5 AGENTS TEST SUITE")
    print("Testing: RefactorAgent, DatabaseAgent, UIDesignAgent")
    print("="*70)

    test_functions = [
        # Refactor Agent Tests
        test_refactor_agent_initialization,
        test_refactor_agent_system_prompt,
        test_refactor_agent_code_smell_detection,

        # Database Agent Tests
        test_database_agent_initialization,
        test_database_agent_system_prompt,
        test_database_agent_orm_detection,

        # UI Design Agent Tests
        test_ui_design_agent_initialization,
        test_ui_design_agent_system_prompt,
        test_ui_design_agent_framework_detection,
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            await test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test_func.__name__}: {e}")
            failed += 1

    print("\n" + "="*70)
    print("PHASE 5 AGENTS TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    print("="*70)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

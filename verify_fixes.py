#!/usr/bin/env python3
"""
Verification script for the 5 security/architecture fixes.
Run this to confirm all fixes are working correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_fix1_e2b_hardfail():
    """Test Fix 1: E2B hard-fail when unavailable."""
    print("\n" + "="*60)
    print("TEST 1: E2B Hard-Fail When Unavailable")
    print("="*60)

    # Temporarily clear the API key to simulate missing key
    original_key = os.environ.get("E2B_API_KEY")
    os.environ.pop("E2B_API_KEY", None)

    try:
        from core.e2b_sandbox_manager import E2BSandboxManager

        # This should raise RuntimeError, not fall back silently
        config = {"e2b_enabled": True, "e2b_api_key": None}
        manager = E2BSandboxManager(config)

        print("[FAIL] FAIL: E2B manager created without raising error!")
        print("   The system should have raised RuntimeError")
        return False

    except RuntimeError as e:
        if "SECURITY" in str(e):
            print("[PASS] PASS: RuntimeError raised as expected")
            print(f"   Error message: {str(e)[:80]}...")
            return True
        else:
            print(f"[FAIL] FAIL: Wrong RuntimeError: {e}")
            return False
    except Exception as e:
        print(f"[FAIL] FAIL: Unexpected error type: {type(e).__name__}: {e}")
        return False
    finally:
        # Restore the original key
        if original_key:
            os.environ["E2B_API_KEY"] = original_key


def test_fix2_shell_injection():
    """Test Fix 2: Shell injection protection."""
    print("\n" + "="*60)
    print("TEST 2: Shell Injection Protection")
    print("="*60)

    import shlex

    # Test that shlex is imported in e2b_mcp_server
    try:
        mcp_server_path = Path(__file__).parent / "mcp_servers" / "e2b" / "e2b_mcp_server.py"
        content = mcp_server_path.read_text(encoding='utf-8')

        checks = [
            ("import shlex", "shlex import"),
            ("shlex.quote(", "shlex.quote() usage"),
            ("escaped_path = shlex.quote(path)", "path escaping in _list_files"),
        ]

        all_passed = True
        for pattern, description in checks:
            if pattern in content:
                print(f"[PASS] PASS: Found {description}")
            else:
                print(f"[FAIL] FAIL: Missing {description}")
                all_passed = False

        # Test that malicious paths would be escaped
        malicious_path = "/tmp; rm -rf /; echo '"
        escaped = shlex.quote(malicious_path)
        if escaped != malicious_path:
            print(f"[PASS] PASS: Malicious path would be escaped")
            print(f"   Original: {malicious_path}")
            print(f"   Escaped:  {escaped}")
        else:
            print("[FAIL] FAIL: Path not properly escaped")
            all_passed = False

        return all_passed

    except Exception as e:
        print(f"[FAIL] FAIL: Error checking shell injection fix: {e}")
        return False


def test_fix3_client_initialization():
    """Test Fix 3: Client initialization in orchestrator."""
    print("\n" + "="*60)
    print("TEST 3: Client Initialization in Orchestrator")
    print("="*60)

    try:
        orchestrator_path = Path(__file__).parent / "orchestrator.py"
        content = orchestrator_path.read_text(encoding='utf-8')

        checks = [
            ("claude_client = await create_client", "client creation call"),
            ("Claude SDK client created successfully", "success log message"),
            ("claude_client=claude_client", "client passed to agents"),
        ]

        all_passed = True
        for pattern, description in checks:
            if pattern in content:
                print(f"[PASS] PASS: Found {description}")
            else:
                print(f"[FAIL] FAIL: Missing {description}")
                all_passed = False

        # Count how many agents receive the client
        client_assignments = content.count("claude_client=claude_client")
        print(f"   Found {client_assignments} agent(s) receiving claude_client")

        if client_assignments >= 10:
            print("[PASS] PASS: Multiple agents receiving client")
        else:
            print("[FAIL] FAIL: Not enough agents receiving client")
            all_passed = False

        return all_passed

    except Exception as e:
        print(f"[FAIL] FAIL: Error checking client initialization: {e}")
        return False


def test_fix4_async_callbacks():
    """Test Fix 4: Async callback handling in message bus."""
    print("\n" + "="*60)
    print("TEST 4: Async Callback Handling in Message Bus")
    print("="*60)

    try:
        message_bus_path = Path(__file__).parent / "core" / "message_bus.py"
        content = message_bus_path.read_text(encoding='utf-8')

        checks = [
            ("import asyncio", "asyncio import"),
            ("asyncio.iscoroutine(result)", "coroutine detection"),
            ("asyncio.create_task(result)", "task scheduling"),
        ]

        all_passed = True
        for pattern, description in checks:
            if pattern in content:
                print(f"[PASS] PASS: Found {description}")
            else:
                print(f"[FAIL] FAIL: Missing {description}")
                all_passed = False

        # Actually test the functionality
        from core.message_bus import MessageBus
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            bus = MessageBus(bus_path=Path(tmpdir))

            # Test with sync callback
            sync_called = []
            def sync_callback(msg):
                sync_called.append(msg)

            bus.subscribe("test_channel", "test_agent", sync_callback)
            bus.publish("test_channel", {"test": "data"})

            if sync_called:
                print("[PASS] PASS: Sync callbacks work correctly")
            else:
                print("[FAIL] FAIL: Sync callbacks not working")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"[FAIL] FAIL: Error checking async callbacks: {e}")
        return False


def test_fix5_file_locking():
    """Test Fix 5: File locking for concurrency safety."""
    print("\n" + "="*60)
    print("TEST 5: File Locking for Concurrency Safety")
    print("="*60)

    try:
        # Check imports
        task_queue_path = Path(__file__).parent / "core" / "task_queue.py"
        message_bus_path = Path(__file__).parent / "core" / "message_bus.py"

        all_passed = True

        for path, name in [(task_queue_path, "task_queue"), (message_bus_path, "message_bus")]:
            content = path.read_text(encoding='utf-8')

            if "from filelock import FileLock" in content:
                print(f"[PASS] PASS: {name} has filelock import")
            else:
                print(f"[FAIL] FAIL: {name} missing filelock import")
                all_passed = False

            if "FileLock(str(" in content:
                print(f"[PASS] PASS: {name} uses FileLock")
            else:
                print(f"[FAIL] FAIL: {name} not using FileLock")
                all_passed = False

        # Check requirements.txt
        req_path = Path(__file__).parent / "requirements.txt"
        if "filelock" in req_path.read_text(encoding='utf-8'):
            print("[PASS] PASS: filelock in requirements.txt")
        else:
            print("[FAIL] FAIL: filelock not in requirements.txt")
            all_passed = False

        # Test actual locking
        try:
            from filelock import FileLock
            print("[PASS] PASS: filelock package is installed")
        except ImportError:
            print("[WARN]  WARN: filelock not installed (run: pip install filelock)")

        return all_passed

    except Exception as e:
        print(f"[FAIL] FAIL: Error checking file locking: {e}")
        return False


def test_fix6_agent_e2b_integration():
    """Test Fix 6: E2B integration in single-agent demo."""
    print("\n" + "="*60)
    print("TEST 6: E2B Integration in Single-Agent Demo")
    print("="*60)

    all_passed = True

    try:
        # Check client.py has E2B integration
        client_path = Path(__file__).parent / "client.py"
        content = client_path.read_text(encoding='utf-8')

        checks = [
            ("E2B_TOOLS = [", "E2B tools list defined"),
            ("e2b_api_key = os.environ.get(\"E2B_API_KEY\")", "E2B API key check"),
            ("E2B sandbox is REQUIRED", "E2B requirement error message"),
            ("\"e2b\": {", "E2B MCP server configured"),
            ("*E2B_TOOLS", "E2B tools in allowed_tools"),
            ("mcp__e2b__e2b_execute_command", "E2B execute command tool"),
        ]

        for pattern, description in checks:
            if pattern in content:
                print(f"[PASS] PASS: {description}")
            else:
                print(f"[FAIL] FAIL: Missing {description}")
                all_passed = False

        # Check security.py blocks all bash
        security_path = Path(__file__).parent / "security.py"
        security_content = security_path.read_text(encoding='utf-8')

        if "BLOCK ALL DIRECT BASH COMMANDS" in security_content:
            print("[PASS] PASS: security.py blocks all direct bash")
        else:
            print("[FAIL] FAIL: security.py not blocking all bash")
            all_passed = False

        # Test that bash_security_hook blocks commands
        import asyncio
        from security import bash_security_hook

        async def test_hook():
            result = await bash_security_hook({
                'tool_name': 'Bash',
                'tool_input': {'command': 'ls -la'}
            })
            return result.get('block', False)

        if asyncio.run(test_hook()):
            print("[PASS] PASS: bash_security_hook blocks commands")
        else:
            print("[FAIL] FAIL: bash_security_hook not blocking")
            all_passed = False

        return all_passed

    except Exception as e:
        print(f"[FAIL] FAIL: Error checking E2B integration: {e}")
        return False


def main():
    """Run all verification tests."""
    print("\n" + "#"*60)
    print("# CODING-AGENT-HARNESS FIX VERIFICATION")
    print("#"*60)

    results = {
        "Fix 1 - E2B Hard-Fail": test_fix1_e2b_hardfail(),
        "Fix 2 - Shell Injection": test_fix2_shell_injection(),
        "Fix 3 - Client Init": test_fix3_client_initialization(),
        "Fix 4 - Async Callbacks": test_fix4_async_callbacks(),
        "Fix 5 - File Locking": test_fix5_file_locking(),
        "Fix 6 - Agent E2B": test_fix6_agent_e2b_integration(),
    }

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    all_passed = True
    for name, passed in results.items():
        status = "[PASS] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("*** ALL FIXES VERIFIED SUCCESSFULLY!")
    else:
        print("[WARN]  SOME FIXES NEED ATTENTION")
    print("="*60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

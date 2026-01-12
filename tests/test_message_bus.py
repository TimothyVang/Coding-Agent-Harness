"""
Integration Tests for Message Bus
===================================

Tests the MessageBus's pub/sub and direct messaging capabilities.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.message_bus import MessageBus, MessageTypes


async def test_message_bus_initialization():
    """Test that message bus initializes correctly."""
    print("\n" + "="*60)
    print("TEST: Message Bus Initialization")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create message bus
        bus = MessageBus(bus_path=temp_path)

        # Verify structure
        assert bus.data is not None
        assert "messages" in bus.data
        assert "channels" in bus.data
        assert "version" in bus.data

        print("[PASS] Message bus initialized with correct structure")
        print(f"   Version: {bus.data['version']}")
        print(f"   Messages: {len(bus.data['messages'])}")
        print(f"   Channels: {len(bus.data['channels'])}")

        # Verify subscriptions
        assert bus.subscriptions is not None

        print("[PASS] Subscriptions registry initialized")


async def test_publish_subscribe():
    """Test publish/subscribe messaging."""
    print("\n" + "="*60)
    print("TEST: Publish/Subscribe Messaging")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        bus = MessageBus(bus_path=temp_path)

        # Track received messages
        received_messages = []

        def message_callback(message):
            received_messages.append(message)

        # Subscribe to channel
        bus.subscribe("task_updates", "agent-1", message_callback)

        print("[PASS] Agent-1 subscribed to 'task_updates' channel")

        # Publish message
        bus.publish(
            channel="task_updates",
            message={"type": "TASK_COMPLETED", "task_id": "task-001"},
            sender="agent-2"
        )

        print("[PASS] Published message to 'task_updates' channel")

        # Verify message received
        assert len(received_messages) == 1
        assert received_messages[0]["message"]["type"] == "TASK_COMPLETED"
        assert received_messages[0]["message"]["task_id"] == "task-001"

        print(f"[PASS] Message received by subscriber")
        print(f"   Type: {received_messages[0]['message']['type']}")
        print(f"   Sender: {received_messages[0]['sender']}")

        # Multiple subscribers
        received_messages_2 = []

        def message_callback_2(message):
            received_messages_2.append(message)

        bus.subscribe("task_updates", "agent-3", message_callback_2)

        print("[PASS] Agent-3 also subscribed to 'task_updates'")

        # Publish another message
        bus.publish(
            channel="task_updates",
            message={"type": "TASK_FAILED", "task_id": "task-002"},
            sender="agent-4"
        )

        # Both subscribers should receive it
        assert len(received_messages) == 2
        assert len(received_messages_2) == 1

        print(f"[PASS] Message delivered to all subscribers")
        print(f"   Agent-1 received: {len(received_messages)} messages")
        print(f"   Agent-3 received: {len(received_messages_2)} messages")


async def test_direct_messaging():
    """Test direct agent-to-agent messaging."""
    print("\n" + "="*60)
    print("TEST: Direct Messaging")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        bus = MessageBus(bus_path=temp_path)

        # Track received messages
        agent1_messages = []
        agent2_messages = []

        def agent1_callback(message):
            agent1_messages.append(message)

        def agent2_callback(message):
            agent2_messages.append(message)

        # Subscribe to direct channels
        bus.subscribe("direct.agent-1", "agent-1", agent1_callback)
        bus.subscribe("direct.agent-2", "agent-2", agent2_callback)

        print("[PASS] Agents subscribed to direct channels")

        # Send direct message from agent-2 to agent-1
        bus.send_direct(
            recipient="agent-1",
            message={"type": "health_check_request"},
            sender="agent-2"
        )

        print("[PASS] Direct message sent from agent-2 to agent-1")

        # Verify only agent-1 received it
        assert len(agent1_messages) == 1
        assert len(agent2_messages) == 0

        print(f"[PASS] Message delivered only to recipient")
        print(f"   Agent-1 received: {len(agent1_messages)}")
        print(f"   Agent-2 received: {len(agent2_messages)}")

        # Reply from agent-1 to agent-2
        bus.send_direct(
            recipient="agent-2",
            message={"type": "health_check_response", "status": "healthy"},
            sender="agent-1"
        )

        # Now agent-2 should have received the reply
        assert len(agent1_messages) == 1
        assert len(agent2_messages) == 1

        print(f"[PASS] Reply delivered")
        print(f"   Agent-2 reply: {agent2_messages[0]['message']}")


async def test_message_persistence():
    """Test message persistence to disk."""
    print("\n" + "="*60)
    print("TEST: Message Persistence")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create bus and publish messages
        bus1 = MessageBus(bus_path=temp_path)

        bus1.publish(
            channel="notifications",
            message={"type": "agent_started", "agent_id": "builder-1"},
            sender="orchestrator"
        )

        bus1.publish(
            channel="notifications",
            message={"type": "agent_started", "agent_id": "verifier-1"},
            sender="orchestrator"
        )

        print(f"[PASS] Published 2 messages")
        print(f"   Total messages: {len(bus1.data['messages'])}")

        # Close first bus (saves data)
        initial_message_count = len(bus1.data['messages'])
        del bus1

        # Create new bus instance (should load persisted messages)
        bus2 = MessageBus(bus_path=temp_path)

        # Verify messages were loaded
        assert len(bus2.data['messages']) == initial_message_count

        print(f"[PASS] Messages persisted and reloaded")
        print(f"   Reloaded {len(bus2.data['messages'])} messages")

        # Verify message content
        messages = bus2.data['messages']
        assert any(m['message'].get('agent_id') == 'builder-1' for m in messages)
        assert any(m['message'].get('agent_id') == 'verifier-1' for m in messages)

        print(f"[PASS] Message content verified after reload")


async def test_channel_isolation():
    """Test that messages stay within their channels."""
    print("\n" + "="*60)
    print("TEST: Channel Isolation")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        bus = MessageBus(bus_path=temp_path)

        # Track messages by channel
        channel_a_messages = []
        channel_b_messages = []

        def channel_a_callback(message):
            channel_a_messages.append(message)

        def channel_b_callback(message):
            channel_b_messages.append(message)

        # Subscribe to different channels
        bus.subscribe("channel_a", "listener-1", channel_a_callback)
        bus.subscribe("channel_b", "listener-2", channel_b_callback)

        print("[PASS] Subscribed to channel_a and channel_b")

        # Publish to channel_a
        bus.publish(
            channel="channel_a",
            message={"data": "Message for A"},
            sender="sender-1"
        )

        # Publish to channel_b
        bus.publish(
            channel="channel_b",
            message={"data": "Message for B"},
            sender="sender-2"
        )

        # Verify isolation
        assert len(channel_a_messages) == 1
        assert len(channel_b_messages) == 1
        assert channel_a_messages[0]['message']['data'] == "Message for A"
        assert channel_b_messages[0]['message']['data'] == "Message for B"

        print(f"[PASS] Channel isolation verified")
        print(f"   Channel A received: '{channel_a_messages[0]['message']['data']}'")
        print(f"   Channel B received: '{channel_b_messages[0]['message']['data']}'")

        # Publish multiple to one channel
        for i in range(3):
            bus.publish(
                channel="channel_a",
                message={"count": i},
                sender="sender-1"
            )

        # channel_a should have 4 messages, channel_b still 1
        assert len(channel_a_messages) == 4
        assert len(channel_b_messages) == 1

        print(f"[PASS] Multiple messages to one channel")
        print(f"   Channel A: {len(channel_a_messages)} messages")
        print(f"   Channel B: {len(channel_b_messages)} messages")


async def test_message_priority():
    """Test priority message handling."""
    print("\n" + "="*60)
    print("TEST: Message Priority")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        bus = MessageBus(bus_path=temp_path)

        received_messages = []

        def callback(message):
            received_messages.append(message)

        bus.subscribe("alerts", "listener", callback)

        # Publish messages with different priorities
        bus.publish("alerts", {"alert": "low"}, sender="system", priority="LOW")
        bus.publish("alerts", {"alert": "critical"}, sender="system", priority="CRITICAL")
        bus.publish("alerts", {"alert": "high"}, sender="system", priority="HIGH")
        bus.publish("alerts", {"alert": "medium"}, sender="system", priority="MEDIUM")

        print(f"[PASS] Published 4 messages with different priorities")
        print(f"   Total received: {len(received_messages)}")

        # Check messages were received
        assert len(received_messages) == 4

        print(f"[PASS] All priority messages received")

        # Verify all priorities present
        priorities = [msg.get('priority') for msg in received_messages]
        assert "CRITICAL" in priorities
        assert "HIGH" in priorities
        assert "MEDIUM" in priorities
        assert "LOW" in priorities

        print(f"[PASS] All priority levels present: {set(priorities)}")


async def run_all_tests():
    """Run all integration tests."""
    print("\n" + "#"*60)
    print("# MESSAGE BUS INTEGRATION TESTS")
    print("#"*60)

    tests = [
        ("Initialization", test_message_bus_initialization),
        ("Publish/Subscribe", test_publish_subscribe),
        ("Direct Messaging", test_direct_messaging),
        ("Message Persistence", test_message_persistence),
        ("Channel Isolation", test_channel_isolation),
        ("Message Priority", test_message_priority),
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

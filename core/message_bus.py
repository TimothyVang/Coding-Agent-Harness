"""
Message Bus System
==================

Inter-agent communication system for coordination and information sharing.

Features:
- Publish/subscribe messaging
- Direct agent-to-agent messaging
- Channel-based communication
- Message persistence
- Message history and replay
- Support for various message types
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional


class MessageBus:
    """
    Message bus for inter-agent communication.

    Supports:
    - Publish/subscribe pattern on named channels
    - Direct messaging to specific agents
    - Message persistence (file-based)
    - Message history and replay
    - Callback-based subscription

    Can be extended to use Redis or database for production.
    """

    def __init__(self, bus_path: Optional[Path] = None, mode: str = "file"):
        """
        Initialize message bus.

        Args:
            bus_path: Path to message storage (defaults to .agent_army/messages/)
            mode: Storage mode (file, redis, database) - currently only file implemented
        """
        if bus_path is None:
            bus_dir = Path.cwd() / ".agent_army" / "messages"
            bus_dir.mkdir(parents=True, exist_ok=True)
            self.bus_path = bus_dir
        else:
            self.bus_path = Path(bus_path)
            self.bus_path.mkdir(parents=True, exist_ok=True)

        self.mode = mode
        self.messages_file = self.bus_path / "messages.json"
        self.subscriptions_file = self.bus_path / "subscriptions.json"

        self.data = self._load_or_create()
        self.subscriptions = self._load_subscriptions()

        # In-memory callbacks (not persisted)
        self.callbacks: Dict[str, List[Callable]] = {}

    def _load_or_create(self) -> Dict:
        """Load existing messages or create new structure."""
        if self.messages_file.exists():
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "messages": [],
                "channels": {}
            }

    def _load_subscriptions(self) -> Dict:
        """Load subscriptions registry."""
        if self.subscriptions_file.exists():
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "subscriptions": {}
            }

    def _save(self):
        """Save messages to disk."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.messages_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def _save_subscriptions(self):
        """Save subscriptions to disk."""
        with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
            json.dump(self.subscriptions, f, indent=2)

    def publish(
        self,
        channel: str,
        message: Dict,
        sender: Optional[str] = None,
        priority: str = "NORMAL"
    ) -> str:
        """
        Publish a message to a channel.

        All subscribers to the channel will receive the message.

        Args:
            channel: Channel name to publish to
            message: Message dict to publish
            sender: Optional sender ID
            priority: Message priority (CRITICAL, HIGH, NORMAL, LOW)

        Returns:
            Message ID
        """
        message_id = f"msg-{str(uuid.uuid4())[:8]}"

        msg = {
            "message_id": message_id,
            "channel": channel,
            "sender": sender,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "delivered_to": [],
            "read_by": []
        }

        self.data["messages"].append(msg)

        # Update channel registry
        if channel not in self.data["channels"]:
            self.data["channels"][channel] = {
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "subscribers": []
            }

        self.data["channels"][channel]["message_count"] += 1

        self._save()

        # Trigger callbacks for this channel
        self._trigger_callbacks(channel, msg)

        return message_id

    def send_direct(
        self,
        recipient: str,
        message: Dict,
        sender: Optional[str] = None,
        priority: str = "NORMAL"
    ) -> str:
        """
        Send a direct message to a specific agent.

        Args:
            recipient: Agent ID to send to
            message: Message dict to send
            sender: Optional sender ID
            priority: Message priority

        Returns:
            Message ID
        """
        # Use a special channel for direct messages
        channel = f"direct.{recipient}"

        message_data = {
            "type": "direct",
            "recipient": recipient,
            **message
        }

        return self.publish(channel, message_data, sender, priority)

    def subscribe(
        self,
        channel: str,
        agent_id: str,
        callback: Optional[Callable] = None
    ):
        """
        Subscribe an agent to a channel.

        Args:
            channel: Channel name to subscribe to
            agent_id: Agent ID subscribing
            callback: Optional callback function for new messages
        """
        # Register subscription
        if channel not in self.subscriptions["subscriptions"]:
            self.subscriptions["subscriptions"][channel] = []

        if agent_id not in self.subscriptions["subscriptions"][channel]:
            self.subscriptions["subscriptions"][channel].append(agent_id)
            self._save_subscriptions()

        # Update channel registry
        if channel not in self.data["channels"]:
            self.data["channels"][channel] = {
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "subscribers": []
            }

        if agent_id not in self.data["channels"][channel]["subscribers"]:
            self.data["channels"][channel]["subscribers"].append(agent_id)
            self._save()

        # Register callback
        if callback:
            if channel not in self.callbacks:
                self.callbacks[channel] = []
            self.callbacks[channel].append(callback)

    def unsubscribe(self, channel: str, agent_id: str):
        """
        Unsubscribe an agent from a channel.

        Args:
            channel: Channel name to unsubscribe from
            agent_id: Agent ID unsubscribing
        """
        if channel in self.subscriptions["subscriptions"]:
            if agent_id in self.subscriptions["subscriptions"][channel]:
                self.subscriptions["subscriptions"][channel].remove(agent_id)
                self._save_subscriptions()

        if channel in self.data["channels"]:
            if agent_id in self.data["channels"][channel]["subscribers"]:
                self.data["channels"][channel]["subscribers"].remove(agent_id)
                self._save()

    def get_messages(
        self,
        channel: Optional[str] = None,
        agent_id: Optional[str] = None,
        unread_only: bool = False,
        since: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get messages from the bus.

        Args:
            channel: Optional channel filter
            agent_id: Optional agent ID filter (for direct messages)
            unread_only: Only return unread messages
            since: Optional timestamp to get messages after
            limit: Optional limit on number of messages

        Returns:
            List of message dicts
        """
        messages = self.data["messages"]

        # Filter by channel
        if channel:
            messages = [m for m in messages if m["channel"] == channel]

        # Filter by agent (direct messages)
        if agent_id:
            direct_channel = f"direct.{agent_id}"
            messages = [m for m in messages if m["channel"] == direct_channel]

        # Filter unread
        if unread_only and agent_id:
            messages = [m for m in messages if agent_id not in m["read_by"]]

        # Filter by timestamp
        if since:
            since_dt = self._parse_datetime(since)
            messages = [
                m for m in messages
                if self._parse_datetime(m["timestamp"]) > since_dt
            ]

        # Sort by timestamp (newest first)
        messages.sort(key=lambda m: m["timestamp"], reverse=True)

        # Apply limit
        if limit:
            messages = messages[:limit]

        return messages

    def mark_read(self, message_id: str, agent_id: str):
        """
        Mark a message as read by an agent.

        Args:
            message_id: Message ID to mark as read
            agent_id: Agent ID marking as read
        """
        for msg in self.data["messages"]:
            if msg["message_id"] == message_id:
                if agent_id not in msg["read_by"]:
                    msg["read_by"].append(agent_id)
                    self._save()
                break

    def mark_delivered(self, message_id: str, agent_id: str):
        """
        Mark a message as delivered to an agent.

        Args:
            message_id: Message ID to mark as delivered
            agent_id: Agent ID marking as delivered
        """
        for msg in self.data["messages"]:
            if msg["message_id"] == message_id:
                if agent_id not in msg["delivered_to"]:
                    msg["delivered_to"].append(agent_id)
                    self._save()
                break

    def get_unread_count(self, agent_id: str, channel: Optional[str] = None) -> int:
        """
        Get count of unread messages for an agent.

        Args:
            agent_id: Agent ID to count for
            channel: Optional channel filter

        Returns:
            Number of unread messages
        """
        messages = self.get_messages(
            channel=channel,
            agent_id=agent_id if not channel else None,
            unread_only=True
        )
        return len(messages)

    def list_channels(self) -> List[str]:
        """
        List all active channels.

        Returns:
            List of channel names
        """
        return list(self.data["channels"].keys())

    def get_channel_info(self, channel: str) -> Optional[Dict]:
        """
        Get information about a channel.

        Args:
            channel: Channel name

        Returns:
            Channel info dict or None if not found
        """
        return self.data["channels"].get(channel)

    def clear_old_messages(self, older_than_days: int = 7):
        """
        Clear messages older than specified days.

        Args:
            older_than_days: Only clear messages older than this many days
        """
        cutoff = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)

        self.data["messages"] = [
            msg for msg in self.data["messages"]
            if self._parse_datetime(msg["timestamp"]).timestamp() > cutoff
        ]

        self._save()

    def _trigger_callbacks(self, channel: str, message: Dict):
        """Trigger callbacks for a channel."""
        if channel in self.callbacks:
            for callback in self.callbacks[channel]:
                try:
                    callback(message)
                except Exception as e:
                    # Log error but don't fail
                    print(f"Error in callback for channel {channel}: {e}")

    def _parse_datetime(self, iso_string: str) -> datetime:
        """Parse ISO format datetime string."""
        try:
            return datetime.fromisoformat(iso_string)
        except (ValueError, AttributeError, TypeError):
            return datetime.now()

    def export_to_markdown(self, output_path: Optional[Path] = None) -> str:
        """
        Export message bus status to markdown format.

        Args:
            output_path: Optional path to write markdown file

        Returns:
            Markdown string
        """
        if not output_path:
            output_path = self.bus_path / "MESSAGE_BUS.md"

        lines = []
        lines.append("# Message Bus Status")
        lines.append("")
        lines.append(f"**Last Updated**: {self.data['last_updated']}")
        lines.append("")

        # Statistics
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- **Total Messages**: {len(self.data['messages'])}")
        lines.append(f"- **Active Channels**: {len(self.data['channels'])}")
        lines.append("")

        # Channels
        lines.append("## Channels")
        lines.append("")

        for channel_name, channel_info in self.data["channels"].items():
            lines.append(f"### {channel_name}")
            lines.append("")
            lines.append(f"- **Message Count**: {channel_info['message_count']}")
            lines.append(f"- **Subscribers**: {len(channel_info['subscribers'])}")

            if channel_info['subscribers']:
                lines.append(f"- **Subscriber List**: {', '.join(channel_info['subscribers'])}")

            lines.append("")

        # Recent messages (last 10)
        recent = sorted(
            self.data["messages"],
            key=lambda m: m["timestamp"],
            reverse=True
        )[:10]

        if recent:
            lines.append("## Recent Messages")
            lines.append("")

            for msg in recent:
                lines.append(f"### {msg['message_id']}")
                lines.append("")
                lines.append(f"- **Channel**: {msg['channel']}")
                lines.append(f"- **Sender**: {msg.get('sender', 'system')}")
                lines.append(f"- **Priority**: {msg['priority']}")
                lines.append(f"- **Timestamp**: {msg['timestamp']}")
                lines.append(f"- **Delivered To**: {len(msg['delivered_to'])} agents")
                lines.append(f"- **Read By**: {len(msg['read_by'])} agents")
                lines.append("")

        markdown = "\n".join(lines)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return markdown


# Common message types for convenience
class MessageTypes:
    """Standard message types for the agent army."""

    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    VERIFICATION_REQUIRED = "verification_required"
    TESTS_GENERATED = "tests_generated"
    SUBTASKS_CREATED = "subtasks_created"
    BLOCKING_TASK_EXISTS = "blocking_task_exists"
    AGENT_HEALTH_CHECK = "agent_health_check"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    BEST_PRACTICES_UPDATE = "best_practices_update"
    PATTERN_LEARNED = "pattern_learned"
    INSIGHTS_GENERATED = "insights_generated"

    # E2B Execution message types
    EXECUTION_REQUEST = "execution_request"
    EXECUTION_RESULT = "execution_result"
    EXECUTION_FAILED = "execution_failed"

    # E2B Sandbox lifecycle
    SANDBOX_CREATED = "sandbox_created"
    SANDBOX_TERMINATED = "sandbox_terminated"
    SANDBOX_ERROR = "sandbox_error"

    # Checklist system message types
    CHECKLIST_INITIALIZED = "checklist_initialized"
    CHECKLIST_TASK_UPDATE = "checklist_task_update"
    CHECKLIST_BLOCKING_TASK = "checklist_blocking_task"

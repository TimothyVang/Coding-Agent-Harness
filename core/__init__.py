"""
Core Infrastructure
==================

Core components for the Universal AI Development Platform:
- EnhancedChecklistManager: Task tracking with subtasks and blocking
- ProjectRegistry: Multi-project management
- TaskQueue: Priority-based task distribution
- MessageBus: Inter-agent communication
- AgentMemory: Agent learning and memory system
- EmbeddingManager: Vector embeddings for similarity search
"""

from .enhanced_checklist import EnhancedChecklistManager
from .project_registry import ProjectRegistry
from .task_queue import TaskQueue
from .message_bus import MessageBus
from .agent_memory import AgentMemory

# Optional embedding support
try:
    from .embeddings import EmbeddingManager, EmbeddingStorage, EMBEDDINGS_AVAILABLE
except ImportError:
    EmbeddingManager = None
    EmbeddingStorage = None
    EMBEDDINGS_AVAILABLE = False

__all__ = [
    'EnhancedChecklistManager',
    'ProjectRegistry',
    'TaskQueue',
    'MessageBus',
    'AgentMemory',
    'EmbeddingManager',
    'EmbeddingStorage',
    'EMBEDDINGS_AVAILABLE',
]

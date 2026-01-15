"""
Tests for Embedding System
==========================

Tests for EmbeddingManager, EmbeddingStorage, and AgentMemory embedding integration.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

# Import core modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.embeddings import (
    EmbeddingManager, EmbeddingStorage,
    EMBEDDINGS_AVAILABLE, check_embedding_dependencies
)
from core.agent_memory import AgentMemory


class TestEmbeddingDependencies:
    """Test embedding dependency checking."""

    def test_check_dependencies(self):
        """Test that dependency check returns expected structure."""
        result = check_embedding_dependencies()

        assert "available" in result
        assert "numpy" in result
        assert "sentence_transformers" in result
        assert "install_command" in result

    def test_embeddings_available_flag(self):
        """Test that EMBEDDINGS_AVAILABLE is a boolean."""
        assert isinstance(EMBEDDINGS_AVAILABLE, bool)


class TestEmbeddingManager:
    """Test EmbeddingManager functionality."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = EmbeddingManager()

        assert manager.model_name == "all-MiniLM-L6-v2"
        assert manager._model is None  # Lazy loading

    def test_available_property(self):
        """Test available property."""
        manager = EmbeddingManager()

        assert manager.available == EMBEDDINGS_AVAILABLE

    @pytest.mark.skipif(not EMBEDDINGS_AVAILABLE, reason="Embeddings not installed")
    def test_encode_single_text(self):
        """Test encoding a single text."""
        manager = EmbeddingManager()

        embedding = manager.encode("Hello world")

        assert embedding is not None
        assert embedding.shape == (1, 384)  # MiniLM produces 384-dim vectors

    @pytest.mark.skipif(not EMBEDDINGS_AVAILABLE, reason="Embeddings not installed")
    def test_encode_multiple_texts(self):
        """Test encoding multiple texts."""
        manager = EmbeddingManager()

        texts = ["Hello", "World", "Test"]
        embeddings = manager.encode(texts)

        assert embeddings is not None
        assert embeddings.shape == (3, 384)

    @pytest.mark.skipif(not EMBEDDINGS_AVAILABLE, reason="Embeddings not installed")
    def test_cosine_similarity(self):
        """Test cosine similarity computation."""
        manager = EmbeddingManager()

        texts = ["Hello world", "Hi there", "Completely different topic"]
        embeddings = manager.encode(texts)

        query = manager.encode("Hello")
        similarities = manager.cosine_similarity(query, embeddings)

        assert len(similarities) == 3
        # "Hello world" should be most similar to "Hello"
        assert similarities[0] > similarities[2]

    @pytest.mark.skipif(not EMBEDDINGS_AVAILABLE, reason="Embeddings not installed")
    def test_similarity_search(self):
        """Test similarity search."""
        manager = EmbeddingManager()

        texts = [
            "JWT authentication pattern",
            "Database connection pooling",
            "React component lifecycle",
            "User authentication flow"
        ]
        metadata = [{"title": t, "index": i} for i, t in enumerate(texts)]
        embeddings = manager.encode(texts)

        results = manager.similarity_search(
            "auth login",
            embeddings,
            metadata,
            top_k=2,
            threshold=0.0
        )

        assert len(results) <= 2
        # Auth-related should rank higher
        titles = [r[2]["title"] for r in results]
        assert any("auth" in t.lower() for t in titles)


class TestEmbeddingStorage:
    """Test EmbeddingStorage functionality."""

    def setup_method(self):
        """Create temp directory for tests."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test storage initialization."""
        storage = EmbeddingStorage(self.temp_dir)

        assert storage.storage_dir == self.temp_dir

    @pytest.mark.skipif(not EMBEDDINGS_AVAILABLE, reason="Embeddings not installed")
    def test_save_and_load(self):
        """Test saving and loading embeddings."""
        import numpy as np

        storage = EmbeddingStorage(self.temp_dir)

        # Create test data
        embeddings = np.random.randn(5, 384).astype(np.float32)
        metadata = [{"title": f"Pattern {i}"} for i in range(5)]

        # Save
        storage.save("patterns", embeddings, metadata)

        # Load
        loaded_embeddings, loaded_metadata = storage.load("patterns")

        assert loaded_embeddings is not None
        assert loaded_embeddings.shape == (5, 384)
        assert len(loaded_metadata) == 5
        assert loaded_metadata[0]["title"] == "Pattern 0"

    def test_exists(self):
        """Test exists check."""
        storage = EmbeddingStorage(self.temp_dir)

        assert not storage.exists("patterns")

    @pytest.mark.skipif(not EMBEDDINGS_AVAILABLE, reason="Embeddings not installed")
    def test_delete(self):
        """Test deleting embeddings."""
        import numpy as np

        storage = EmbeddingStorage(self.temp_dir)

        # Save and delete
        embeddings = np.random.randn(3, 384).astype(np.float32)
        storage.save("test", embeddings, [{}] * 3)

        assert storage.exists("test")

        storage.delete("test")

        assert not storage.exists("test")


class TestAgentMemoryWithEmbeddings:
    """Test AgentMemory embedding integration."""

    def setup_method(self):
        """Create temp directory for tests."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization_with_embeddings(self):
        """Test memory initialization with embeddings enabled."""
        memory = AgentMemory("test-agent", self.temp_dir, use_embeddings=True)

        assert memory.use_embeddings == EMBEDDINGS_AVAILABLE
        assert memory._embedding_manager is None  # Lazy loading

    def test_initialization_without_embeddings(self):
        """Test memory initialization with embeddings disabled."""
        memory = AgentMemory("test-agent", self.temp_dir, use_embeddings=False)

        assert memory.use_embeddings is False

    def test_add_pattern_marks_dirty(self):
        """Test that adding pattern marks embeddings as dirty."""
        memory = AgentMemory("test-agent", self.temp_dir, use_embeddings=True)

        memory.add_pattern(
            title="Test Pattern",
            description="A test pattern"
        )

        assert memory._embeddings_dirty is True

    @pytest.mark.skipif(not EMBEDDINGS_AVAILABLE, reason="Embeddings not installed")
    def test_find_similar_patterns_with_embeddings(self):
        """Test pattern similarity search with embeddings."""
        memory = AgentMemory("test-agent", self.temp_dir, use_embeddings=True)

        # Add some patterns
        memory.add_pattern("JWT authentication", "Token-based auth using JWT")
        memory.add_pattern("Database connection", "PostgreSQL connection pooling")
        memory.add_pattern("User login flow", "Authentication with password")

        # Search
        results = memory.find_similar_patterns("authentication login")

        assert len(results) > 0
        # Auth-related patterns should rank higher
        assert any("auth" in p["title"].lower() or "login" in p["title"].lower()
                   for p in results[:2])

    def test_find_similar_patterns_keyword_fallback(self):
        """Test pattern search falls back to keyword matching."""
        memory = AgentMemory("test-agent", self.temp_dir, use_embeddings=False)

        memory.add_pattern("JWT authentication", "Token-based auth")
        memory.add_pattern("Database setup", "PostgreSQL config")

        results = memory.find_similar_patterns("authentication")

        assert len(results) >= 1
        assert results[0]["title"] == "JWT authentication"

    @pytest.mark.skipif(not EMBEDDINGS_AVAILABLE, reason="Embeddings not installed")
    def test_get_relevant_mistakes_with_embeddings(self):
        """Test mistake search with embeddings."""
        memory = AgentMemory("test-agent", self.temp_dir, use_embeddings=True)

        memory.add_mistake(
            title="Missing input validation",
            task_id="task-1",
            error="User input not sanitized",
            solution="Always validate and sanitize input"
        )
        memory.add_mistake(
            title="SQL injection vulnerability",
            task_id="task-2",
            error="Raw SQL query with user input",
            solution="Use parameterized queries"
        )

        results = memory.get_relevant_mistakes("validate user input security")

        assert len(results) > 0

    def test_get_relevant_mistakes_keyword_fallback(self):
        """Test mistake search falls back to keyword matching."""
        memory = AgentMemory("test-agent", self.temp_dir, use_embeddings=False)

        memory.add_mistake(
            title="Memory leak",
            task_id="task-1",
            error="Objects not cleaned up",
            solution="Use context managers"
        )

        results = memory.get_relevant_mistakes("memory")

        assert len(results) >= 1
        assert results[0]["title"] == "Memory leak"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

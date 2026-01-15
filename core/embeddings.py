"""
Embedding Manager
=================

Vector embeddings for semantic similarity search in agent memory.

Features:
- Lazy model loading (only loads when first needed)
- Cosine similarity search
- NumPy-based storage for fast retrieval
- Fallback to basic search if dependencies unavailable
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Suppress TensorFlow warnings before importing
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Try to import embedding dependencies
EMBEDDINGS_AVAILABLE = False
np = None
SentenceTransformer = None

try:
    import numpy as np
    # Try importing sentence_transformers with error handling for TF/Keras issues
    try:
        from sentence_transformers import SentenceTransformer
        EMBEDDINGS_AVAILABLE = True
    except (ImportError, ValueError) as e:
        # Handle Keras 3 / tf-keras compatibility issues
        if "Keras" in str(e) or "tf_keras" in str(e):
            print(f"[EmbeddingManager] Note: TensorFlow/Keras conflict detected, but PyTorch backend will be used")
            # sentence-transformers primarily uses PyTorch, try alternative import
            try:
                import torch
                from sentence_transformers import SentenceTransformer
                EMBEDDINGS_AVAILABLE = True
            except Exception:
                pass
        else:
            pass
except ImportError:
    pass


class EmbeddingManager:
    """
    Manages text embeddings with lazy model loading.

    Uses sentence-transformers for semantic similarity search.
    Falls back to keyword matching if dependencies are unavailable.
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str = None):
        """
        Initialize embedding manager.

        Args:
            model_name: Name of sentence-transformers model to use
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self._model = None
        self._dimension = None

    @property
    def available(self) -> bool:
        """Check if embedding functionality is available."""
        return EMBEDDINGS_AVAILABLE

    @property
    def model(self):
        """Lazy load the embedding model."""
        if not EMBEDDINGS_AVAILABLE:
            return None

        if self._model is None:
            print(f"[EmbeddingManager] Loading model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
            print(f"[EmbeddingManager] Model loaded ({self._dimension} dimensions)")

        return self._model

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None and self.model:
            self._dimension = self.model.get_sentence_embedding_dimension()
        return self._dimension or 384

    def encode(self, texts: Union[str, List[str]]) -> Optional['np.ndarray']:
        """
        Convert texts to embeddings.

        Args:
            texts: Single text or list of texts to encode

        Returns:
            NumPy array of embeddings, or None if unavailable
        """
        if not self.available or self.model is None:
            return None

        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings

    def cosine_similarity(
        self,
        query_embedding: 'np.ndarray',
        embeddings: 'np.ndarray'
    ) -> 'np.ndarray':
        """
        Compute cosine similarity between query and all embeddings.

        Args:
            query_embedding: Single query embedding (1D or 2D with shape [1, dim])
            embeddings: Matrix of embeddings to compare against

        Returns:
            Array of similarity scores
        """
        if not EMBEDDINGS_AVAILABLE:
            return np.array([])

        # Ensure query is 1D
        if query_embedding.ndim == 2:
            query_embedding = query_embedding[0]

        # Normalize
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
        embeddings_norm = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-9)

        # Compute cosine similarity
        similarities = np.dot(embeddings_norm, query_norm)

        return similarities

    def similarity_search(
        self,
        query: str,
        embeddings: 'np.ndarray',
        metadata: List[Dict],
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Tuple[int, float, Dict]]:
        """
        Find most similar items using cosine similarity.

        Args:
            query: Search query text
            embeddings: Matrix of embeddings
            metadata: List of metadata dicts corresponding to embeddings
            top_k: Maximum number of results
            threshold: Minimum similarity score (0-1)

        Returns:
            List of (index, score, metadata) tuples, sorted by score descending
        """
        if not self.available or embeddings is None or len(embeddings) == 0:
            return []

        # Encode query
        query_embedding = self.encode(query)
        if query_embedding is None:
            return []

        # Compute similarities
        similarities = self.cosine_similarity(query_embedding, embeddings)

        # Filter by threshold and get top-k
        results = []
        for idx, score in enumerate(similarities):
            if score >= threshold and idx < len(metadata):
                results.append((idx, float(score), metadata[idx]))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]


class EmbeddingStorage:
    """
    Stores and manages embedding vectors on disk.

    Uses NumPy binary format for fast I/O.
    Maintains metadata JSON for mapping and versioning.
    """

    def __init__(self, storage_dir: Path):
        """
        Initialize embedding storage.

        Args:
            storage_dir: Directory to store embedding files
        """
        self.storage_dir = Path(storage_dir)
        self.embeddings_dir = self.storage_dir / "embeddings"

    def _ensure_dir(self):
        """Ensure storage directory exists."""
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)

    def _hash_content(self, content: str) -> str:
        """Generate hash for content."""
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def save(
        self,
        name: str,
        embeddings: 'np.ndarray',
        metadata: List[Dict],
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Save embeddings to disk.

        Args:
            name: Name for this embedding set (e.g., "patterns", "mistakes")
            embeddings: NumPy array of embeddings
            metadata: List of metadata dicts
            model_name: Model used to generate embeddings
        """
        if not EMBEDDINGS_AVAILABLE or embeddings is None:
            return

        self._ensure_dir()

        # Save embeddings
        npy_path = self.embeddings_dir / f"{name}.npy"
        np.save(str(npy_path), embeddings)

        # Save metadata
        meta = {
            "version": "1.0",
            "model": model_name,
            "dimension": embeddings.shape[1] if len(embeddings.shape) > 1 else 384,
            "count": len(embeddings),
            "updated_at": datetime.now().isoformat(),
            "entries": metadata
        }

        meta_path = self.embeddings_dir / f"{name}_metadata.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def load(self, name: str) -> Tuple[Optional['np.ndarray'], List[Dict]]:
        """
        Load embeddings from disk.

        Args:
            name: Name of embedding set to load

        Returns:
            Tuple of (embeddings array, metadata list)
        """
        if not EMBEDDINGS_AVAILABLE:
            return None, []

        npy_path = self.embeddings_dir / f"{name}.npy"
        meta_path = self.embeddings_dir / f"{name}_metadata.json"

        if not npy_path.exists() or not meta_path.exists():
            return None, []

        try:
            embeddings = np.load(str(npy_path))

            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)

            return embeddings, meta.get("entries", [])
        except Exception as e:
            print(f"[EmbeddingStorage] Error loading {name}: {e}")
            return None, []

    def exists(self, name: str) -> bool:
        """Check if embeddings exist for given name."""
        npy_path = self.embeddings_dir / f"{name}.npy"
        return npy_path.exists()

    def delete(self, name: str):
        """Delete embeddings for given name."""
        npy_path = self.embeddings_dir / f"{name}.npy"
        meta_path = self.embeddings_dir / f"{name}_metadata.json"

        if npy_path.exists():
            npy_path.unlink()
        if meta_path.exists():
            meta_path.unlink()

    def get_stats(self) -> Dict:
        """Get storage statistics."""
        stats = {
            "available": EMBEDDINGS_AVAILABLE,
            "storage_dir": str(self.storage_dir),
            "embedding_sets": []
        }

        if self.embeddings_dir.exists():
            for meta_file in self.embeddings_dir.glob("*_metadata.json"):
                name = meta_file.stem.replace("_metadata", "")
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    stats["embedding_sets"].append({
                        "name": name,
                        "count": meta.get("count", 0),
                        "model": meta.get("model", "unknown"),
                        "updated_at": meta.get("updated_at", "unknown")
                    })
                except Exception:
                    pass

        return stats


def check_embedding_dependencies() -> Dict:
    """
    Check if embedding dependencies are installed.

    Returns:
        Dict with status and installation instructions
    """
    result = {
        "available": EMBEDDINGS_AVAILABLE,
        "numpy": False,
        "sentence_transformers": False,
        "install_command": "pip install sentence-transformers numpy"
    }

    try:
        import numpy
        result["numpy"] = True
        result["numpy_version"] = numpy.__version__
    except ImportError:
        pass

    try:
        import sentence_transformers
        result["sentence_transformers"] = True
        result["sentence_transformers_version"] = sentence_transformers.__version__
    except ImportError:
        pass

    return result

# CineVault OS — Self-Hosted Text Embedding Service
# Replaces the local-Ollama dependency for taste-vector generation (ADR-004
# follow-up). Ollama was already running `all-minilm` for this — the same
# model family as `all-MiniLM-L6-v2` below — so this is a same-output swap,
# not a behavior change, and it removes an external service dependency
# entirely: no network call after the model weights are cached on first use.

import asyncio
import logging
import threading
from typing import List, Optional

logger = logging.getLogger("cinevault.ai.embedding")

EMBEDDING_DIMENSION = 384
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None
_model_lock = threading.Lock()


def _get_model():
    """
    Lazily loads and caches the sentence-transformers model as a process-wide
    singleton. Loading happens on first use (not at import time) so importing
    this module never triggers a model download, and so app startup / tests
    that never call generate_embedding never pay the load cost.
    """
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        if _model is None:
            # Imported lazily too — keeps `sentence-transformers` off the
            # import path for any code that only imports this module for
            # EMBEDDING_DIMENSION or type hints.
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model %s (first use, one-time cost)...", _MODEL_NAME)
            _model = SentenceTransformer(_MODEL_NAME)
            logger.info("Embedding model loaded.")
    return _model


def _encode_sync(text: str) -> List[float]:
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return [float(x) for x in vector.tolist()]


async def generate_embedding(text: str) -> List[float]:
    """
    Generates a 384-dimensional dense vector embedding for the input text
    using a self-hosted sentence-transformers model — no external API call.

    :param text: Text to embed (e.g. a user's free-text taste summary).
    :return: 384-dimensional dense float vector, L2-normalized.
    :raises ValueError: If the input text is empty.
    :raises RuntimeError: If the underlying model fails to load or encode.
    """
    if not text or not text.strip():
        raise ValueError("Input text for embedding generation cannot be empty.")

    try:
        # sentence-transformers is a synchronous, CPU-bound library — run it
        # off the event loop thread so it doesn't block other requests.
        return await asyncio.to_thread(_encode_sync, text.strip())
    except ValueError:
        raise
    except Exception as exc:
        logger.error("Failed to generate embedding: %s", exc, exc_info=True)
        raise RuntimeError(f"Embedding generation failed: {exc}") from exc

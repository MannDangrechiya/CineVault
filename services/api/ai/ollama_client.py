# CineVault OS — Async Ollama AI Brain Client (v2.0 Module 3)
# Communicates with local or remote Ollama instances for embeddings and chat generation (ADR-004)

import os
import logging
from typing import List, Optional, Dict, Any
import httpx

logger = logging.getLogger("cinevault.ai.ollama")


class OllamaClient:
    """
    Async HTTP client for communicating with an Ollama AI instance.
    Provides methods for vector embedding generation (all-minilm) and LLM chat generation (mistral/llama3).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        embedding_model: str = "all-minilm",
        chat_model: str = "mistral",
        timeout: float = 30.0,
        client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initializes the Ollama HTTP client.

        :param base_url: Base URL for the Ollama API (defaults to OLLAMA_BASE_URL env var or http://localhost:11434).
        :param embedding_model: Name of the embedding model (default: all-minilm).
        :param chat_model: Name of the generative chat model (default: mistral).
        :param timeout: Request timeout in seconds.
        :param client: Optional pre-configured httpx.AsyncClient for connection reuse or testing.
        """
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.embedding_model = embedding_model
        self.chat_model = chat_model
        self.timeout = timeout
        self._injected_client = client

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns the injected client or creates a temporary context."""
        if self._injected_client is not None:
            return self._injected_client
        return httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for the input text using Ollama /api/embeddings.

        :param text: Text string to embed (e.g., taste summary or movie metadata).
        :return: 384-dimensional dense float vector embedding.
        :raises RuntimeError: If Ollama API call fails or returns unexpected payload format.
        """
        if not text or not text.strip():
            raise ValueError("Input text for embedding generation cannot be empty.")

        url = f"{self.base_url}/api/embeddings"
        payload = {
            "model": self.embedding_model,
            "prompt": text.strip(),
        }

        try:
            if self._injected_client is not None:
                client = await self._get_client()
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data: Dict[str, Any] = response.json()
            else:
                async with await self._get_client() as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()

            # Ollama /api/embeddings returns {"embedding": [float, ...]}
            if "embedding" in data and isinstance(data["embedding"], list):
                return [float(x) for x in data["embedding"]]
            elif "embeddings" in data and isinstance(data["embeddings"], list) and len(data["embeddings"]) > 0:
                # Ollama /api/embed batch format compatibility
                return [float(x) for x in data["embeddings"][0]]
            else:
                raise KeyError(f"Unexpected response format from Ollama embeddings: {data}")

        except httpx.HTTPStatusError as exc:
            logger.error(f"Ollama embedding HTTP error {exc.response.status_code}: {exc.response.text}")
            raise RuntimeError(f"Ollama API HTTP {exc.response.status_code} error: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            logger.error(f"Ollama embedding connection error to {url}: {exc}")
            raise RuntimeError(f"Could not connect to Ollama at {self.base_url}: {exc}") from exc
        except Exception as exc:
            logger.error(f"Failed to generate Ollama embedding: {exc}", exc_info=True)
            raise RuntimeError(f"Ollama embedding generation failed: {exc}") from exc

    async def generate_chat(self, prompt: str) -> str:
        """
        Generates a natural language response using Ollama /api/generate (non-streaming).

        :param prompt: Prompt string for the LLM.
        :return: String response from the AI model.
        :raises RuntimeError: If Ollama API call fails.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt for chat generation cannot be empty.")

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.chat_model,
            "prompt": prompt.strip(),
            "stream": False,
        }

        try:
            if self._injected_client is not None:
                client = await self._get_client()
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data: Dict[str, Any] = response.json()
            else:
                async with await self._get_client() as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()

            # Ollama /api/generate returns {"response": "..."}
            if "response" in data:
                return str(data["response"]).strip()
            elif "message" in data and isinstance(data["message"], dict):
                return str(data["message"].get("content", "")).strip()
            else:
                raise KeyError(f"Unexpected response format from Ollama generate: {data}")

        except httpx.HTTPStatusError as exc:
            logger.error(f"Ollama generate HTTP error {exc.response.status_code}: {exc.response.text}")
            raise RuntimeError(f"Ollama API HTTP {exc.response.status_code} error: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            logger.error(f"Ollama generate connection error to {url}: {exc}")
            raise RuntimeError(f"Could not connect to Ollama at {self.base_url}: {exc}") from exc
        except Exception as exc:
            logger.error(f"Failed to generate Ollama chat: {exc}", exc_info=True)
            raise RuntimeError(f"Ollama chat generation failed: {exc}") from exc

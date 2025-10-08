"""Ollama adapter implementation."""

import os
from typing import List

import httpx

from .base import LLMAdapter, LLMMessage, LLMResponse


class OllamaAdapter(LLMAdapter):
    """Adapter for Ollama local models."""

    SUPPORTED_MODELS = [
        "llama2",
        "llama2:13b",
        "llama2:70b",
        "mistral",
        "mixtral",
        "codellama",
        "phi",
        "neural-chat",
    ]

    def __init__(self, model: str, api_key: str | None = None, **kwargs):
        """Initialize Ollama adapter.

        Args:
            model: Ollama model name (e.g., 'llama2', 'mistral')
            api_key: Not used for Ollama (local service)
            **kwargs: Additional configuration (base_url, timeout, etc.)
        """
        super().__init__(model, api_key, **kwargs)
        self.base_url = kwargs.get("base_url") or os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        self.timeout = kwargs.get("timeout", 120.0)

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Ollama API.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum response tokens (num_predict in Ollama)
            **kwargs: Additional Ollama parameters

        Returns:
            LLMResponse with generated content

        Raises:
            RuntimeError: If API call fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Ollama chat API format
                ollama_messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ]

                payload = {
                    "model": self.model,
                    "messages": ollama_messages,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                    "stream": False,
                }

                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                return LLMResponse(
                    content=data["message"]["content"],
                    model=self.model,
                    provider=self.provider_name,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count"),
                        "completion_tokens": data.get("eval_count"),
                    } if "eval_count" in data else None
                )

        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API call failed: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Ollama request failed: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check Ollama service availability and model availability.

        Returns:
            True if Ollama is running and the model is available
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if Ollama service is running
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()

                # Check if the specific model is available
                available_models = [m["name"] for m in data.get("models", [])]

                # Match model name (handle tags like "llama2:latest" vs "llama2")
                model_base = self.model.split(":")[0]
                return any(
                    m.startswith(model_base) or m.split(":")[0] == model_base
                    for m in available_models
                )

        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "ollama"

    async def list_available_models(self) -> List[str]:
        """List models available in the local Ollama instance.

        Returns:
            List of model names
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

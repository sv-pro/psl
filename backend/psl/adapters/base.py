"""Base LLM adapter interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal


@dataclass
class LLMMessage:
    """Represents a message in an LLM conversation."""
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM adapter."""
    content: str
    model: str
    provider: str
    usage: dict | None = None


class LLMAdapter(ABC):
    """Abstract base class for LLM adapters.

    Each provider (OpenAI, Anthropic, Ollama) implements this interface
    to provide a consistent API across different LLM services.
    """

    def __init__(self, model: str, api_key: str | None = None, **kwargs):
        """Initialize the adapter.

        Args:
            model: The model identifier (e.g., 'gpt-4', 'claude-sonnet-4-5-20250929')
            api_key: API key for the provider (if required)
            **kwargs: Additional provider-specific configuration
        """
        self.model = model
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse containing the generated text and metadata

        Raises:
            ValueError: If the request is invalid
            RuntimeError: If the API call fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and configured correctly.

        Returns:
            True if the provider is healthy, False otherwise
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'anthropic', 'ollama')."""
        pass

"""OpenAI adapter implementation."""

import os
from typing import List

from openai import AsyncOpenAI

from .base import LLMAdapter, LLMMessage, LLMResponse


class OpenAIAdapter(LLMAdapter):
    """Adapter for OpenAI models (GPT-4, GPT-3.5, etc.)."""

    SUPPORTED_MODELS = [
        "gpt-5",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]

    def __init__(self, model: str, api_key: str | None = None, **kwargs):
        """Initialize OpenAI adapter.

        Args:
            model: OpenAI model name (e.g., 'gpt-4')
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            **kwargs: Additional OpenAI client configuration
        """
        super().__init__(model, api_key, **kwargs)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = AsyncOpenAI(api_key=self.api_key, **kwargs)

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using OpenAI API.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum response tokens
            **kwargs: Additional OpenAI parameters

        Returns:
            LLMResponse with generated content

        Raises:
            RuntimeError: If API call fails
        """
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check OpenAI API availability.

        Returns:
            True if API is accessible and model is available
        """
        try:
            # Try a minimal completion to verify connectivity
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return response.choices[0].message.content is not None
        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "openai"

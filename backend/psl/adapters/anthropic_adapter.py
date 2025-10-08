"""Anthropic Claude adapter implementation."""

import os
from typing import List

from anthropic import AsyncAnthropic

from .base import LLMAdapter, LLMMessage, LLMResponse


class AnthropicAdapter(LLMAdapter):
    """Adapter for Anthropic Claude models."""

    SUPPORTED_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-sonnet-4-5-20250929",  # Latest model
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]

    def __init__(self, model: str, api_key: str | None = None, **kwargs):
        """Initialize Anthropic adapter.

        Args:
            model: Claude model name (e.g., 'claude-sonnet-4-5-20250929')
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            **kwargs: Additional Anthropic client configuration
        """
        super().__init__(model, api_key, **kwargs)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")

        self.client = AsyncAnthropic(api_key=self.api_key, **kwargs)

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Anthropic API.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum response tokens
            **kwargs: Additional Anthropic parameters

        Returns:
            LLMResponse with generated content

        Raises:
            RuntimeError: If API call fails
        """
        try:
            # Anthropic requires system message separately
            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    conversation_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            # Ensure we have at least one user message
            if not conversation_messages or conversation_messages[0]["role"] != "user":
                raise ValueError("First non-system message must be from user")

            request_params = {
                "model": self.model,
                "messages": conversation_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }

            if system_message:
                request_params["system"] = system_message

            response = await self.client.messages.create(**request_params)

            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                provider=self.provider_name,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                } if response.usage else None
            )

        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check Anthropic API availability.

        Returns:
            True if API is accessible and model is available
        """
        try:
            # Try a minimal completion to verify connectivity
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return response.content[0].text is not None
        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "anthropic"

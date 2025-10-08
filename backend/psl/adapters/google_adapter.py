"""Google AI (Gemini) adapter implementation."""

import os
from typing import List

import httpx

from .base import LLMAdapter, LLMMessage, LLMResponse


class GoogleAdapter(LLMAdapter):
    """Adapter for Google AI (Gemini) models."""

    SUPPORTED_MODELS = [
        "gemini-pro",
        "gemini-pro-vision",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    def __init__(self, model: str, api_key: str | None = None, **kwargs):
        """Initialize Google AI adapter.

        Args:
            model: Google AI model name (e.g., 'gemini-pro')
            api_key: Google AI API key (defaults to GOOGLE_API_KEY env var)
            **kwargs: Additional configuration
        """
        super().__init__(model, api_key, **kwargs)
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google AI API key not provided")

        self.timeout = kwargs.get("timeout", 60.0)

    async def complete(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Google AI Gemini API.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            **kwargs: Additional Gemini parameters

        Returns:
            LLMResponse with generated content

        Raises:
            RuntimeError: If API call fails
        """
        try:
            # Convert messages to Gemini format
            # Gemini uses "parts" with "text" field
            contents = []
            for msg in messages:
                role = "user" if msg.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })

            # Merge system messages into first user message
            # (Gemini doesn't have explicit system role)
            system_content = ""
            filtered_contents = []
            for content in contents:
                if content["role"] == "system":
                    system_content += content["parts"][0]["text"] + "\n\n"
                else:
                    filtered_contents.append(content)

            if system_content and filtered_contents:
                # Prepend system content to first user message
                filtered_contents[0]["parts"][0]["text"] = (
                    system_content + filtered_contents[0]["parts"][0]["text"]
                )

            payload = {
                "contents": filtered_contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                }
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
                response = await client.post(
                    url,
                    json=payload,
                    params={"key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()

                # Extract content from response
                if "candidates" not in data or not data["candidates"]:
                    raise RuntimeError("No candidates in Gemini response")

                candidate = data["candidates"][0]
                content = candidate["content"]["parts"][0]["text"]

                # Extract token usage if available
                usage = None
                if "usageMetadata" in data:
                    metadata = data["usageMetadata"]
                    usage = {
                        "prompt_tokens": metadata.get("promptTokenCount"),
                        "completion_tokens": metadata.get("candidatesTokenCount"),
                    }

                return LLMResponse(
                    content=content,
                    model=self.model,
                    provider=self.provider_name,
                    usage=usage
                )

        except httpx.HTTPError as e:
            raise RuntimeError(f"Google AI API call failed: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"Google AI request failed: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check Google AI API availability.

        Returns:
            True if API is accessible and key is valid
        """
        try:
            # Simple test with minimal tokens
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}"
                response = await client.get(
                    url,
                    params={"key": self.api_key}
                )
                response.raise_for_status()
                return True

        except Exception:
            return False

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "google"

    async def list_available_models(self) -> List[str]:
        """List available Google AI models.

        Returns:
            List of model names
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = "https://generativelanguage.googleapis.com/v1beta/models"
                response = await client.get(
                    url,
                    params={"key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()

                # Filter for generative models only
                models = []
                for model in data.get("models", []):
                    name = model.get("name", "")
                    # Extract model ID from "models/gemini-pro" format
                    if "/" in name:
                        model_id = name.split("/")[-1]
                        if "generateContent" in model.get("supportedGenerationMethods", []):
                            models.append(model_id)

                return models

        except Exception:
            return self.SUPPORTED_MODELS.copy()

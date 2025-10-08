"""LLM adapter layer for PSL.

Provides a unified interface for multiple LLM providers, replacing LiteLLM
with direct API calls to support latest models.
"""

from .base import LLMAdapter, LLMMessage, LLMResponse
from .factory import get_adapter, list_available_models

__all__ = [
    "LLMAdapter",
    "LLMMessage",
    "LLMResponse",
    "get_adapter",
    "list_available_models",
]

"""Factory for creating LLM adapters."""

from typing import Dict, List

from .anthropic_adapter import AnthropicAdapter
from .base import LLMAdapter
from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter


# Model to provider mapping
MODEL_REGISTRY: Dict[str, type[LLMAdapter]] = {}

# Register OpenAI models
for model in OpenAIAdapter.SUPPORTED_MODELS:
    MODEL_REGISTRY[model] = OpenAIAdapter

# Register Anthropic models
for model in AnthropicAdapter.SUPPORTED_MODELS:
    MODEL_REGISTRY[model] = AnthropicAdapter

# Register Ollama models (with ollama/ prefix)
for model in OllamaAdapter.SUPPORTED_MODELS:
    MODEL_REGISTRY[f"ollama/{model}"] = OllamaAdapter
    # Also support without prefix for convenience
    MODEL_REGISTRY[model] = OllamaAdapter


def get_adapter(model: str, **kwargs) -> LLMAdapter:
    """Create an appropriate adapter for the given model.

    Args:
        model: Model identifier (e.g., 'gpt-4', 'claude-sonnet-4-5-20250929', 'ollama/llama2')
        **kwargs: Additional configuration passed to the adapter

    Returns:
        Initialized LLMAdapter instance

    Raises:
        ValueError: If the model is not supported

    Examples:
        >>> adapter = get_adapter("gpt-4")
        >>> adapter = get_adapter("claude-sonnet-4-5-20250929")
        >>> adapter = get_adapter("ollama/llama2")
    """
    # Check if model is in registry
    if model in MODEL_REGISTRY:
        adapter_class = MODEL_REGISTRY[model]
        # Strip ollama/ prefix when creating Ollama adapter
        actual_model = model.replace("ollama/", "") if model.startswith("ollama/") else model
        return adapter_class(actual_model, **kwargs)

    # Try to infer provider from model name patterns
    if model.startswith("gpt-") or model.startswith("text-"):
        return OpenAIAdapter(model, **kwargs)
    elif model.startswith("claude-"):
        return AnthropicAdapter(model, **kwargs)
    elif model.startswith("ollama/") or "/" not in model:
        # Assume it's an Ollama model if it has no provider prefix
        actual_model = model.replace("ollama/", "")
        return OllamaAdapter(actual_model, **kwargs)

    raise ValueError(
        f"Unsupported model: {model}. "
        f"Supported models: {', '.join(sorted(MODEL_REGISTRY.keys()))}"
    )


def list_available_models() -> Dict[str, List[str]]:
    """List all supported models grouped by provider.

    Returns:
        Dictionary mapping provider names to lists of model names

    Example:
        >>> models = list_available_models()
        >>> print(models)
        {
            'openai': ['gpt-4', 'gpt-3.5-turbo', ...],
            'anthropic': ['claude-sonnet-4-5-20250929', ...],
            'ollama': ['ollama/llama2', 'ollama/mistral', ...]
        }
    """
    models_by_provider: Dict[str, List[str]] = {
        "openai": OpenAIAdapter.SUPPORTED_MODELS.copy(),
        "anthropic": AnthropicAdapter.SUPPORTED_MODELS.copy(),
        "ollama": [f"ollama/{m}" for m in OllamaAdapter.SUPPORTED_MODELS],
    }

    # Sort models within each provider
    for provider in models_by_provider:
        models_by_provider[provider].sort()

    return models_by_provider


def get_model_display_name(model: str) -> str:
    """Get a user-friendly display name for a model.

    Args:
        model: Model identifier

    Returns:
        Human-readable model name

    Examples:
        >>> get_model_display_name("gpt-4")
        'OpenAI: GPT-4'
        >>> get_model_display_name("claude-sonnet-4-5-20250929")
        'Anthropic: Claude Sonnet 4.5'
        >>> get_model_display_name("ollama/llama2")
        'Ollama: Llama 2'
    """
    try:
        adapter = get_adapter(model)
        provider = adapter.provider_name.title()

        # Format model name for display
        if model.startswith("gpt-"):
            name = model.replace("gpt-", "GPT-").replace("-turbo", " Turbo")
        elif model.startswith("claude-"):
            parts = model.replace("claude-", "").split("-")
            name = f"Claude {parts[0].title()}"
            if len(parts) > 1:
                name += f" {parts[1]}"
        elif model.startswith("ollama/"):
            name = model.replace("ollama/", "").title()
        else:
            name = model.title()

        return f"{provider}: {name}"
    except ValueError:
        return model

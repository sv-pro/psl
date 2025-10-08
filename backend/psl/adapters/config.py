"""Configuration loader for model registry."""

import os
from pathlib import Path
from typing import Any, Dict, List

import yaml


def load_model_config(config_path: str | None = None) -> Dict[str, Any]:
    """Load model configuration from YAML file.

    Args:
        config_path: Path to config file (defaults to models.yaml in adapters dir)

    Returns:
        Dictionary with provider configurations

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    if config_path is None:
        # Default to models.yaml in the same directory as this file
        config_path = os.path.join(os.path.dirname(__file__), "models.yaml")

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Model config file not found: {config_path}")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    if not config or "providers" not in config:
        raise ValueError("Invalid model config: missing 'providers' key")

    return config


def get_provider_models(provider: str, config: Dict[str, Any] | None = None) -> List[str]:
    """Get list of models for a specific provider.

    Args:
        provider: Provider name (e.g., 'openai', 'anthropic', 'ollama')
        config: Loaded config dict (if None, loads from default path)

    Returns:
        List of model identifiers for the provider

    Raises:
        ValueError: If provider not found in config
    """
    if config is None:
        config = load_model_config()

    providers = config.get("providers", {})
    if provider not in providers:
        raise ValueError(f"Provider '{provider}' not found in config")

    return providers[provider].get("models", [])


def get_all_providers(config: Dict[str, Any] | None = None, include_disabled: bool = False) -> Dict[str, Dict[str, Any]]:
    """Get all provider configurations.

    Args:
        config: Loaded config dict (if None, loads from default path)
        include_disabled: If True, include providers with enabled=false (default: False)

    Returns:
        Dictionary mapping provider names to their configurations
        (only enabled providers unless include_disabled=True)
    """
    if config is None:
        config = load_model_config()

    providers = config.get("providers", {})
    
    if include_disabled:
        return providers
    
    # Filter out disabled providers
    enabled_providers = {}
    for name, provider_config in providers.items():
        # Default to enabled if not specified
        if provider_config.get("enabled", True):
            enabled_providers[name] = provider_config
    
    return enabled_providers

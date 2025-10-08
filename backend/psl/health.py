"""Health check module for verifying API connectivity and model availability"""

import asyncio
import os
import httpx
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from .adapters import get_adapter, list_available_models


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNCONFIGURED = "unconfigured"
    UNKNOWN = "unknown"


@dataclass
class ModelCheck:
    """Result of a model availability check"""
    model: str
    status: HealthStatus
    message: str
    response_time_ms: Optional[float] = None


@dataclass
class ProviderCheck:
    """Result of a provider health check"""
    provider: str
    status: HealthStatus
    message: str
    api_key_configured: bool
    models_checked: List[ModelCheck]


class HealthChecker:
    """Check health of various LLM providers using adapter layer"""

    def __init__(self):
        self.timeout = httpx.Timeout(10.0)
        # Use unsorted models to test most important/latest models first
        self.available_models = list_available_models(sort=False)

    async def check_openai_async(self) -> ProviderCheck:
        """Check OpenAI API connectivity and model availability using adapter"""
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            return ProviderCheck(
                provider="OpenAI",
                status=HealthStatus.UNCONFIGURED,
                message="OPENAI_API_KEY not set in environment",
                api_key_configured=False,
                models_checked=[]
            )

        # Check first available model using adapter
        openai_models = self.available_models.get("openai", [])
        if not openai_models:
            return ProviderCheck(
                provider="OpenAI",
                status=HealthStatus.UNHEALTHY,
                message="No OpenAI models configured in models.yaml",
                api_key_configured=True,
                models_checked=[]
            )
        
        models_to_check = openai_models[:2]
        model_checks = []

        for model in models_to_check:
            try:
                adapter = get_adapter(model)
                is_healthy = await adapter.health_check()

                if is_healthy:
                    model_checks.append(ModelCheck(
                        model=model,
                        status=HealthStatus.HEALTHY,
                        message="Model available"
                    ))
                else:
                    model_checks.append(ModelCheck(
                        model=model,
                        status=HealthStatus.UNHEALTHY,
                        message="Health check failed"
                    ))
            except ValueError as e:
                # API key issue
                return ProviderCheck(
                    provider="OpenAI",
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    api_key_configured=True,
                    models_checked=[]
                )
            except Exception as e:
                model_checks.append(ModelCheck(
                    model=model,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Error: {str(e)}"
                ))

        # Determine overall status
        if any(m.status == HealthStatus.HEALTHY for m in model_checks):
            status = HealthStatus.HEALTHY
            message = "API accessible"
        else:
            status = HealthStatus.UNHEALTHY
            message = "No models available"

        return ProviderCheck(
            provider="OpenAI",
            status=status,
            message=message,
            api_key_configured=True,
            models_checked=model_checks
        )

    def check_openai(self) -> ProviderCheck:
        """Sync wrapper for OpenAI health check"""
        return asyncio.run(self.check_openai_async())

    async def check_anthropic_async(self) -> ProviderCheck:
        """Check Anthropic API connectivity and model availability using adapter"""
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            return ProviderCheck(
                provider="Anthropic",
                status=HealthStatus.UNCONFIGURED,
                message="ANTHROPIC_API_KEY not set in environment",
                api_key_configured=False,
                models_checked=[]
            )

        # Check first available model using adapter
        anthropic_models = self.available_models.get("anthropic", [])
        if not anthropic_models:
            return ProviderCheck(
                provider="Anthropic",
                status=HealthStatus.UNHEALTHY,
                message="No Anthropic models configured in models.yaml",
                api_key_configured=True,
                models_checked=[]
            )
        
        models_to_check = anthropic_models[:2]
        model_checks = []

        for model in models_to_check:
            try:
                adapter = get_adapter(model)
                is_healthy = await adapter.health_check()

                if is_healthy:
                    model_checks.append(ModelCheck(
                        model=model,
                        status=HealthStatus.HEALTHY,
                        message="Model available"
                    ))
                else:
                    model_checks.append(ModelCheck(
                        model=model,
                        status=HealthStatus.UNHEALTHY,
                        message="Health check failed"
                    ))
            except ValueError as e:
                return ProviderCheck(
                    provider="Anthropic",
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    api_key_configured=True,
                    models_checked=[]
                )
            except Exception as e:
                model_checks.append(ModelCheck(
                    model=model,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Error: {str(e)}"
                ))

        # Determine overall status
        if any(m.status == HealthStatus.HEALTHY for m in model_checks):
            status = HealthStatus.HEALTHY
            message = "API accessible"
        else:
            status = HealthStatus.UNHEALTHY
            message = "No models available"

        return ProviderCheck(
            provider="Anthropic",
            status=status,
            message=message,
            api_key_configured=True,
            models_checked=model_checks
        )

    def check_anthropic(self) -> ProviderCheck:
        """Sync wrapper for Anthropic health check"""
        return asyncio.run(self.check_anthropic_async())

    async def check_ollama_async(self) -> ProviderCheck:
        """Check Ollama connectivity and model availability using adapter"""
        base_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        model_checks: list[ModelCheck] = []

        try:
            # Fetch installed models directly from Ollama daemon
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                installed_models = {m["name"] for m in data.get("models", [])}
        except Exception as e:
            return ProviderCheck(
                provider="Ollama",
                status=HealthStatus.UNHEALTHY,
                message=f"Cannot connect to Ollama at {base_url}: {str(e)}",
                api_key_configured=True,
                models_checked=[]
            )

        # Get configured (enabled) models from models.yaml (may include disabled entries filtered earlier)
        configured_models = self.available_models.get("ollama", [])

        # If no configured models, still show installed ones (informational)
        if not configured_models:
            if not installed_models:
                return ProviderCheck(
                    provider="Ollama",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Ollama running at {base_url} but no models installed (pull one with: ollama pull mistral)",
                    api_key_configured=True,
                    models_checked=[]
                )
            for im in sorted(installed_models):
                model_checks.append(ModelCheck(
                    model=f"ollama/{im}",
                    status=HealthStatus.HEALTHY,
                    message="Installed (not declared in models.yaml)"
                ))
            return ProviderCheck(
                provider="Ollama",
                status=HealthStatus.HEALTHY,
                message=f"Ollama running at {base_url} ({len(installed_models)} installed; none explicitly configured)",
                api_key_configured=True,
                models_checked=model_checks
            )

        # For each configured model, mark installed vs missing
        healthy_any = False
        for cfg_model in configured_models:
            # Strip optional prefix for comparison
            short_cfg = cfg_model.replace("ollama/", "")
            # Match either exact tag or base name if tag omitted in config
            is_installed = any(
                im == short_cfg or im.split(":")[0] == short_cfg.split(":")[0]
                for im in installed_models
            )
            if is_installed:
                healthy_any = True
                model_checks.append(ModelCheck(
                    model=cfg_model,
                    status=HealthStatus.HEALTHY,
                    message="Installed"
                ))
            else:
                model_checks.append(ModelCheck(
                    model=cfg_model,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Not installed (pull with: ollama pull {short_cfg})"
                ))

        overall_status = HealthStatus.HEALTHY if healthy_any else HealthStatus.UNHEALTHY
        overall_message = (
            f"Ollama running at {base_url} - {sum(1 for m in model_checks if m.status == HealthStatus.HEALTHY)} / {len(model_checks)} configured models installed"
            if configured_models else f"Ollama running at {base_url}"
        )

        return ProviderCheck(
            provider="Ollama",
            status=overall_status,
            message=overall_message,
            api_key_configured=True,
            models_checked=model_checks
        )

    def check_ollama(self) -> ProviderCheck:
        """Sync wrapper for Ollama health check"""
        return asyncio.run(self.check_ollama_async())

    async def check_google_async(self) -> ProviderCheck:
        """Check Google AI (Gemini) API connectivity and model availability using adapter"""
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            return ProviderCheck(
                provider="Google AI",
                status=HealthStatus.UNCONFIGURED,
                message="GOOGLE_API_KEY not set in environment",
                api_key_configured=False,
                models_checked=[]
            )

        # Check first available model using adapter
        google_models = self.available_models.get("google", [])
        if not google_models:
            return ProviderCheck(
                provider="Google AI",
                status=HealthStatus.UNHEALTHY,
                message="No Google models configured in models.yaml",
                api_key_configured=True,
                models_checked=[]
            )
        
        models_to_check = google_models[:2]
        model_checks = []

        for model in models_to_check:
            try:
                adapter = get_adapter(model)
                is_healthy = await adapter.health_check()

                if is_healthy:
                    model_checks.append(ModelCheck(
                        model=model,
                        status=HealthStatus.HEALTHY,
                        message="Model available"
                    ))
                else:
                    model_checks.append(ModelCheck(
                        model=model,
                        status=HealthStatus.UNHEALTHY,
                        message="Health check failed"
                    ))
            except ValueError as e:
                return ProviderCheck(
                    provider="Google AI",
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    api_key_configured=True,
                    models_checked=[]
                )
            except Exception as e:
                model_checks.append(ModelCheck(
                    model=model,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Error: {str(e)}"
                ))

        # Determine overall status
        if any(m.status == HealthStatus.HEALTHY for m in model_checks):
            status = HealthStatus.HEALTHY
            message = "API accessible"
        else:
            status = HealthStatus.UNHEALTHY
            message = "No models available"

        return ProviderCheck(
            provider="Google AI",
            status=status,
            message=message,
            api_key_configured=True,
            models_checked=model_checks
        )

    def check_google(self) -> ProviderCheck:
        """Sync wrapper for Google health check"""
        return asyncio.run(self.check_google_async())

    def check_provider(self, provider_name: str) -> ProviderCheck:
        """Check a specific provider by name dynamically"""
        provider_methods = {
            "openai": self.check_openai,
            "anthropic": self.check_anthropic,
            "google": self.check_google,
            "ollama": self.check_ollama,
        }
        
        if provider_name not in provider_methods:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return provider_methods[provider_name]()

    def check_all(self) -> Dict[str, ProviderCheck]:
        """Check all providers dynamically based on models.yaml"""
        results = {}
        
        # Check all providers that have models configured
        for provider_name in self.available_models.keys():
            try:
                result = self.check_provider(provider_name)
                results[provider_name] = result
            except ValueError:
                # Provider method not implemented yet
                pass
        
        return results

    def get_available_providers(self) -> List[str]:
        """Get list of provider names from models.yaml"""
        return list(self.available_models.keys())


def format_health_report(results: Dict[str, ProviderCheck]) -> str:
    """Format health check results as a readable report"""
    lines = []
    lines.append("=" * 70)
    lines.append("PSL Health Check Report")
    lines.append("=" * 70)
    lines.append("")

    for provider_key, check in results.items():
        # Status symbol
        if check.status == HealthStatus.HEALTHY:
            symbol = "✅"
        elif check.status == HealthStatus.UNCONFIGURED:
            symbol = "⚙️ "
        else:
            symbol = "❌"

        lines.append(f"{symbol} {check.provider}")
        lines.append(f"   Status: {check.status.value}")
        lines.append(f"   Message: {check.message}")
        lines.append(f"   API Key: {'Configured' if check.api_key_configured else 'Not configured'}")

        if check.models_checked:
            lines.append(f"   Models:")
            for model in check.models_checked:
                model_symbol = "✓" if model.status == HealthStatus.HEALTHY else "✗"
                time_str = f" ({model.response_time_ms}ms)" if model.response_time_ms else ""
                lines.append(f"     {model_symbol} {model.model}: {model.message}{time_str}")

        lines.append("")

    # Summary
    healthy = sum(1 for c in results.values() if c.status == HealthStatus.HEALTHY)
    unconfigured = sum(1 for c in results.values() if c.status == HealthStatus.UNCONFIGURED)
    unhealthy = sum(1 for c in results.values() if c.status == HealthStatus.UNHEALTHY)

    lines.append("=" * 70)
    lines.append(f"Summary: {healthy} healthy, {unconfigured} unconfigured, {unhealthy} unhealthy")
    lines.append("=" * 70)

    return "\n".join(lines)

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
        self.available_models = list_available_models()

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
        models_to_check = self.available_models.get("openai", ["gpt-4"])[:2]
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
        models_to_check = self.available_models.get("anthropic", ["claude-3-5-haiku-20241022"])[:2]
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

        # Check a default model using adapter
        models_to_check = ["ollama/llama2"]
        model_checks = []

        try:
            for model in models_to_check:
                try:
                    adapter = get_adapter(model, base_url=base_url)
                    is_healthy = await adapter.health_check()

                    if is_healthy:
                        model_checks.append(ModelCheck(
                            model=model,
                            status=HealthStatus.HEALTHY,
                            message="Model available"
                        ))
                        # If one model works, also list other available models
                        if hasattr(adapter, 'list_available_models'):
                            available = await adapter.list_available_models()
                            for av_model in available[:5]:  # Limit to 5
                                if av_model != model.replace("ollama/", ""):
                                    model_checks.append(ModelCheck(
                                        model=f"ollama/{av_model}",
                                        status=HealthStatus.HEALTHY,
                                        message="Available"
                                    ))
                        break  # Success, no need to check more
                    else:
                        model_checks.append(ModelCheck(
                            model=model,
                            status=HealthStatus.UNHEALTHY,
                            message="Model not found (pull with: ollama pull llama2)"
                        ))
                except Exception as e:
                    model_checks.append(ModelCheck(
                        model=model,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Error: {str(e)}"
                    ))

            # Determine overall status
            if any(m.status == HealthStatus.HEALTHY for m in model_checks):
                status = HealthStatus.HEALTHY
                message = f"Ollama running at {base_url}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Ollama may not be running or no models available at {base_url}"

            return ProviderCheck(
                provider="Ollama",
                status=status,
                message=message,
                api_key_configured=True,
                models_checked=model_checks
            )

        except Exception as e:
            return ProviderCheck(
                provider="Ollama",
                status=HealthStatus.UNHEALTHY,
                message=f"Cannot connect to {base_url}: {str(e)}",
                api_key_configured=True,
                models_checked=[]
            )

    def check_ollama(self) -> ProviderCheck:
        """Sync wrapper for Ollama health check"""
        return asyncio.run(self.check_ollama_async())

    def check_all(self) -> Dict[str, ProviderCheck]:
        """Check all providers"""
        return {
            "openai": self.check_openai(),
            "anthropic": self.check_anthropic(),
            "ollama": self.check_ollama()
        }


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

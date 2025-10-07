"""Health check module for verifying API connectivity and model availability"""

import os
import httpx
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


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
    """Check health of various LLM providers"""

    def __init__(self):
        self.timeout = httpx.Timeout(10.0)

    def check_openai(self) -> ProviderCheck:
        """Check OpenAI API connectivity and model availability"""
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            return ProviderCheck(
                provider="OpenAI",
                status=HealthStatus.UNCONFIGURED,
                message="OPENAI_API_KEY not set in environment",
                api_key_configured=False,
                models_checked=[]
            )

        # Test connectivity with models list endpoint
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )

                if response.status_code == 200:
                    # Check specific models
                    models_to_check = ["gpt-4", "gpt-3.5-turbo"]
                    models_data = response.json().get("data", [])
                    available_models = {m["id"] for m in models_data}

                    model_checks = []
                    for model in models_to_check:
                        if model in available_models:
                            model_checks.append(ModelCheck(
                                model=model,
                                status=HealthStatus.HEALTHY,
                                message="Model available"
                            ))
                        else:
                            model_checks.append(ModelCheck(
                                model=model,
                                status=HealthStatus.UNHEALTHY,
                                message="Model not found in account"
                            ))

                    return ProviderCheck(
                        provider="OpenAI",
                        status=HealthStatus.HEALTHY,
                        message="API accessible",
                        api_key_configured=True,
                        models_checked=model_checks
                    )
                elif response.status_code == 401:
                    return ProviderCheck(
                        provider="OpenAI",
                        status=HealthStatus.UNHEALTHY,
                        message="Invalid API key",
                        api_key_configured=True,
                        models_checked=[]
                    )
                else:
                    return ProviderCheck(
                        provider="OpenAI",
                        status=HealthStatus.UNHEALTHY,
                        message=f"API error: {response.status_code}",
                        api_key_configured=True,
                        models_checked=[]
                    )
        except httpx.TimeoutException:
            return ProviderCheck(
                provider="OpenAI",
                status=HealthStatus.UNHEALTHY,
                message="Connection timeout",
                api_key_configured=True,
                models_checked=[]
            )
        except Exception as e:
            return ProviderCheck(
                provider="OpenAI",
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}",
                api_key_configured=True,
                models_checked=[]
            )

    def check_anthropic(self) -> ProviderCheck:
        """Check Anthropic API connectivity and model availability"""
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            return ProviderCheck(
                provider="Anthropic",
                status=HealthStatus.UNCONFIGURED,
                message="ANTHROPIC_API_KEY not set in environment",
                api_key_configured=False,
                models_checked=[]
            )

        # Test with a minimal API call
        models_to_check = ["claude-3-5-haiku-20241022"]
        model_checks = []

        for model in models_to_check:
            try:
                import time
                start = time.time()

                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        },
                        json={
                            "model": model,
                            "max_tokens": 10,
                            "messages": [{"role": "user", "content": "Hi"}]
                        }
                    )

                    elapsed = (time.time() - start) * 1000

                    if response.status_code == 200:
                        model_checks.append(ModelCheck(
                            model=model,
                            status=HealthStatus.HEALTHY,
                            message="Model available",
                            response_time_ms=round(elapsed, 2)
                        ))
                    elif response.status_code == 404:
                        model_checks.append(ModelCheck(
                            model=model,
                            status=HealthStatus.UNHEALTHY,
                            message="Model not found"
                        ))
                    elif response.status_code == 401:
                        return ProviderCheck(
                            provider="Anthropic",
                            status=HealthStatus.UNHEALTHY,
                            message="Invalid API key",
                            api_key_configured=True,
                            models_checked=[]
                        )
                    else:
                        error_data = response.json()
                        model_checks.append(ModelCheck(
                            model=model,
                            status=HealthStatus.UNHEALTHY,
                            message=f"Error: {error_data.get('error', {}).get('message', 'Unknown')}"
                        ))
            except httpx.TimeoutException:
                return ProviderCheck(
                    provider="Anthropic",
                    status=HealthStatus.UNHEALTHY,
                    message="Connection timeout",
                    api_key_configured=True,
                    models_checked=[]
                )
            except Exception as e:
                return ProviderCheck(
                    provider="Anthropic",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Error: {str(e)}",
                    api_key_configured=True,
                    models_checked=[]
                )

        # Overall status based on model checks
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

    def check_ollama(self) -> ProviderCheck:
        """Check Ollama connectivity and model availability"""
        base_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                # Check if Ollama is running
                response = client.get(f"{base_url}/api/tags")

                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])

                    if not models:
                        return ProviderCheck(
                            provider="Ollama",
                            status=HealthStatus.HEALTHY,
                            message="Ollama running but no models installed",
                            api_key_configured=True,
                            models_checked=[]
                        )

                    model_checks = [
                        ModelCheck(
                            model=m["name"],
                            status=HealthStatus.HEALTHY,
                            message=f"Available (size: {m.get('size', 'unknown')})"
                        )
                        for m in models[:5]  # Limit to first 5
                    ]

                    return ProviderCheck(
                        provider="Ollama",
                        status=HealthStatus.HEALTHY,
                        message=f"Ollama running with {len(models)} model(s)",
                        api_key_configured=True,
                        models_checked=model_checks
                    )
                else:
                    return ProviderCheck(
                        provider="Ollama",
                        status=HealthStatus.UNHEALTHY,
                        message=f"Unexpected status: {response.status_code}",
                        api_key_configured=True,
                        models_checked=[]
                    )
        except httpx.ConnectError:
            return ProviderCheck(
                provider="Ollama",
                status=HealthStatus.UNHEALTHY,
                message=f"Cannot connect to {base_url}. Is Ollama running?",
                api_key_configured=True,
                models_checked=[]
            )
        except httpx.TimeoutException:
            return ProviderCheck(
                provider="Ollama",
                status=HealthStatus.UNHEALTHY,
                message="Connection timeout",
                api_key_configured=True,
                models_checked=[]
            )
        except Exception as e:
            return ProviderCheck(
                provider="Ollama",
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}",
                api_key_configured=True,
                models_checked=[]
            )

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

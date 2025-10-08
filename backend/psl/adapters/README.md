# LLM Adapter Layer

This directory contains the adapter layer for integrating multiple LLM providers with PSL.

## Architecture

The adapter layer uses a **factory pattern** with **YAML-based configuration** to support multiple LLM providers:

- **Base Interface** ([base.py](base.py)) - Abstract `LLMAdapter` class that all adapters implement
- **Provider Adapters** - Concrete implementations for each provider
- **Factory** ([factory.py](factory.py)) - Creates adapter instances based on model name
- **Config Loader** ([config.py](config.py)) - Loads model registry from YAML

## Configuration

### Model Registry (models.yaml)

The [models.yaml](models.yaml) file defines all supported models and their provider mappings. This allows you to **add or remove models without changing code**.

**Structure:**

```yaml
providers:
  provider_name:
    adapter_class: AdapterClassName
    description: Human-readable description
    prefix: optional/prefix/  # For models like ollama/llama2
    models:
      - model-id
      - model-id:variant
```

**Example:**

```yaml
providers:
  openai:
    adapter_class: OpenAIAdapter
    description: OpenAI GPT models via native SDK
    models:
      - gpt-4
      - gpt-3.5-turbo

  anthropic:
    adapter_class: AnthropicAdapter
    description: Anthropic Claude models via native SDK
    models:
      - claude-sonnet-4-5-20250929
      - claude-3-5-sonnet-20241022

  ollama:
    adapter_class: OllamaAdapter
    description: Local models via Ollama
    prefix: ollama/
    models:
      - llama2
      - mistral
      - gemma
```

### Adding New Models

To add support for a new model:

1. **Edit [models.yaml](models.yaml)**:
   ```yaml
   providers:
     openai:
       models:
         - gpt-4
         - gpt-4o  # ← Add new model here
   ```

2. **Restart the backend** - The factory automatically loads the updated config

3. **Verify** the model appears:
   ```bash
   make list-models
   # or
   python -m psl.cli list-models
   ```

No code changes needed!

### Adding New Providers

To add a completely new provider:

1. **Create adapter class** (e.g., `cohere_adapter.py`):
   ```python
   from .base import LLMAdapter, LLMMessage, LLMResponse

   class CohereAdapter(LLMAdapter):
       SUPPORTED_MODELS = ["command", "command-light"]

       async def complete(self, messages, temperature, max_tokens, **kwargs):
           # Implement provider-specific API call
           pass

       async def health_check(self):
           # Implement health check
           pass
   ```

2. **Register in factory** ([factory.py](factory.py)):
   ```python
   from .cohere_adapter import CohereAdapter

   ADAPTER_CLASSES = {
       "CohereAdapter": CohereAdapter,
       # ... other adapters
   }
   ```

3. **Add to config** ([models.yaml](models.yaml)):
   ```yaml
   providers:
     cohere:
       adapter_class: CohereAdapter
       description: Cohere models
       models:
         - command
         - command-light
   ```

## Provider-Specific Adapters

### OpenAI Adapter

**File:** [openai_adapter.py](openai_adapter.py)

- Uses native `openai` SDK (v1.x)
- Requires `OPENAI_API_KEY` environment variable
- Supports GPT-4, GPT-3.5-turbo variants

### Anthropic Adapter

**File:** [anthropic_adapter.py](anthropic_adapter.py)

- Uses native `anthropic` SDK
- Requires `ANTHROPIC_API_KEY` environment variable
- Supports Claude 3, Claude 3.5, Claude Sonnet 4.5

### Google Adapter

**File:** [google_adapter.py](google_adapter.py)

- Uses direct REST API calls via `httpx`
- Requires `GOOGLE_API_KEY` environment variable
- Supports Gemini Pro, Gemini 1.5 Pro, Gemini 1.5 Flash
- Handles system message conversion (Gemini doesn't have explicit system role)

### Ollama Adapter

**File:** [ollama_adapter.py](ollama_adapter.py)

- Uses `httpx` for direct HTTP calls to local Ollama instance
- No API key required (local service)
- Configurable base URL via `OLLAMA_API_BASE` (default: `http://localhost:11434`)
- Supports Llama 2, Mistral, Mixtral, Gemma, CodeLlama, Phi, Neural Chat

## Usage

### Factory Pattern

```python
from psl.adapters.factory import get_adapter, list_available_models

# Get an adapter for a specific model
adapter = get_adapter("gpt-4", api_key="sk-...")

# Use the adapter
response = await adapter.complete(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    max_tokens=150
)

print(response.content)
```

### List Available Models

```python
from psl.adapters.factory import list_available_models

models = list_available_models()
# {
#   "openai": ["gpt-4", "gpt-3.5-turbo", ...],
#   "anthropic": ["claude-sonnet-4-5-20250929", ...],
#   "ollama": ["ollama/llama2", "ollama/mistral", ...]
# }
```

### Health Checks

```python
adapter = get_adapter("gpt-4")
is_healthy = await adapter.health_check()

if is_healthy:
    print("Provider is available")
```

## Config Fallback

If the `models.yaml` file is missing or invalid, the factory falls back to **hardcoded model lists** in each adapter class (`SUPPORTED_MODELS`). This ensures the system remains functional even if the config file is corrupted.

## Testing

Model configuration is tested via:
- Unit tests in `tests/test_adapters.py`
- Health check CLI: `python -m psl.cli healthcheck`
- Integration tests with real API calls (not mocked)

## API Keys

Configure provider API keys in `backend/.env`:

```bash
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OLLAMA_API_BASE=http://localhost:11434  # Optional
```

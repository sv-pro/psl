# Health Check System

PSL includes a built-in health check system to verify API connectivity and model availability before running the linter.

## Quick Start

```bash
cd backend
make healthcheck
```

## Commands

| Command | Description |
|---------|-------------|
| `make healthcheck` | Check all providers (OpenAI, Anthropic, Ollama) |
| `make check-openai` | Check only OpenAI API |
| `make check-anthropic` | Check only Anthropic API |
| `make check-ollama` | Check only Ollama (local models) |
| `make list-models` | List all available models from all providers |

## CLI Usage

The health check system is also available as a standalone CLI tool:

```bash
# Check all providers
python -m psl.cli healthcheck

# Strict mode (fail if ANY provider is unhealthy)
python -m psl.cli healthcheck --strict

# Check specific provider
python -m psl.cli check openai
python -m psl.cli check anthropic
python -m psl.cli check ollama

# List available models
python -m psl.cli list-models
```

## Example Output

```
======================================================================
PSL Health Check Report
======================================================================

✅ OpenAI
   Status: healthy
   Message: API accessible
   API Key: Configured
   Models:
     ✓ gpt-4: Model available
     ✓ gpt-3.5-turbo: Model available

✅ Anthropic
   Status: healthy
   Message: API accessible
   API Key: Configured
   Models:
     ✓ claude-3-5-haiku-20241022: Model available (1297.76ms)

❌ Ollama
   Status: unhealthy
   Message: Cannot connect to http://localhost:11434. Is Ollama running?
   API Key: Configured

======================================================================
Summary: 2 healthy, 0 unconfigured, 1 unhealthy
======================================================================
```

## Status Indicators

| Symbol | Status | Meaning |
|--------|--------|---------|
| ✅ | `healthy` | Provider is accessible and models are available |
| ⚙️ | `unconfigured` | API key not configured in `.env` |
| ❌ | `unhealthy` | Provider has errors (connectivity, auth, etc.) |

## What Gets Checked

### OpenAI
- API key validity
- Connectivity to `api.openai.com`
- Availability of `gpt-4` and `gpt-3.5-turbo`

### Anthropic
- API key validity
- Connectivity to `api.anthropic.com`
- Availability and response time of `claude-3-5-haiku-20241022`

### Ollama
- Connectivity to local Ollama instance (default: `http://localhost:11434`)
- List of installed models
- Model sizes

## Integration with Setup

Health checks run automatically during `make init`:

```bash
cd backend
make init

# Output includes:
# - Virtual environment setup
# - Dependency installation
# - Automatic health check
# - Configuration tips
```

## Programmatic Usage

You can use the health check system in your own Python code:

```python
from psl.health import HealthChecker, HealthStatus, format_health_report

# Create checker
checker = HealthChecker()

# Check all providers
results = checker.check_all()

# Print formatted report
print(format_health_report(results))

# Check individual providers
openai_check = checker.check_openai()
anthropic_check = checker.check_anthropic()
ollama_check = checker.check_ollama()

# Access results
if openai_check.status == HealthStatus.HEALTHY:
    print("OpenAI is ready!")
    for model in openai_check.models_checked:
        print(f"  - {model.model}: {model.message}")
```

## Troubleshooting

### "UNCONFIGURED" Status

**Problem:** API key not set

**Solution:**
```bash
cd backend
cp .env.example .env
# Edit .env and add your API keys
```

### "UNHEALTHY - Invalid API key"

**Problem:** API key is incorrect or expired

**Solution:**
- OpenAI: Get new key from https://platform.openai.com/api-keys
- Anthropic: Get new key from https://console.anthropic.com/settings/keys
- Update `backend/.env` with new key

### "Cannot connect to Ollama"

**Problem:** Ollama not running

**Solution:**
```bash
# Start Ollama
ollama serve

# Or use the Ollama app

# Verify it's running
curl http://localhost:11434/api/tags
```

### "Connection timeout"

**Problem:** Network issues or firewall

**Solution:**
- Check internet connection
- Try disabling VPN
- Check firewall settings
- Verify you can access the API directly:
  ```bash
  curl https://api.openai.com/v1/models
  curl https://api.anthropic.com/v1/messages
  ```

## Exit Codes

The health check CLI returns appropriate exit codes:

| Exit Code | Meaning |
|-----------|---------|
| 0 | At least one provider is healthy |
| 1 | All configured providers are unhealthy |
| 130 | Interrupted by user (Ctrl+C) |

In `--strict` mode:
- Returns 1 if ANY provider is unhealthy
- Useful for CI/CD pipelines

## See Also

- [README.md](README.md) - Quick start guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed troubleshooting
- [backend/.env.example](backend/.env.example) - Environment configuration

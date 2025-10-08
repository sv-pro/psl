# PSL (Prompt Semantic Linter) - AI Coding Agent Guide

## Project Philosophy: A.G.I.L.E. Architecture

PSL demonstrates **building reliable AI systems from unreliable components** through compositional validation:

```
User Prompt → Semantic Parser (LLM) → Structured IR → Validation Rules (deterministic) → Feedback
                   ↓ unreliable                              ↓ reliable
```

Even if the parser LLM misinterprets, rule-based validation catches semantic issues deterministically. This pattern is core to IntentHub's philosophy of **layered reliability**.

## Three-Tier Architecture

1. **Semantic Parser** (`backend/psl/parser.py`) - LLM converts prompts to structured IR
2. **Validator** (`backend/psl/validator.py`) - Deterministic rules check IR for issues  
3. **Didactic Evaluator** (`backend/psl/evaluation.py`) - Tests if prompts demonstrate expected behavior

All three stages use the **custom adapter layer** (`backend/psl/adapters/`) - not LiteLLM.

## Critical Patterns

### IR Schema (`backend/psl/ir.py`)
The Intermediate Representation uses Pydantic models:
- `ComputedField` - Fields requiring computation (has_definition, definition, source_fields)
- `Constraint` - Output requirements (type, value, conflicts_with)
- `DomainTerm` - Technical jargon (term, defined, definition, is_standard)
- `IR` - Top-level with fallback_strategy: "null" | "error" | "default" | "unspecified"

**All validation rules operate on IR, not raw prompt text.**

### Custom Adapter Layer (Not LiteLLM)
Located in `backend/psl/adapters/`:
- `base.py` - Abstract `LLMAdapter` with `complete()` and `health_check()`
- Provider implementations: `openai_adapter.py`, `anthropic_adapter.py`, `google_adapter.py`, `ollama_adapter.py`
- `factory.py` - `get_adapter(model_name)` returns appropriate adapter
- **`models.yaml`** - Add/remove models without code changes
- Use `factory.get_adapter()` for all LLM calls, never direct SDK imports in business logic

### Rules System (`backend/psl/rules/`)
Each rule extends `Rule` from `base.py`:
```python
class MyRule(Rule):
    @property
    def name(self) -> str: return "my-rule"
    
    def check(self, ir: IR) -> List[LintError]:
        # Validate IR, return LintError list
```

Currently only `NoUndefinedComputedFieldsRule` exists. Add new rules by creating files in `rules/` and registering in `validator.py`.

### Didactic Evaluation Logic
Bad prompt + hallucination → ✅ Success (proves PSL's value)  
Good prompt + correct output → ✅ Success (solution works)  
Bad prompt + no hallucination → ❌ Failure (model too conservative)  
Good prompt + hallucination → ❌ Failure (model unreliable)

See `DidacticEvaluator._evaluate_didactic_outcome()` in `evaluation.py`.

## Development Workflows

### Environment Setup
**Always use project Makefiles, not manual commands:**
```bash
# Root level - run both frontend + backend
make dev              # Starts both servers in parallel
make install          # Install all dependencies

# Backend only
cd backend
make init             # Full setup: venv + deps + healthcheck
make test             # Run pytest (checks env first)
make healthcheck      # Verify API keys and model availability
make list-models      # See all 26 supported models
```

**Python Environment:** Project uses pyenv with virtualenv `psl-env` (Python 3.13). If `pyenv activate psl-env` fails, use `pyenv local psl-env` or direct activation via `~/.pyenv/versions/3.13.0/envs/psl-env/bin/activate`.

### API Endpoints (`backend/psl/api.py`)
- `POST /lint` - Takes `{prompt: str, model: str}`, returns `{ir: IR, errors: List[LintError], summary: dict}`
- `POST /execute` - Takes `{prompt: str, context: str, model: str}`, returns `{output: str, model: str}`
- `POST /evaluate` - Takes `{example_ids?: string[], models?: string[]}`, runs didactic evaluation matrix
- `GET /models` - Lists all available models grouped by provider
- `GET /examples` - Loads prompt examples from `backend/psl/examples/`

### Frontend Architecture
**Monolithic UI:** All code in `frontend/src/App.tsx` (no separate components).
- Monaco Editor for prompt/context editing
- Three-column input layout (Prompt | Context | Actions)
- Two-column results (Lint Errors | LLM Output)
- Example loader with 8 curated prompts (4 bad, 4 fixed)
- Model selector with provider grouping

## Adding Features

### New Validation Rule
1. Create `backend/psl/rules/my_rule.py` extending `Rule`
2. Import in `backend/psl/rules/__init__.py`
3. Add to `Validator.rules` list in `validator.py`
4. Add fixtures in `tests/fixtures/bad_prompts/` and `good_prompts/`
5. Write tests in `tests/test_rules.py`

### New LLM Provider
1. Create adapter in `backend/psl/adapters/my_provider_adapter.py` implementing `LLMAdapter`
2. Add to `models.yaml`:
   ```yaml
   providers:
     my_provider:
       enabled: true  # Optional: set to false to disable
       adapter_class: MyProviderAdapter
       description: "My provider models"
       models: [model-1, model-2]
   ```
3. Add health check method in `backend/psl/health.py` following the pattern of existing providers
4. Restart backend (no code changes needed in factory)

### Disabling Models
Disable specific models without removing them from `models.yaml`:
```yaml
providers:
  ollama:
    models:
      - mistral:latest           # String format (always enabled)
      - name: llama2             # Object format with enabled flag
        enabled: false           # Disabled - won't be checked or listed
```

### New Example Prompt
1. Add prompt to `backend/psl/examples/bad/` or `good/`
2. Add context to `backend/psl/examples/contexts/`
3. Register in `backend/psl/examples/metadata.json`:
   ```json
   {
     "id": "my_example",
     "name": "Display Name",
     "category": "Category",
     "type": "bad" | "good",
     "prompt_file": "bad/my_example.txt",
     "context_file": "contexts/my_example_context.txt",
     "expected_behavior": "What should happen"
   }
   ```

## Testing

Run via `make test` (checks environment) or `pytest tests/ -v` directly.

Test structure:
- `conftest.py` - Fixtures for rules, validator, sample prompts
- `test_rules.py` - Unit tests for each validation rule
- Fixtures in `tests/fixtures/bad_prompts/` and `good_prompts/`

**When adding rules, always add corresponding test fixtures.**

## Key Files Reference

- **Core Logic:** `parser.py`, `validator.py`, `evaluation.py`, `ir.py`
- **API:** `api.py` (FastAPI), `main.py` (entry point)
- **Adapters:** `adapters/factory.py`, `adapters/models.yaml`, `adapters/base.py`
- **Rules:** `rules/hallucination.py` (only rule currently)
- **CLI:** `cli.py` (health checks, model listing)
- **Examples:** `examples/metadata.json` (example registry)
- **Docs:** `CLAUDE.md` (detailed agent guide), `PITCH.md` (value proposition), `psl_project_spec.md` (full spec)

## Common Pitfalls

1. **Never import LLM SDKs directly** - Always use `get_adapter()` from factory
2. **Rules operate on IR, not prompt text** - Parser converts first
3. **Use Makefiles for commands** - They handle environment checking
4. **API keys in `backend/.env`** - Copy from `.env.example`, never commit
5. **CORS configured for localhost:5173** - Frontend must run on Vite default port
6. **Hallucination detection is heuristic** - See `_detect_hallucination()` in `evaluation.py`
7. **Didactic scoring is inverted** - Bad prompts *should* cause issues to prove value
8. **Provider system is dynamic** - `models.yaml` controls which providers are active (use `enabled: false` to disable)
9. **Model order matters** - Health checks test first 2 models from `models.yaml` in original order (not sorted)

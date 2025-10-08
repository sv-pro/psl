# Prompt Semantic Linter (PSL)

**Measure what matters. Build what lasts. Benchmark what's real.**

PSL is a multi-purpose platform that simultaneously:

1. **Measures Prompt Quality** - Detects semantic issues that cause hallucinations (utility) and validates prompts demonstrate their quality (didactic)
2. **Demonstrates IntentHub's A.G.I.L.E. Philosophy** - Building reliable AI systems through compositional validation of unreliable components
3. **Benchmarks Models Fairly** - Compares models using quality-controlled prompts with known expected behaviors

See [PITCH.md](PITCH.md) for the complete value proposition.

## Demo

**Interactive UI** with 8 curated prompt examples:
- Load bad prompts → see lint errors → execute → observe hallucinations
- Load fixed prompts → no errors → execute → correct output
- Compare across 19 models (OpenAI, Anthropic, Ollama)
- Run didactic evaluation matrix to see which models demonstrate PSL's value

## Quick Start

### Prerequisites

This project requires Python 3.11+ and Node.js 18+. We recommend using `pyenv` for Python version management.

### Easy Way (Recommended)

From the project root, run both backend and frontend together:

```bash
# Install all dependencies
make install

# Configure API keys
cp backend/.env.example backend/.env
# Edit backend/.env and add your ANTHROPIC_API_KEY or OPENAI_API_KEY

# Run both servers in parallel
make dev
```

This will start:
- Backend at `http://localhost:8000`
- Frontend at `http://localhost:5173`

### Manual Setup

#### Backend Setup

#### Option 1: Using pyenv (Recommended)

```bash
cd backend

# Create a virtual environment for this project
pyenv virtualenv 3.13.0 psl-env

# Activate the environment (one of these methods will work):
pyenv activate psl-env
# OR if pyenv-virtualenv isn't loaded in your shell:
source ~/.pyenv/versions/3.13.0/envs/psl-env/bin/activate
# OR simply:
pyenv local psl-env

# Install dependencies
pip install -r requirements.txt

# Set up API keys
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY or OPENAI_API_KEY

# Run server
python main.py
```

#### Option 2: Using venv (Standard Python)

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Set up API keys
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY or OPENAI_API_KEY

# Run server
python main.py
```

**Note on pyenv activation**: If `pyenv activate` doesn't work, it means pyenv-virtualenv plugin isn't loaded in your shell. You can either:

- Load it in your `.bashrc`/`.zshrc`: `eval "$(pyenv virtualenv-init -)"`
- Use the direct activation: `source ~/.pyenv/versions/3.13.0/envs/psl-env/bin/activate`
- Use `pyenv local psl-env` to set it for the directory

Server will be running at `http://localhost:8000`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend will be running at `http://localhost:5173`

## Supported Models (19 total)

PSL uses a **custom adapter layer** with direct API calls (no LiteLLM dependency) for maximum compatibility with latest models.

### OpenAI (via `openai` SDK)

- `gpt-4`, `gpt-4-turbo`, `gpt-4-turbo-preview`
- `gpt-3.5-turbo`, `gpt-3.5-turbo-16k`

Requires `OPENAI_API_KEY` in `backend/.env`

### Anthropic (via `anthropic` SDK)

- `claude-sonnet-4-5-20250929` ✨ **Latest model - fully supported**
- `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`
- `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`

Requires `ANTHROPIC_API_KEY` in `backend/.env`

### Ollama (via `httpx` for local models)

- `ollama/llama2`, `ollama/llama2:13b`, `ollama/llama2:70b`
- `ollama/mistral`, `ollama/mixtral`, `ollama/codellama`
- `ollama/phi`, `ollama/neural-chat`

Requires Ollama running locally. Configure `OLLAMA_API_BASE=http://localhost:11434` in `backend/.env` (optional).

**Model Selection:** All models available in UI dropdown, organized by provider. Use `make list-models` to see full list.

## Troubleshooting

See documentation:
- [HEALTH_CHECK.md](HEALTH_CHECK.md) - Health check system guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed troubleshooting

### Quick Fixes

### Python 3.13 Installation Issues

If you encounter build errors with `pydantic-core` on Python 3.13, try one of these solutions:

#### Option 1: Use Python 3.11 (Recommended)

```bash
cd backend
rm -rf venv  # or deactivate and remove pyenv virtualenv
pyenv virtualenv 3.11.13 psl-env
pyenv local psl-env
pip install --upgrade pip
pip install -r requirements.txt
```

#### Option 2: Install Rust toolchain

```bash
# Install Rust (required for compiling pydantic-core from source)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Then retry installation
pip install --upgrade pip
pip install -r requirements.txt
```

#### Option 3: Use pre-release wheels

```bash
pip install --upgrade pip
pip install --pre pydantic-core pydantic
pip install -r requirements.txt
```

## Health Checks

Verify API connectivity and model availability:

```bash
cd backend

# Check all providers
make healthcheck

# Check specific provider
make check-openai
make check-anthropic
make check-ollama

# List available models
make list-models
```

The health check verifies:
- ✅ API keys are configured correctly
- ✅ Providers are accessible
- ✅ Models are available in your account
- ✅ Response times for each model


## Testing

```bash
cd backend
make test       # Checks environment and runs tests
# OR
pytest tests/   # Run directly
```

## How It Works

The UI provides three columns:
1. **System Prompt** - The prompt template to analyze
2. **Context/Input** - Example data to test with (e.g., Kubernetes manifest)
3. **Actions** - Lint, Execute, or both

Results are displayed side-by-side:
- **Lint Results** - Semantic issues detected in the prompt
- **Actual LLM Output** - What the model actually produces (to see hallucinations in action)

### Architecture

PSL demonstrates **A.G.I.L.E. principles** (Auditable, Gradual, Interpretable, Layered, Explicit):

1. **Semantic Parser** - Uses LLM to convert prompts into structured IR (Intermediate Representation)
2. **Validator** - Runs deterministic linting rules on the IR
3. **Didactic Evaluator** - Tests prompts × models to measure demonstration effectiveness
4. **LLM Adapter Layer** - Unified interface across OpenAI, Anthropic, Ollama

**Key Components:**

- **8 Prompt Examples** - 4 bad, 4 good (K8s, finance, code, sentiment)
- **Didactic Scoring** - Bad prompt + hallucination = ✅ (proves PSL's value)
- **Model Benchmarking** - Compare 19 models using quality-controlled prompts
- **API Endpoints** - `/lint`, `/execute`, `/evaluate`, `/models`, `/examples`

## Current Rules

- ✅ **no-undefined-computed-fields** - Detects computed fields that will cause hallucinations

## Features

✅ **Implemented:**

- Custom LLM adapter layer (OpenAI, Anthropic, Ollama)
- 19 models supported with latest versions
- 8 curated prompt examples (good and bad)
- Didactic evaluation system
- Model benchmarking with quality-controlled prompts
- Interactive UI with example/model dropdowns
- Health check system
- Real-time lint + execute workflow

🔨 **Roadmap:**

- [ ] Additional linting rules (conflicting constraints, ambiguous requirements)
- [ ] Auto-fix suggestions
- [ ] VS Code extension
- [ ] CI/CD integration
- [ ] Expanded didactic evaluation metrics

## License

MIT

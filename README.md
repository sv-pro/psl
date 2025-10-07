# Prompt Semantic Linter

A tool to detect semantic issues in LLM prompts that lead to hallucinations and unpredictable behavior.

## Demo

Try the Kubernetes metrics example to see how PSL catches undefined computed fields that cause LLMs to hallucinate numbers.

## Quick Start

### Prerequisites

This project requires Python 3.11+ and Node.js 18+. We recommend using `pyenv` for Python version management.

### Backend Setup

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

## Supported Models

### OpenAI Models
- `gpt-4` - GPT-4 (recommended, most reliable)
- `gpt-3.5-turbo` - GPT-3.5 Turbo (faster, cheaper)

Requires `OPENAI_API_KEY` in `backend/.env`

### Anthropic Claude Models (2025)
- `claude-sonnet-4-5-20250929` - Claude Sonnet 4.5 (latest, most capable)
- `claude-3-7-sonnet-20250219` - Claude Sonnet 3.7
- `claude-3-5-haiku-20241022` - Claude Haiku 3.5 (fast & cost-efficient)

Requires `ANTHROPIC_API_KEY` in `backend/.env`

**Note**: Model names change over time. For the latest official model names, see:
- OpenAI: https://platform.openai.com/docs/models
- Anthropic: https://docs.anthropic.com/en/docs/about-claude/models

### Local Models
- `ollama/llama2` - Llama 2 via Ollama (requires Ollama running locally)
- Configure `OLLAMA_API_BASE=http://localhost:11434` in `backend/.env`

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions to common issues.

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

## Testing

```bash
cd backend
make test       # Checks environment and runs tests
# OR
pytest tests/   # Run directly
```

## How It Works

1. **Semantic Parser** - Converts natural language prompts into structured IR (Intermediate Representation)
2. **Validator** - Runs linting rules on the IR
3. **Rules** - Detect specific issues:
   - `no-undefined-computed-fields` - Catches metrics/fields without definitions

## Current Rules

- ✅ **no-undefined-computed-fields** - Detects computed fields that will cause hallucinations

## Roadmap

- [ ] Add more rules (conflicting constraints, ambiguous requirements)
- [ ] Auto-fix suggestions
- [ ] VS Code extension
- [ ] CI/CD integration

## License

MIT

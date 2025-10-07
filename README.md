# Prompt Semantic Linter

A tool to detect semantic issues in LLM prompts that lead to hallucinations and unpredictable behavior.

## Demo

Try the Kubernetes metrics example to see how PSL catches undefined computed fields that cause LLMs to hallucinate numbers.

## Quick Start

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up API keys
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY or OPENAI_API_KEY

# Run server
python main.py
```

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

## Testing

```bash
cd backend
pytest tests/
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

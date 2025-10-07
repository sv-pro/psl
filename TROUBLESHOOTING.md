# Troubleshooting Guide

This document covers common issues and their solutions encountered during setup and development of the Prompt Semantic Linter.

## Table of Contents

- [Backend Issues](#backend-issues)
  - [pytest-asyncio Not Working](#pytest-asyncio-not-working)
  - [Environment Variables Not Loading](#environment-variables-not-loading)
  - [API Key Errors](#api-key-errors)
  - [Uvicorn Reload Warning](#uvicorn-reload-warning)
  - [Virtual Environment Not Activated](#virtual-environment-not-activated)
- [Frontend Issues](#frontend-issues)
  - [Tailwind CSS PostCSS Plugin Error](#tailwind-css-postcss-plugin-error)
  - [Module Export Errors](#module-export-errors)
  - [API Connection Errors](#api-connection-errors)
- [Model-Specific Issues](#model-specific-issues)
  - [Claude Model 404 Errors](#claude-model-404-errors)
  - [OpenAI Authentication Errors](#openai-authentication-errors)

---

## Backend Issues

### pytest-asyncio Not Working

**Symptoms:**
```
FAILED tests/test_rules.py::test_bad_k8s_prompt - Failed: async def functions are not natively supported.
PytestUnknownMarkWarning: Unknown pytest.mark.asyncio
```

**Root Cause:**
- Tests were marked as `async` but didn't actually use any async operations
- `pytest-asyncio` configuration was missing or incorrect

**Solution:**

1. **Remove async decorators** from tests that don't need them:
```python
# Before
@pytest.mark.asyncio
async def test_bad_k8s_prompt():
    ...

# After
def test_bad_k8s_prompt():
    ...
```

2. **Create/update pytest.ini**:
```ini
[pytest]
filterwarnings =
    ignore::UserWarning:pydantic.main
    ignore::DeprecationWarning:litellm._service_logger
```

3. **Create tests/conftest.py** to load environment variables:
```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory
backend_dir = Path(__file__).parent.parent
env_file = backend_dir / ".env"
load_dotenv(env_file)
```

**Files Changed:**
- `backend/tests/test_rules.py` - Removed async decorators
- `backend/pytest.ini` - Added warning filters
- `backend/tests/conftest.py` - Created for env loading

---

### Environment Variables Not Loading

**Symptoms:**
```
litellm.AuthenticationError: Missing Anthropic API Key
```

**Root Cause:**
The main.py file wasn't loading the `.env` file, so API keys weren't available to the application.

**Solution:**

Add dotenv loading to `backend/main.py`:

```python
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    uvicorn.run("psl.api:app", host="0.0.0.0", port=8000, reload=True)
```

**Files Changed:**
- `backend/main.py` - Added `load_dotenv()` call

---

### API Key Errors

**Symptoms:**
- `AuthenticationError: OpenAIException - The api_key client option must be set`
- `AuthenticationError: Missing Anthropic API Key`

**Solution:**

1. **Verify .env file exists** in `backend/` directory:
```bash
cd backend
ls -la .env
```

2. **Check .env contains valid keys**:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
OPENAI_API_KEY=sk-proj-xxxxx
```

3. **Get new API keys if needed**:
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys

4. **Restart the backend server** after updating .env:
```bash
# Kill existing server (Ctrl+C)
python main.py
```

---

### Uvicorn Reload Warning

**Symptoms:**
```
WARNING: You must pass the application as an import string to enable 'reload' or 'workers'.
```

**Root Cause:**
Uvicorn's reload feature requires the app to be passed as an import string, not as an object.

**Solution:**

Change `backend/main.py`:

```python
# Before
from psl.api import app
uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

# After
uvicorn.run("psl.api:app", host="0.0.0.0", port=8000, reload=True)
```

**Files Changed:**
- `backend/main.py` - Changed to import string

---

### Virtual Environment Not Activated

**Symptoms:**
```
⚠️  Warning: psl-env is not activated!
```

**Solution:**

Choose one of these activation methods:

**Option 1: pyenv activate (if pyenv-virtualenv is loaded)**
```bash
pyenv activate psl-env
```

**Option 2: Direct activation**
```bash
source ~/.pyenv/versions/3.13.0/envs/psl-env/bin/activate
```

**Option 3: pyenv local (recommended)**
```bash
cd backend
pyenv local psl-env  # Auto-activates when you cd into directory
```

**Verify activation:**
```bash
which python
# Should show: ~/.pyenv/versions/3.13.0/envs/psl-env/bin/python
```

---

## Frontend Issues

### Tailwind CSS PostCSS Plugin Error

**Symptoms:**
```
[postcss] It looks like you're trying to use `tailwindcss` directly as a PostCSS plugin.
The PostCSS plugin has moved to a separate package
```

**Root Cause:**
Tailwind CSS v4 changed its architecture. The PostCSS plugin is now in a separate package `@tailwindcss/postcss`.

**Solution:**

1. **Install the PostCSS plugin**:
```bash
cd frontend
npm install -D @tailwindcss/postcss
```

2. **Update postcss.config.js**:
```javascript
export default {
  plugins: {
    '@tailwindcss/postcss': {},  // Changed from 'tailwindcss'
    autoprefixer: {},
  },
}
```

3. **Update src/index.css** to use Tailwind v4 syntax:
```css
/* Before */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* After */
@import "tailwindcss";
```

4. **Clear Vite cache**:
```bash
rm -rf node_modules/.vite dist
npm run dev
```

**Files Changed:**
- `frontend/postcss.config.js` - Updated plugin name
- `frontend/src/index.css` - Updated to v4 syntax

---

### Module Export Errors

**Symptoms:**
```
Uncaught SyntaxError: The requested module '/src/api/client.ts' does not provide an export named 'LintResponse'
```

**Root Cause:**
TypeScript's `verbatimModuleSyntax: true` can cause issues with how modules are resolved in Vite.

**Solution:**

Update `frontend/tsconfig.app.json`:

```json
{
  "compilerOptions": {
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,  // Changed from verbatimModuleSyntax
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx"
  }
}
```

Clear cache and restart:
```bash
rm -rf node_modules/.vite dist
npm run dev
```

**Files Changed:**
- `frontend/tsconfig.app.json` - Changed to `isolatedModules`

---

### API Connection Errors

**Symptoms:**
- `Error: API error: Internal Server Error`
- `Failed to load resource: the server responded with a status of 500`

**Solution:**

1. **Verify backend is running**:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

2. **Check backend logs** for detailed error messages

3. **Verify CORS is configured** in `backend/psl/api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

4. **Verify .env is loaded** (see [Environment Variables Not Loading](#environment-variables-not-loading))

---

## Model-Specific Issues

### Claude Model 404 Errors

**Symptoms:**
```
litellm.NotFoundError: AnthropicException - {"type":"error","error":{"type":"not_found_error","message":"model: claude-sonnet-4-5-20250929"}}
```

**Root Cause:**
LiteLLM hasn't been updated to support the newest Anthropic model names yet. While Anthropic's API supports these models directly, litellm may lag behind.

**Solution:**

**Currently Working Models (litellm 1.77.7):**
- `claude-3-5-haiku-20241022` - Claude Haiku 3.5 ✅
- `gpt-4` - OpenAI GPT-4 ✅
- `gpt-3.5-turbo` - OpenAI GPT-3.5 ✅

**Not Yet Supported by litellm:**
- `claude-sonnet-4-5-20250929` - Latest Sonnet (works via direct API)
- `claude-3-7-sonnet-20250219` - Sonnet 3.7 (works via direct API)

**Verify a model works:**
```bash
curl -s -X POST http://localhost:8000/lint \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","model":"claude-3-5-haiku-20241022"}'
```

**Test directly with Anthropic API (bypass litellm):**
```bash
curl https://api.anthropic.com/v1/messages \
  --header "x-api-key: YOUR_KEY" \
  --header "anthropic-version: 2023-06-01" \
  --header "content-type: application/json" \
  --data '{"model":"claude-sonnet-4-5-20250929","max_tokens":1024,"messages":[{"role":"user","content":"test"}]}'
```

**Note:** LiteLLM may take time to add support for new Claude models. Check their repo for updates.

**Files Changed:**
- `frontend/src/App.tsx` - Updated model dropdown
- `backend/psl/api.py` - Updated default model
- `backend/psl/parser.py` - Updated default model

---

### OpenAI Authentication Errors

**Symptoms:**
```
AuthenticationError: OpenAIException - The api_key client option must be set
```

**Solution:**

1. **Verify API key in .env**:
```bash
cat backend/.env | grep OPENAI_API_KEY
```

2. **Verify key is valid**:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

3. **Get a new key** if needed:
- Visit https://platform.openai.com/api-keys
- Create new secret key
- Update `backend/.env`

4. **Restart backend** to load new key:
```bash
# In backend directory
python main.py
```

---

## Testing Checklist

After fixing issues, verify everything works:

### Backend
```bash
cd backend
pyenv local psl-env
make test                    # Should pass with 0 warnings
curl http://localhost:8000/health  # Should return {"status":"ok"}
```

### Frontend
```bash
cd frontend
npm run dev                  # Should start without errors
# Open http://localhost:5173
# Click "Lint Prompt" - Should work with gpt-4
```

### Integration
1. Start backend: `cd backend && python main.py`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser to http://localhost:5173
4. Click "Lint Prompt" button
5. Verify results appear without errors

---

## Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/anthropics/claude-code/issues)
2. Review backend logs for detailed error messages
3. Check browser console for frontend errors
4. Verify all dependencies are installed: `pip list` and `npm list`

## Related Documentation

- [README.md](README.md) - Setup and quick start
- Backend: `backend/psl/` - API and validation code
- Frontend: `frontend/src/` - React application code

# Prompt Semantic Linter (PSL) - Project Specification

## Overview

**Prompt Semantic Linter** is a tool that analyzes system prompts and detects semantic issues that lead to hallucinations, contradictions, and unpredictable LLM behavior. Think ESLint, but for prompts.

Based on A.G.I.L.E. (AI-Guided Language Engineering) principles from IntentHub framework.

## Core Problem

LLMs hallucinate when prompts contain:
- Undefined computed fields ("calculate mesh_coherence_index" without defining what it means)
- Conflicting constraints ("be concise" + "provide detailed explanations")
- Ambiguous requirements ("ALL fields required" without fallback strategy)
- Undefined domain terminology

## Demo Case: Kubernetes Metrics

**Bad Prompt** (causes hallucinations):
```
You are an expert in analyzing Kubernetes manifests.
Extract the following metrics:
- pod_density_ratio
- mesh_coherence_index
- scheduling_entropy

ALL metrics must be calculated from the manifest.
```

**Result**: Model invents numbers like `{"pod_density_ratio": 0.73, "mesh_coherence_index": 0.91}` with no basis.

**After PSL**:
```
❌ ERROR [no-undefined-computed-fields]
   Metric 'pod_density_ratio' has no definition
   → Add formula or mark as optional

❌ ERROR [no-undefined-computed-fields]
   Metric 'mesh_coherence_index' has no definition
   → This term is not standard Kubernetes terminology
```

## Architecture

```
┌──────────────────────────────────────┐
│  Frontend (TypeScript/React)         │
│  - Monaco Editor (VS Code in browser)│
│  - Client-side rules (regex)         │
│  - Results display                   │
└────────────┬─────────────────────────┘
             │ HTTP
             ▼
┌──────────────────────────────────────┐
│  Backend (Python + FastAPI)          │
│  - LiteLLM for LLM abstraction       │
│  - Semantic Parser (LLM-based)       │
│  - Validation rules engine           │
└──────────────────────────────────────┘
```

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - REST API
- **LiteLLM** - unified interface for Claude/GPT-4/Ollama/etc
- **Pydantic** - data validation
- **pytest** - testing

### Frontend
- **TypeScript**
- **React + Vite**
- **Monaco Editor** - code editor component
- **Tailwind CSS** - styling

## Project Structure

```
prompt-semantic-linter/
├── backend/
│   ├── psl/
│   │   ├── __init__.py
│   │   ├── parser.py          # Semantic Parser (LLM-based)
│   │   ├── ir.py               # IR (Intermediate Representation) schema
│   │   ├── rules/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Base Rule class
│   │   │   ├── hallucination.py # no-undefined-computed-fields
│   │   │   ├── contradictions.py # no-conflicting-constraints
│   │   │   └── ambiguity.py    # explicit-fallback-strategy
│   │   ├── validator.py        # Runs rules on IR
│   │   └── api.py              # FastAPI endpoints
│   ├── tests/
│   │   ├── fixtures/
│   │   │   ├── bad_prompts/
│   │   │   │   └── k8s_metrics.txt
│   │   │   └── good_prompts/
│   │   │       └── k8s_metrics_fixed.txt
│   │   └── test_rules.py
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PromptEditor.tsx
│   │   │   ├── ModelSelector.tsx
│   │   │   ├── ResultsPanel.tsx
│   │   │   └── LintError.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── index.html
├── .gitignore
├── README.md
└── LICENSE
```

## Phase 1: MVP (Start Here)

### Goal
Working prototype with ONE rule that catches hallucinations in Kubernetes metrics example.

### Deliverables
1. Backend API with semantic parser and validator
2. Frontend with Monaco Editor
3. One working rule: `no-undefined-computed-fields`
4. Demo with K8s example showing before/after

### Tasks for Claude Code

#### 1. Initialize Git Repository

```bash
# Create project directory
mkdir prompt-semantic-linter
cd prompt-semantic-linter

# Initialize git
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
.pytest_cache/
.coverage
htmlcov/

# Node
node_modules/
dist/
*.log
.DS_Store

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

# Build
build/
*.egg-info/
EOF

# Create README.md (placeholder)
cat > README.md << 'EOF'
# Prompt Semantic Linter

A tool to detect semantic issues in LLM prompts that lead to hallucinations and unpredictable behavior.

## Quick Start

Coming soon...

## Project Status

🚧 Under active development
EOF

# Create LICENSE (MIT)
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Prompt Semantic Linter Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Initial commit
git add .
git commit -m "Initial commit: project structure"
```

#### 2. Backend Setup

```bash
# Create backend structure
mkdir -p backend/psl/rules backend/tests/fixtures/{bad_prompts,good_prompts}

# Create requirements.txt
cat > backend/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
litellm==1.17.0
pydantic==2.5.0
pytest==7.4.3
httpx==0.25.2
python-dotenv==1.0.0
EOF

# Create .env template
cat > backend/.env.example << 'EOF'
# Add your API keys here
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Optional: for Ollama local models
OLLAMA_API_BASE=http://localhost:11434
EOF
```

**File: `backend/psl/ir.py`** - IR Schema
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class ComputedField(BaseModel):
    """Represents a field that requires computation/extraction"""
    name: str
    has_definition: bool
    definition: Optional[str] = None
    source_fields: Optional[List[str]] = None

class Constraint(BaseModel):
    """Represents a constraint on output/behavior"""
    type: Literal["output_length", "style", "format", "priority"]
    value: str
    conflicts_with: Optional[List[str]] = None

class DomainTerm(BaseModel):
    """Represents domain-specific terminology"""
    term: str
    defined: bool
    definition: Optional[str] = None
    is_standard: bool = True

class IR(BaseModel):
    """Intermediate Representation of a prompt"""
    computed_fields: List[ComputedField] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    domain_terms: List[DomainTerm] = Field(default_factory=list)
    fallback_strategy: Literal["null", "error", "default", "unspecified"] = "unspecified"
```

**File: `backend/psl/parser.py`** - Semantic Parser
```python
from litellm import completion
import json
from typing import Dict, Any
from .ir import IR

class SemanticParser:
    """Converts natural language prompts into structured IR using LLM"""
    
    SYSTEM_PROMPT = """You are a semantic analyzer for LLM system prompts.
Extract structured information following this schema:

{
  "computed_fields": [
    {
      "name": "field_name",
      "has_definition": true/false,
      "definition": "formula if exists or null",
      "source_fields": ["field1", "field2"] or null
    }
  ],
  "constraints": [
    {
      "type": "output_length" | "style" | "format" | "priority",
      "value": "...",
      "conflicts_with": ["constraint_value"] or null
    }
  ],
  "domain_terms": [
    {
      "term": "technical term",
      "defined": true/false,
      "definition": "if exists or null",
      "is_standard": true/false
    }
  ],
  "fallback_strategy": "null" | "error" | "default" | "unspecified"
}

Look for:
- Phrases like "calculate", "extract", "compute", "determine" → computed_fields
- Output requirements like "be concise", "detailed" → constraints
- Technical jargon → domain_terms
- Instructions about missing data → fallback_strategy

Return ONLY valid JSON matching the schema."""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        self.model = model
    
    def parse(self, prompt_text: str) -> IR:
        """Parse prompt into IR"""
        try:
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this prompt:\n\n{prompt_text}"}
                ],
                temperature=0.1,
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            return IR(**data)
            
        except Exception as e:
            raise ValueError(f"Failed to parse prompt: {str(e)}")
```

**File: `backend/psl/rules/base.py`** - Base Rule Class
```python
from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel

class LintError(BaseModel):
    """Represents a linting error"""
    rule: str
    severity: str  # "error" | "warning" | "info"
    message: str
    suggestion: str

class Rule(ABC):
    """Base class for linting rules"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Rule identifier"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description"""
        pass
    
    @abstractmethod
    def check(self, ir) -> List[LintError]:
        """Check IR and return errors"""
        pass
```

**File: `backend/psl/rules/hallucination.py`** - First Rule
```python
from typing import List
from .base import Rule, LintError
from ..ir import IR

class NoUndefinedComputedFieldsRule(Rule):
    """Detects computed fields without definitions (hallucination risk)"""
    
    @property
    def name(self) -> str:
        return "no-undefined-computed-fields"
    
    @property
    def description(self) -> str:
        return "Computed fields must have explicit definitions to prevent hallucinations"
    
    def check(self, ir: IR) -> List[LintError]:
        errors = []
        
        for field in ir.computed_fields:
            if not field.has_definition:
                errors.append(LintError(
                    rule=self.name,
                    severity="error",
                    message=f"Field '{field.name}' requires computation but has no definition",
                    suggestion=f"Add formula for '{field.name}' or mark as optional with fallback strategy"
                ))
        
        return errors
```

**File: `backend/psl/validator.py`** - Validator
```python
from typing import List
from .ir import IR
from .rules.base import Rule, LintError
from .rules.hallucination import NoUndefinedComputedFieldsRule

class Validator:
    """Runs linting rules on IR"""
    
    def __init__(self):
        self.rules: List[Rule] = [
            NoUndefinedComputedFieldsRule(),
        ]
    
    def validate(self, ir: IR) -> List[LintError]:
        """Run all rules and collect errors"""
        all_errors = []
        
        for rule in self.rules:
            errors = rule.check(ir)
            all_errors.extend(errors)
        
        return all_errors
```

**File: `backend/psl/api.py`** - FastAPI Endpoints
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from .parser import SemanticParser
from .validator import Validator
from .rules.base import LintError
from .ir import IR

app = FastAPI(title="Prompt Semantic Linter API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LintRequest(BaseModel):
    prompt: str
    model: str = "claude-3-5-sonnet-20241022"

class LintResponse(BaseModel):
    ir: IR
    errors: List[LintError]
    summary: dict

@app.post("/lint", response_model=LintResponse)
async def lint_prompt(req: LintRequest):
    """Lint a system prompt"""
    try:
        # Parse prompt into IR
        parser = SemanticParser(model=req.model)
        ir = parser.parse(req.prompt)
        
        # Validate IR
        validator = Validator()
        errors = validator.validate(ir)
        
        # Summary
        summary = {
            "total_errors": len([e for e in errors if e.severity == "error"]),
            "total_warnings": len([e for e in errors if e.severity == "warning"]),
            "computed_fields": len(ir.computed_fields),
            "undefined_fields": len([f for f in ir.computed_fields if not f.has_definition])
        }
        
        return LintResponse(ir=ir, errors=errors, summary=summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
```

**File: `backend/main.py`** - Entry Point
```python
import uvicorn
from psl.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

#### 3. Test Fixtures

**File: `backend/tests/fixtures/bad_prompts/k8s_metrics.txt`**
```
You are an expert in analyzing Kubernetes manifests.
Extract the following metrics:

{
  "pod_density_ratio": float,
  "mesh_coherence_index": float,
  "resource_affinity_score": float,
  "scheduling_entropy": float,
  "network_policy_coverage": float
}

ALL metrics must be calculated from the manifest.
```

**File: `backend/tests/fixtures/good_prompts/k8s_metrics_fixed.txt`**
```
You are a Kubernetes manifest analyzer.

Extract metrics if sufficient data exists:

{
  "pod_density_ratio": float or null,
  "containers_count": int or null
}

Definitions:
- pod_density_ratio = containers / requests.memory (if both exist)
- containers_count = length of spec.containers array

If required fields are missing, return null with explanation.
Do not invent values.
```

**File: `backend/tests/test_rules.py`**
```python
import pytest
from psl.parser import SemanticParser
from psl.validator import Validator

@pytest.mark.asyncio
async def test_bad_k8s_prompt():
    """Test that bad K8s prompt triggers errors"""
    with open("tests/fixtures/bad_prompts/k8s_metrics.txt") as f:
        prompt = f.read()
    
    parser = SemanticParser()
    ir = parser.parse(prompt)
    
    validator = Validator()
    errors = validator.validate(ir)
    
    # Should have errors about undefined computed fields
    assert len(errors) > 0
    assert any("pod_density_ratio" in e.message for e in errors)

@pytest.mark.asyncio
async def test_good_k8s_prompt():
    """Test that fixed prompt passes validation"""
    with open("tests/fixtures/good_prompts/k8s_metrics_fixed.txt") as f:
        prompt = f.read()
    
    parser = SemanticParser()
    ir = parser.parse(prompt)
    
    validator = Validator()
    errors = validator.validate(ir)
    
    # Should have no errors or only warnings
    critical_errors = [e for e in errors if e.severity == "error"]
    assert len(critical_errors) == 0
```

#### 4. Frontend Setup

```bash
# Create frontend with Vite
cd frontend
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install
npm install @monaco-editor/react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**File: `frontend/src/api/client.ts`**
```typescript
export interface LintRequest {
  prompt: string;
  model?: string;
}

export interface LintError {
  rule: string;
  severity: string;
  message: string;
  suggestion: string;
}

export interface LintResponse {
  ir: any;
  errors: LintError[];
  summary: {
    total_errors: number;
    total_warnings: number;
    computed_fields: number;
    undefined_fields: number;
  };
}

const API_BASE = 'http://localhost:8000';

export async function lintPrompt(req: LintRequest): Promise<LintResponse> {
  const response = await fetch(`${API_BASE}/lint`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  
  return response.json();
}
```

**File: `frontend/src/App.tsx`**
```typescript
import { useState } from 'react';
import Editor from '@monaco-editor/react';
import { lintPrompt, LintResponse } from './api/client';

const EXAMPLE_PROMPT = `You are an expert in analyzing Kubernetes manifests.
Extract the following metrics:
- pod_density_ratio
- mesh_coherence_index
- scheduling_entropy

ALL metrics must be calculated from the manifest.`;

function App() {
  const [prompt, setPrompt] = useState(EXAMPLE_PROMPT);
  const [model, setModel] = useState('claude-3-5-sonnet-20241022');
  const [results, setResults] = useState<LintResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLint = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await lintPrompt({ prompt, model });
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Prompt Semantic Linter</h1>
          <p className="text-gray-400">Detect semantic issues that cause LLM hallucinations</p>
        </header>

        <div className="grid grid-cols-2 gap-8">
          <div>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Model</label>
              <select 
                value={model} 
                onChange={e => setModel(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded px-4 py-2"
              >
                <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                <option value="gpt-4">GPT-4</option>
                <option value="ollama/llama2">Llama 2 (local)</option>
              </select>
            </div>

            <label className="block text-sm font-medium mb-2">System Prompt</label>
            <div className="border border-gray-700 rounded overflow-hidden">
              <Editor
                height="400px"
                defaultLanguage="text"
                theme="vs-dark"
                value={prompt}
                onChange={(value) => setPrompt(value || '')}
              />
            </div>

            <button
              onClick={handleLint}
              disabled={loading}
              className="mt-4 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-6 py-3 rounded font-medium"
            >
              {loading ? 'Analyzing...' : 'Lint Prompt'}
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Results</label>
            <div className="bg-gray-800 border border-gray-700 rounded p-6 h-[500px] overflow-auto">
              {error && (
                <div className="text-red-400 mb-4">
                  Error: {error}
                </div>
              )}

              {results && (
                <>
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2">Summary</h3>
                    <div className="space-y-1 text-sm">
                      <div>❌ Errors: {results.summary.total_errors}</div>
                      <div>⚠️  Warnings: {results.summary.total_warnings}</div>
                      <div>📊 Computed fields: {results.summary.computed_fields}</div>
                      <div>🚨 Undefined: {results.summary.undefined_fields}</div>
                    </div>
                  </div>

                  {results.errors.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-2">Issues</h3>
                      <div className="space-y-4">
                        {results.errors.map((err, i) => (
                          <div key={i} className="border-l-4 border-red-500 pl-4 py-2">
                            <div className="font-medium">
                              {err.severity === 'error' ? '❌' : '⚠️'} [{err.rule}]
                            </div>
                            <div className="text-sm text-gray-300 mt-1">{err.message}</div>
                            <div className="text-sm text-blue-400 mt-2">💡 {err.suggestion}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {results.errors.length === 0 && (
                    <div className="text-green-400">
                      ✅ No issues found! This prompt looks good.
                    </div>
                  )}
                </>
              )}

              {!results && !error && !loading && (
                <div className="text-gray-500 text-center mt-20">
                  Click "Lint Prompt" to analyze
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
```

#### 5. Running the Project

**File: `README.md`** (updated)
```markdown
# Prompt Semantic Linter

A tool to detect semantic issues in LLM prompts that lead to hallucinations and unpredictable behavior.

## Demo

Try the Kubernetes metrics example to see how PSL catches undefined computed fields that cause LLMs to hallucinate numbers.

## Quick Start

### Backend

\`\`\`bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up API keys
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY or OPENAI_API_KEY

# Run server
python main.py
\`\`\`

Server will be running at `http://localhost:8000`

### Frontend

\`\`\`bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
\`\`\`

Frontend will be running at `http://localhost:5173`

## Testing

\`\`\`bash
cd backend
pytest tests/
\`\`\`

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
```

## Next Steps After MVP

1. Add more rules:
   - `no-conflicting-constraints`
   - `explicit-fallback-strategy`
   - `define-domain-terms`

2. Improve UI:
   - Side-by-side diff for fixes
   - Export lint report
   - Save/load prompts

3. Integration:
   - VS Code extension
   - CLI tool
   - GitHub Action

4. Advanced features:
   - Auto-fix mode
   - Custom rules
   - Rule severity configuration

## Success Metrics

- ✅ Can detect hallucinations in K8s example
- ✅ Works with multiple LLM providers
- ✅ Clear, actionable error messages
- ✅ Fast response time (<5s for parsing)

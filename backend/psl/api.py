from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from litellm import completion
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
    model: str = "gpt-4"

class LintResponse(BaseModel):
    ir: IR
    errors: List[LintError]
    summary: dict

class ExecuteRequest(BaseModel):
    prompt: str
    context: str
    model: str = "gpt-4"

class ExecuteResponse(BaseModel):
    output: str
    model: str
    has_errors: bool

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

@app.post("/execute", response_model=ExecuteResponse)
async def execute_prompt(req: ExecuteRequest):
    """Execute a prompt with given context and return the LLM's output"""
    try:
        response = completion(
            model=req.model,
            messages=[
                {"role": "system", "content": req.prompt},
                {"role": "user", "content": req.context}
            ],
            temperature=0.7,
        )

        output = response.choices[0].message.content

        return ExecuteResponse(
            output=output,
            model=req.model,
            has_errors=False
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

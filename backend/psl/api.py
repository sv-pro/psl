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

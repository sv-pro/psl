import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict

from .adapters import get_adapter, LLMMessage, list_available_models
from .parser import SemanticParser
from .validator import Validator
from .rules.base import LintError
from .ir import IR
from .evaluation import DidacticEvaluator

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
        ir = await parser.parse_async(req.prompt)

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

    except ValueError as e:
        # Model not found or configuration errors
        raise HTTPException(status_code=400, detail=f"Invalid model or configuration: {str(e)}")
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f"ERROR in /lint endpoint: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/execute", response_model=ExecuteResponse)
async def execute_prompt(req: ExecuteRequest):
    """Execute a prompt with given context and return the LLM's output"""
    try:
        adapter = get_adapter(req.model)
        messages = [
            LLMMessage(role="system", content=req.prompt),
            LLMMessage(role="user", content=req.context)
        ]

        response = await adapter.complete(
            messages=messages,
            temperature=0.7,
        )

        return ExecuteResponse(
            output=response.content,
            model=req.model,
            has_errors=False
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/models")
async def get_models() -> Dict[str, List[str]]:
    """Get all available models grouped by provider"""
    return list_available_models()

@app.get("/models/healthy")
async def get_healthy_models() -> Dict[str, List[str]]:
    """Get only models that pass health checks grouped by provider"""
    try:
        from .health import HealthChecker
        
        # Get all configured models
        all_models = list_available_models()
        
        # Run health checks
        health_checker = HealthChecker()
        health_results = await health_checker.check_all()
        
        # Filter to only healthy models
        healthy_models = {}
        
        for provider_check in health_results:
            if provider_check.status.value == "healthy":
                provider_name = provider_check.provider.lower()
                healthy_model_names = []
                
                for model_check in provider_check.models_checked:
                    if model_check.status.value == "healthy":
                        # Extract model name (remove provider prefix if present)
                        model_name = model_check.model
                        if model_name.startswith("ollama/"):
                            model_name = model_name  # Keep ollama/ prefix for consistency
                        elif "/" in model_name:
                            model_name = model_name.split("/", 1)[1]
                        healthy_model_names.append(model_name)
                
                if healthy_model_names:
                    healthy_models[provider_name] = healthy_model_names
        
        return healthy_models
    
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f"ERROR in /models/healthy endpoint: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/examples")
async def get_examples():
    """Get all available prompt examples with metadata"""
    try:
        examples_dir = Path(__file__).parent / "examples"
        metadata_file = examples_dir / "metadata.json"

        if not metadata_file.exists():
            return {"examples": []}

        with open(metadata_file) as f:
            metadata = json.load(f)

        # Load actual content for each example
        for example in metadata["examples"]:
            prompt_path = examples_dir / example["prompt_file"]
            context_path = examples_dir / example["context_file"]

            if prompt_path.exists():
                with open(prompt_path) as f:
                    example["prompt"] = f.read()

            if context_path.exists():
                with open(context_path) as f:
                    example["context"] = f.read()

        return metadata

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class EvaluateRequest(BaseModel):
    example_ids: Optional[List[str]] = None
    models: Optional[List[str]] = None

@app.post("/evaluate")
async def evaluate_prompts(req: EvaluateRequest):
    """Run didactic evaluation matrix: test all prompts against all models"""
    try:
        evaluator = DidacticEvaluator()
        matrix = await evaluator.evaluate_matrix(
            example_ids=req.example_ids,
            models=req.models
        )
        return matrix.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

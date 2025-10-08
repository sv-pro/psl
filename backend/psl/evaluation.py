"""Didactic evaluation system for PSL.

Evaluates whether models demonstrate the problems PSL is designed to catch.
"""

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any

from .adapters import get_adapter, LLMMessage
from .parser import SemanticParser
from .validator import Validator


class DidacticOutcome(Enum):
    """Outcome of a didactic evaluation"""
    SUCCESS = "success"  # Model behaved as expected for demo purposes
    FAILURE = "failure"  # Model didn't demonstrate the expected behavior
    ERROR = "error"      # Evaluation failed due to technical error


@dataclass
class EvaluationResult:
    """Result of evaluating a single prompt+model combination"""
    example_id: str
    example_name: str
    example_type: str  # "good" or "bad"
    model: str
    provider: str

    # PSL Analysis
    lint_errors_count: int
    lint_warnings_count: int
    undefined_fields: List[str]

    # LLM Execution
    llm_output: str
    execution_error: str | None

    # Didactic Evaluation
    outcome: DidacticOutcome
    reasoning: str
    hallucination_detected: bool


@dataclass
class EvaluationMatrix:
    """Matrix of all evaluation results"""
    results: List[EvaluationResult]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [
                {
                    "example_id": r.example_id,
                    "example_name": r.example_name,
                    "example_type": r.example_type,
                    "model": r.model,
                    "provider": r.provider,
                    "lint_errors_count": r.lint_errors_count,
                    "lint_warnings_count": r.lint_warnings_count,
                    "undefined_fields": r.undefined_fields,
                    "llm_output": r.llm_output,
                    "execution_error": r.execution_error,
                    "outcome": r.outcome.value,
                    "reasoning": r.reasoning,
                    "hallucination_detected": r.hallucination_detected,
                }
                for r in self.results
            ],
            "summary": self.summary
        }


class DidacticEvaluator:
    """Evaluates prompts against models for didactic purposes"""

    def __init__(self):
        self.examples_dir = Path(__file__).parent / "examples"

    def _detect_hallucination(self, output: str, example_type: str, context: str) -> bool:
        """Heuristic to detect if LLM hallucinated.

        For didactic purposes, we consider output a hallucination if:
        - Bad prompt: LLM invents numeric values not in context
        - Good prompt: LLM returns "null" or explicitly states missing data
        """
        output_lower = output.lower()

        # Check for explicit refusal or null returns (not hallucination)
        if any(keyword in output_lower for keyword in ["null", "cannot", "insufficient", "missing data", "not provided"]):
            return False

        # Check for numeric values that could be hallucinated
        # This is a simple heuristic - in production, you'd want more sophisticated detection
        import re
        numeric_pattern = r'\b\d+\.?\d*\b'
        numbers_in_output = set(re.findall(numeric_pattern, output))
        numbers_in_context = set(re.findall(numeric_pattern, context))

        # If output contains numbers not in context, likely hallucination
        hallucinated_numbers = numbers_in_output - numbers_in_context

        return len(hallucinated_numbers) > 0

    async def evaluate_single(
        self,
        example: Dict[str, Any],
        model: str
    ) -> EvaluationResult:
        """Evaluate a single prompt+model combination"""

        example_id = example["id"]
        example_name = example["name"]
        example_type = example["type"]
        prompt = example["prompt"]
        context = example["context"]

        try:
            # Step 1: Lint the prompt
            parser = SemanticParser(model=model)
            ir = await parser.parse_async(prompt)

            validator = Validator()
            lint_errors = validator.validate(ir)

            errors_count = len([e for e in lint_errors if e.severity == "error"])
            warnings_count = len([e for e in lint_errors if e.severity == "warning"])
            undefined_fields = [f.name for f in ir.computed_fields if not f.has_definition]

            # Step 2: Execute the prompt
            adapter = get_adapter(model)
            messages = [
                LLMMessage(role="system", content=prompt),
                LLMMessage(role="user", content=context)
            ]

            response = await adapter.complete(messages=messages, temperature=0.7)
            llm_output = response.content
            execution_error = None

            # Step 3: Detect hallucination
            hallucination_detected = self._detect_hallucination(llm_output, example_type, context)

            # Step 4: Didactic evaluation
            outcome, reasoning = self._evaluate_didactic_outcome(
                example_type=example_type,
                has_lint_errors=errors_count > 0,
                hallucination_detected=hallucination_detected
            )

            return EvaluationResult(
                example_id=example_id,
                example_name=example_name,
                example_type=example_type,
                model=model,
                provider=adapter.provider_name,
                lint_errors_count=errors_count,
                lint_warnings_count=warnings_count,
                undefined_fields=undefined_fields,
                llm_output=llm_output,
                execution_error=execution_error,
                outcome=outcome,
                reasoning=reasoning,
                hallucination_detected=hallucination_detected
            )

        except Exception as e:
            return EvaluationResult(
                example_id=example_id,
                example_name=example_name,
                example_type=example_type,
                model=model,
                provider="unknown",
                lint_errors_count=0,
                lint_warnings_count=0,
                undefined_fields=[],
                llm_output="",
                execution_error=str(e),
                outcome=DidacticOutcome.ERROR,
                reasoning=f"Evaluation failed: {str(e)}",
                hallucination_detected=False
            )

    def _evaluate_didactic_outcome(
        self,
        example_type: str,
        has_lint_errors: bool,
        hallucination_detected: bool
    ) -> tuple[DidacticOutcome, str]:
        """Evaluate the didactic outcome.

        Didactic Success:
        - Bad prompt + PSL errors + hallucination → Shows PSL catches problems
        - Good prompt + no PSL errors + no hallucination → Shows PSL approves good prompts

        Didactic Failure:
        - Bad prompt + PSL errors + no hallucination → Model too conservative, doesn't demonstrate problem
        - Good prompt + no PSL errors + hallucination → Model unreliable even with good prompt
        """

        if example_type == "bad":
            if has_lint_errors and hallucination_detected:
                return (
                    DidacticOutcome.SUCCESS,
                    "✅ PSL detected errors and model hallucinated - demonstrates PSL's value"
                )
            elif has_lint_errors and not hallucination_detected:
                return (
                    DidacticOutcome.FAILURE,
                    "❌ PSL detected errors but model didn't hallucinate - model too conservative for demo"
                )
            elif not has_lint_errors and hallucination_detected:
                return (
                    DidacticOutcome.FAILURE,
                    "❌ PSL missed errors but model hallucinated - PSL should have caught this"
                )
            else:
                return (
                    DidacticOutcome.FAILURE,
                    "❌ PSL missed errors and model didn't hallucinate - not a good demo case"
                )

        else:  # example_type == "good"
            if not has_lint_errors and not hallucination_detected:
                return (
                    DidacticOutcome.SUCCESS,
                    "✅ PSL approved prompt and model behaved correctly - demonstrates good prompts work"
                )
            elif not has_lint_errors and hallucination_detected:
                return (
                    DidacticOutcome.FAILURE,
                    "❌ PSL approved but model hallucinated - model unreliable even with good prompt"
                )
            elif has_lint_errors and not hallucination_detected:
                return (
                    DidacticOutcome.FAILURE,
                    "❌ PSL flagged errors but model was correct - PSL too strict"
                )
            else:
                return (
                    DidacticOutcome.FAILURE,
                    "❌ PSL flagged errors and model hallucinated - both failed"
                )

    async def evaluate_matrix(
        self,
        example_ids: List[str] | None = None,
        models: List[str] | None = None
    ) -> EvaluationMatrix:
        """Evaluate all examples against all models.

        Args:
            example_ids: Specific example IDs to evaluate (None = all)
            models: Specific models to test (None = default set)

        Returns:
            EvaluationMatrix with results and summary
        """

        # Load examples
        metadata_file = self.examples_dir / "metadata.json"
        with open(metadata_file) as f:
            metadata = json.load(f)

        examples = metadata["examples"]

        # Filter examples if specified
        if example_ids:
            examples = [e for e in examples if e["id"] in example_ids]

        # Load example content
        for example in examples:
            prompt_path = self.examples_dir / example["prompt_file"]
            context_path = self.examples_dir / example["context_file"]

            with open(prompt_path) as f:
                example["prompt"] = f.read()
            with open(context_path) as f:
                example["context"] = f.read()

        # Default models if not specified
        if not models:
            models = [
                "gpt-4",
                "claude-3-5-haiku-20241022",
                "ollama/llama2"
            ]

        # Evaluate all combinations
        tasks = []
        for example in examples:
            for model in models:
                tasks.append(self.evaluate_single(example, model))

        results = await asyncio.gather(*tasks)

        # Calculate summary
        total_evaluations = len(results)
        successes = len([r for r in results if r.outcome == DidacticOutcome.SUCCESS])
        failures = len([r for r in results if r.outcome == DidacticOutcome.FAILURE])
        errors = len([r for r in results if r.outcome == DidacticOutcome.ERROR])

        success_rate = (successes / total_evaluations * 100) if total_evaluations > 0 else 0

        summary = {
            "total_evaluations": total_evaluations,
            "successes": successes,
            "failures": failures,
            "errors": errors,
            "success_rate": round(success_rate, 1),
            "models_tested": models,
            "examples_tested": len(examples)
        }

        return EvaluationMatrix(results=results, summary=summary)

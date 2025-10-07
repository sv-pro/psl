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

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

"""
Constraint validation rules for detecting conflicting requirements
"""

from typing import List, Dict, Set
import re
from .base import Rule, LintError
from ..ir import IR


class ConflictingConstraintsRule(Rule):
    """Detects constraints that contradict each other and cause LLM confusion"""

    @property
    def name(self) -> str:
        return "no-conflicting-constraints"

    @property
    def description(self) -> str:
        return "Constraints should not contradict each other to prevent LLM confusion"

    def __init__(self):
        # Define conflict patterns: each tuple contains (pattern1, pattern2, explanation)
        self.conflict_patterns = [
            # Length vs Detail conflicts
            (
                ["concise", "brief", "short", "summary"],
                ["detailed", "comprehensive", "in-depth", "thorough", "extensive"],
                "Requesting both concise and detailed output creates ambiguity"
            ),
            
            # Format conflicts
            (
                ["json", "structured", "yaml", "xml"],
                ["natural language", "prose", "narrative", "conversational"],
                "Structured format conflicts with natural language format"
            ),
            
            # Style conflicts
            (
                ["formal", "professional", "academic", "technical"],
                ["casual", "informal", "friendly", "conversational", "relaxed"],
                "Formal style conflicts with casual/informal style"
            ),
            
            # Specificity conflicts
            (
                ["focus on", "only include", "specifically", "just"],
                ["comprehensive", "complete overview", "all aspects", "everything"],
                "Narrow focus conflicts with comprehensive coverage"
            ),
            
            # Tone conflicts
            (
                ["objective", "neutral", "unbiased", "factual"],
                ["persuasive", "opinionated", "subjective", "advocate"],
                "Objective tone conflicts with persuasive/subjective approach"
            )
        ]

    def check(self, ir: IR) -> List[LintError]:
        errors = []
        
        # Extract all constraint values for analysis
        constraint_values = [constraint.value.lower() for constraint in ir.constraints]
        
        # Check for direct conflicts
        conflicts = self._find_constraint_conflicts(constraint_values)
        
        for conflict in conflicts:
            errors.append(LintError(
                rule=self.name,
                severity="error",
                message=f"Conflicting constraints detected: {conflict['explanation']}",
                suggestion=f"Choose either '{conflict['pattern1_match']}' OR '{conflict['pattern2_match']}', not both. Consider clarifying the priority or splitting into separate requests."
            ))
        
        # Check for impossible combinations
        impossible_errors = self._check_impossible_combinations(ir.constraints)
        errors.extend(impossible_errors)
        
        return errors

    def _find_constraint_conflicts(self, constraint_values: List[str]) -> List[Dict]:
        """Find conflicts between constraint patterns"""
        conflicts = []
        
        for pattern1, pattern2, explanation in self.conflict_patterns:
            # Find matches for each pattern
            pattern1_matches = []
            pattern2_matches = []
            
            for value in constraint_values:
                for keyword in pattern1:
                    if keyword in value:
                        pattern1_matches.append(value)
                        break
                        
                for keyword in pattern2:
                    if keyword in value:
                        pattern2_matches.append(value)
                        break
            
            # If both patterns have matches, it's a conflict
            if pattern1_matches and pattern2_matches:
                conflicts.append({
                    'pattern1_match': '; '.join(set(pattern1_matches)),
                    'pattern2_match': '; '.join(set(pattern2_matches)),
                    'explanation': explanation
                })
        
        return conflicts

    def _check_impossible_combinations(self, constraints) -> List[LintError]:
        """Check for logically impossible constraint combinations"""
        errors = []
        
        # Check for multiple conflicting output lengths
        length_constraints = []
        for constraint in constraints:
            if constraint.type == "output_length":
                length_constraints.append(constraint.value)
        
        if len(length_constraints) > 1:
            # Check if they specify different lengths
            word_counts = []
            char_counts = []
            
            for length in length_constraints:
                # Extract numbers from length specifications
                numbers = re.findall(r'\d+', length)
                if 'word' in length.lower() and numbers:
                    word_counts.append(int(numbers[0]))
                elif 'char' in length.lower() and numbers:
                    char_counts.append(int(numbers[0]))
            
            # Check for conflicting word counts
            if len(set(word_counts)) > 1:
                errors.append(LintError(
                    rule=self.name,
                    severity="error",
                    message=f"Multiple conflicting word count requirements: {word_counts}",
                    suggestion="Specify a single word count or acceptable range"
                ))
            
            # Check for conflicting character counts
            if len(set(char_counts)) > 1:
                errors.append(LintError(
                    rule=self.name,
                    severity="error", 
                    message=f"Multiple conflicting character count requirements: {char_counts}",
                    suggestion="Specify a single character count or acceptable range"
                ))
        
        return errors
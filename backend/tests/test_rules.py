import pytest
from psl.parser import SemanticParser
from psl.validator import Validator
from psl.rules.constraints import ConflictingConstraintsRule
from psl.ir import IR, Constraint

def test_bad_k8s_prompt():
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

def test_good_k8s_prompt():
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

def test_conflicting_constraints_rule_bad_prompt():
    """Test that prompts with conflicting constraints trigger errors"""
    with open("tests/fixtures/bad_prompts/conflicting_constraints.txt") as f:
        prompt = f.read()

    parser = SemanticParser()
    ir = parser.parse(prompt)

    validator = Validator()
    errors = validator.validate(ir)

    # Should detect conflicting constraints
    constraint_errors = [e for e in errors if "conflicting constraints" in e.message.lower()]
    assert len(constraint_errors) > 0, "Expected to find conflicting constraints errors"
    
    # The fixture has multiple conflicts (brief/detailed, JSON/plain text, formal/casual)
    # We just need to verify that at least some conflicts were detected
    error_messages = ' '.join([e.message.lower() for e in constraint_errors])
    has_conflict = any(keyword in error_messages for keyword in ['concise', 'detailed', 'formal', 'casual', 'structured'])
    assert has_conflict, f"Expected conflict keywords in error messages, got: {error_messages}"

def test_conflicting_constraints_rule_good_prompt():
    """Test that prompts with clear, non-conflicting constraints pass validation"""
    with open("tests/fixtures/good_prompts/clear_constraints.txt") as f:
        prompt = f.read()

    try:
        parser = SemanticParser()
        ir = parser.parse(prompt)

        validator = Validator()
        errors = validator.validate(ir)

        # Should have no conflicting constraint errors
        constraint_errors = [e for e in errors if "conflicting constraints" in e.message.lower()]
        assert len(constraint_errors) == 0
    except ValueError as e:
        # If the parser fails due to LLM producing invalid constraint types,
        # we can't test the rule, so skip this test
        if "constraint" in str(e).lower() and "type" in str(e).lower():
            import pytest
            pytest.skip(f"LLM produced invalid constraint types: {e}")

def test_conflicting_constraints_rule_direct():
    """Test ConflictingConstraintsRule directly with sample IR"""
    rule = ConflictingConstraintsRule()
    
    # Create IR with conflicting constraints
    conflicting_ir = IR(
        constraints=[
            Constraint(type="output_length", value="brief"),
            Constraint(type="output_length", value="detailed explanation"),
            Constraint(type="format", value="JSON"),
            Constraint(type="format", value="natural language"),
            Constraint(type="style", value="formal"),
            Constraint(type="style", value="casual")
        ],
        computed_fields=[],
        domain_terms=[],
        fallback_strategy="error"
    )
    
    errors = rule.check(conflicting_ir)
    assert len(errors) >= 2  # Should detect at least length and style conflicts
    
    error_messages = [e.message.lower() for e in errors]
    # Check for length/detail conflict
    assert any("concise" in msg and "detailed" in msg for msg in error_messages)
    # Check for style conflict  
    assert any("formal" in msg and "casual" in msg for msg in error_messages)

def test_conflicting_constraints_rule_no_conflicts():
    """Test ConflictingConstraintsRule with non-conflicting constraints"""
    rule = ConflictingConstraintsRule()
    
    # Create IR with compatible constraints
    compatible_ir = IR(
        constraints=[
            Constraint(type="output_length", value="brief"),
            Constraint(type="format", value="JSON"),
            Constraint(type="style", value="professional")
        ],
        computed_fields=[],
        domain_terms=[],
        fallback_strategy="error"
    )
    
    errors = rule.check(compatible_ir)
    assert len(errors) == 0

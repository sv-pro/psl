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

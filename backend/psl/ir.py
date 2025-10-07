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

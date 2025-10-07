from litellm import completion
import json
from typing import Dict, Any
from .ir import IR

class SemanticParser:
    """Converts natural language prompts into structured IR using LLM"""

    SYSTEM_PROMPT = """You are a semantic analyzer for LLM system prompts.
Extract structured information following this schema:

{
  "computed_fields": [
    {
      "name": "field_name",
      "has_definition": true/false,
      "definition": "formula if exists or null",
      "source_fields": ["field1", "field2"] or null
    }
  ],
  "constraints": [
    {
      "type": "output_length" | "style" | "format" | "priority",
      "value": "...",
      "conflicts_with": ["constraint_value"] or null
    }
  ],
  "domain_terms": [
    {
      "term": "technical term",
      "defined": true/false,
      "definition": "if exists or null",
      "is_standard": true/false
    }
  ],
  "fallback_strategy": "null" | "error" | "default" | "unspecified"
}

Look for:
- Phrases like "calculate", "extract", "compute", "determine" → computed_fields
- Output requirements like "be concise", "detailed" → constraints
- Technical jargon → domain_terms
- Instructions about missing data → fallback_strategy

Return ONLY valid JSON matching the schema."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        self.model = model

    def parse(self, prompt_text: str) -> IR:
        """Parse prompt into IR"""
        try:
            response = completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this prompt:\n\n{prompt_text}"}
                ],
                temperature=0.1,
            )

            content = response.choices[0].message.content
            data = json.loads(content)
            return IR(**data)

        except Exception as e:
            raise ValueError(f"Failed to parse prompt: {str(e)}")

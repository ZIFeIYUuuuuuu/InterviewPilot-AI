"""Shared prompt contract snippets for stable structured agent outputs."""

PROMPT_VERSION = "v0.2"

JSON_OUTPUT_CONTRACT = """Prompt version: v0.2

Response contract:
- Return exactly one valid JSON object matching the Output schema.
- Do not wrap the JSON in markdown fences.
- Do not include prose before or after the JSON.
- Use exactly the keys shown in the output schema; do not add extra keys.
- Use empty arrays [] instead of null for list fields.
- Use null only for optional nullable fields.
- Preserve uncertainty explicitly instead of guessing.
- Prefer conservative, evidence-grounded output over fluent but unsupported detail.
- Write user-facing strings in Simplified Chinese while preserving technical terms when clearer."""

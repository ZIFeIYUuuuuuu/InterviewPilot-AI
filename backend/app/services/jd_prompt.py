"""Prompt builder for JD Analyzer."""

from __future__ import annotations

from backend.app.services.prompt_contract import JSON_OUTPUT_CONTRACT


JD_ANALYZER_TASK = "Analyze the provided job description and extract structured JD analysis."


def build_jd_analyzer_prompt(jd_text: str) -> str:
    """Return the JD Analyzer prompt aligned with docs/AGENT_PROMPTS.md."""

    return f'''{JSON_OUTPUT_CONTRACT}

Task:
Analyze the provided job description and extract the role title, required skills, preferred skills, responsibilities, and interview focus.

Success criteria:
- The output accurately reflects the JD.
- Required skills and preferred skills are separated when possible.
- Interview focus reflects what a real interview is likely to test.

Boundaries:
- Use only information supported by the JD text.
- Do not invent skills or responsibilities.
- If the JD is ambiguous, preserve uncertainty rather than guessing.
- Required means explicitly required by the JD; preferred means explicitly optional, nice-to-have, or bonus.
- If the JD is sparse, use conservative defaults and explain uncertainty in uncertainty_notes.

Required steps:
1. Identify the role title.
2. Extract explicit technical and non-technical requirements.
3. Separate required skills from preferred or optional skills when the text supports that distinction.
4. Extract core responsibilities.
5. Infer likely interview focus areas from the responsibilities and requirements.
6. Mark uncertainty if the JD is incomplete or low quality.

Output schema:
{{
  "role_title": "string",
  "required_skills": ["string"],
  "preferred_skills": ["string"],
  "responsibilities": ["string"],
  "interview_focus": ["string"],
  "uncertainty_notes": ["string"],
  "raw_jd_text": "string | null"
}}

Context:
JD text:
"""
{jd_text}
"""
'''

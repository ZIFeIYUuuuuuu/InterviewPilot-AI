"""Prompt builder for Resume Analyzer."""

from __future__ import annotations

from backend.app.services.prompt_contract import JSON_OUTPUT_CONTRACT


RESUME_ANALYZER_TASK = "Analyze the candidate resume and extract structured resume evidence."


def build_resume_analyzer_prompt(resume_text: str) -> str:
    """Return the Resume Analyzer prompt aligned with docs/AGENT_PROMPTS.md."""

    return f'''{JSON_OUTPUT_CONTRACT}

Task:
Analyze the candidate resume and extract core skills, projects, strengths, weaknesses, and weak-evidence skill areas relevant to interview preparation.

Success criteria:
- The output reflects the actual resume rather than generic assumptions.
- Projects include concrete evidence when available.
- Weaknesses distinguish "missing" from "unclear" or "weakly evidenced."

Boundaries:
- Use only information present in the resume.
- Do not infer production experience, ownership, or impact that is not clearly supported.
- If resume evidence is thin, say so explicitly.
- A skill listed only in a skills section is weak evidence unless tied to project, work, or coursework evidence.
- Do not mark JD-specific missing skills here; missing-vs-matched belongs to Gap Analysis.
- For project evidence_quality, use only "high", "medium", or "low".

Required steps:
1. Extract stated technical skills.
2. Identify projects and summarize each project's stack and highlights.
3. Infer candidate strengths only when supported by evidence.
4. Identify weak-evidence areas where the resume mentions a skill but lacks proof.
5. Identify likely interview vulnerability areas caused by sparse, vague, or generic wording.

Output schema:
{{
  "candidate_skills": ["string"],
  "projects": [
    {{
      "name": "string",
      "tech_stack": ["string"],
      "highlights": ["string"],
      "evidence_quality": "high | medium | low"
    }}
  ],
  "strengths": ["string"],
  "weaknesses": ["string"],
  "weak_evidence_skills": ["string"],
  "resume_summary": "string",
  "uncertainty_notes": ["string"],
  "raw_resume_text": "string | null"
}}

Context:
Resume text:
"""
{resume_text}
"""
'''

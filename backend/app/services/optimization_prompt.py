"""Prompt builder for Resume Optimization Suggestions."""

from __future__ import annotations

import json

from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.jd import JDAnalysis
from backend.app.schemas.resume import ResumeAnalysis
from backend.app.services.prompt_contract import JSON_OUTPUT_CONTRACT


RESUME_OPTIMIZATION_TASK = "Generate truthful JD-specific resume optimization suggestions."


def build_resume_optimization_prompt(
    jd_analysis: JDAnalysis, resume_analysis: ResumeAnalysis, gap_analysis: GapAnalysis
) -> str:
    return f'''{JSON_OUTPUT_CONTRACT}

Task:
Generate role-specific resume optimization suggestions based on the JD analysis, resume analysis, and gap analysis.

Success criteria:
- Suggestions improve clarity, specificity, and role relevance.
- Suggestions remain truthful to the candidate's existing evidence.
- The output helps the user improve both resume quality and interview readiness.

Boundaries:
- Do not fabricate experience, metrics, systems, impact, or tools.
- Do not rewrite the entire resume if evidence is weak.
- Prefer targeted suggestions over broad generic advice.
- Example rewrites must preserve the candidate's actual evidence; use conditional wording such as "If true" when suggesting stronger phrasing that requires verification.
- Risk warnings must identify resume claims likely to trigger follow-up questions.

Required steps:
1. Identify the highest-value resume areas to strengthen for this role.
2. Find vague or under-evidenced bullets or project descriptions.
3. Suggest improvements in phrasing, ordering, and emphasis.
4. Provide limited rewrite examples that preserve truthfulness.
5. Identify resume phrasing likely to trigger difficult interview follow-up questions.
6. Keep every suggestion explainable from JD, resume, or gap inputs.

Output schema:
{{
  "optimization_summary": "string",
  "rewrite_targets": ["string"],
  "bullet_improvement_suggestions": [
    {{
      "original_issue": "string",
      "why_it_is_weak": "string",
      "suggested_direction": "string",
      "example_rewrite": "string"
    }}
  ],
  "skill_positioning_suggestions": ["string"],
  "risk_warnings": ["string"]
}}

Context:
JD analysis:
```json
{json.dumps(jd_analysis.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```

Resume analysis:
```json
{json.dumps(resume_analysis.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```

Gap analysis:
```json
{json.dumps(gap_analysis.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```
'''

"""Prompt builder for Gap Analysis."""

from __future__ import annotations

import json

from backend.app.schemas.jd import JDAnalysis
from backend.app.schemas.resume import ResumeAnalysis
from backend.app.services.prompt_contract import JSON_OUTPUT_CONTRACT


GAP_ANALYSIS_TASK = "Compare JD analysis and resume analysis into structured gap analysis."


def build_gap_analysis_prompt(jd_analysis: JDAnalysis, resume_analysis: ResumeAnalysis) -> str:
    return f'''{JSON_OUTPUT_CONTRACT}

Task:
Compare the JD analysis and resume analysis to identify matched skills, missing skills, weak-evidence skills, high-risk interview topics, and recommended interview focus areas.

Success criteria:
- The comparison goes beyond keyword overlap.
- High-risk topics reflect likely interview pressure points.
- Recommended focus areas help drive later interview planning and coaching.

Boundaries:
- Use only the structured JD and resume evidence provided.
- Do not classify a skill as missing if the evidence is merely weak or ambiguous; distinguish those cases clearly.
- Matched requires resume evidence, not just semantic similarity.
- Missing means required by the JD and absent from the resume analysis.
- Weak evidence means present in resume skills or projects but lacking proof, ownership, depth, or outcomes.
- Recommended focus should be usable by Interview Planner and Interviewer.

Required steps:
1. Compare required JD skills against candidate evidence.
2. Identify clearly matched skills.
3. Identify missing skills.
4. Identify weak-evidence skills.
5. Infer high-risk topics for the mock interview.
6. Recommend focus areas for planning and questioning.

Output schema:
{{
  "matched_skills": ["string"],
  "missing_skills": ["string"],
  "weak_evidence_skills": ["string"],
  "high_risk_topics": ["string"],
  "recommended_focus": ["string"],
  "summary": "string"
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
'''

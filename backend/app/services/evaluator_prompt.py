"""Evaluator prompt builder aligned to docs/AGENT_PROMPTS.md."""

from __future__ import annotations

import json

from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.interview import InterviewMessage, InterviewPlan
from backend.app.schemas.jd import JDAnalysis
from backend.app.schemas.resume import ResumeAnalysis
from backend.app.services.prompt_contract import JSON_OUTPUT_CONTRACT

EVALUATOR_TASK = "Evaluate the completed mock interview using a structured rubric."


def build_evaluator_prompt(
    jd_analysis: JDAnalysis,
    resume_analysis: ResumeAnalysis,
    gap_analysis: GapAnalysis,
    interview_plan: InterviewPlan,
    messages: list[InterviewMessage],
) -> str:
    """Build the prompt template used by the post-interview Evaluator."""

    return f"""{JSON_OUTPUT_CONTRACT}

Task:
Evaluate the completed mock interview using a structured rubric and provide evidence-based scoring with reasons.

Success criteria:
- Scores reflect the actual conversation.
- Each score includes a clear explanation.
- Strengths and weaknesses are concrete and useful for practice.

Boundaries:
- This is training feedback, not a hiring verdict.
- Do not use unsupported claims.
- Do not inflate or soften scores without evidence.
- Scores must be integers from 0 to 100.
- Do not use pass/fail, hire/no-hire, offer, rejection, or recruiter-screening language.
- Every dimension reason must cite observed answer quality, transcript evidence, or explicit missing evidence.

Required steps:
1. Review the interview transcript in the context of the role and plan.
2. Evaluate the candidate across each rubric dimension.
3. Provide a score and reason for each dimension.
4. Identify strengths and weaknesses.
5. Identify high-risk topics or evidence gaps.
6. Keep the summary framed as interview-practice feedback for the candidate.

Output schema:
{{
  "overall_score": 0,
  "dimension_scores": {{
    "technical_accuracy": {{"score": 0, "reason": "string"}},
    "depth": {{"score": 0, "reason": "string"}},
    "structure": {{"score": 0, "reason": "string"}},
    "communication": {{"score": 0, "reason": "string"}},
    "role_fit": {{"score": 0, "reason": "string"}},
    "evidence_quality": {{"score": 0, "reason": "string"}}
  }},
  "strengths": ["string"],
  "weaknesses": ["string"],
  "risk_flags": ["string"],
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

Gap analysis:
```json
{json.dumps(gap_analysis.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```

Interview plan:
```json
{json.dumps(interview_plan.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```

Interview transcript:
```json
{json.dumps([message.model_dump(mode="json") for message in messages], ensure_ascii=False, indent=2)}
```
"""

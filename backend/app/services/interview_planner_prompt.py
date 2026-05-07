"""Prompt builder for Interview Planner."""

from __future__ import annotations

import json

from backend.app.schemas.common import Difficulty
from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.jd import JDAnalysis
from backend.app.schemas.resume import ResumeAnalysis
from backend.app.services.prompt_contract import JSON_OUTPUT_CONTRACT


INTERVIEW_PLANNER_TASK = "Create a structured mock interview plan for candidate practice."


def build_interview_planner_prompt(
    jd_analysis: JDAnalysis,
    resume_analysis: ResumeAnalysis,
    gap_analysis: GapAnalysis,
    interview_type: str,
    difficulty: Difficulty,
    duration_minutes: int,
) -> str:
    return f'''{JSON_OUTPUT_CONTRACT}

Task:
Create a structured mock interview plan based on the target role, the candidate resume, identified gaps, requested interview type, difficulty, and duration.

Success criteria:
- The interview plan feels realistic and purposeful.
- Sections reflect the role and the candidate's likely weak points.
- Question flow supports dynamic follow-up later.

Boundaries:
- Do not output a random question list without structure.
- Keep the section count and question count appropriate for the duration.
- Each section must have a clear causal link to JD requirements, resume evidence, or gap analysis.
- Do not exceed the requested duration.

Required steps:
1. Determine the most important interview themes.
2. Allocate interview time by section.
3. Define a goal for each section.
4. Set focus topics for each section.
5. Estimate a practical maximum question count.
6. Prioritize weak-evidence and high-risk topics when assigning section focus.

Output schema:
{{
  "interview_type": "string",
  "duration_minutes": 0,
  "difficulty": "easy | medium | hard",
  "sections": [
    {{
      "name": "string",
      "duration_minutes": 0,
      "goal": "string",
      "focus_topics": ["string"]
    }}
  ],
  "max_questions": 0,
  "plan_summary": "string"
}}

Context:
Interview type: {interview_type}
Difficulty: {difficulty.value}
Duration minutes: {duration_minutes}

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

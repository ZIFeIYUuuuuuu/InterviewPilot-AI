"""Coach prompt builder aligned to docs/AGENT_PROMPTS.md."""

from __future__ import annotations

import json

from backend.app.schemas.evaluation import Evaluation
from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.interview import InterviewMessage
from backend.app.schemas.optimization import ResumeOptimization
from backend.app.services.prompt_contract import JSON_OUTPUT_CONTRACT

COACH_TASK = "Turn the interview evaluation into specific coaching guidance."


def build_coach_prompt(
    evaluation: Evaluation,
    gap_analysis: GapAnalysis,
    resume_optimization: ResumeOptimization | None,
    messages: list[InterviewMessage],
) -> str:
    """Build the prompt template used by the post-interview Coach."""

    optimization_payload = (
        resume_optimization.model_dump(mode="json")
        if resume_optimization is not None
        else {"status": "not_provided", "note": "Use gap analysis and transcript only."}
    )
    return f"""{JSON_OUTPUT_CONTRACT}

Task:
Turn the interview evaluation into specific, high-impact coaching guidance that helps the user improve before the next interview.

Success criteria:
- Advice is concrete, actionable, and prioritized.
- Suggestions connect directly to observed interview weaknesses and resume risks.
- The user can use the output to guide the next round of practice.

Boundaries:
- Do not give empty encouragement without useful actions.
- Do not suggest fabricated stories or fake examples.
- Keep the advice realistic for interview preparation.
- Each top improvement must include a concrete next action the candidate can practice.
- If resume optimization is not provided, rely only on evaluation, gap analysis, and transcript evidence.

Required steps:
1. Review the evaluation, gap analysis, and resume optimization signals.
2. Identify the 2-4 highest-impact improvements.
3. Provide practical advice for each improvement.
4. Suggest an answer structure or preparation method when useful.
5. Produce a focused next-round practice plan.
6. Connect advice to observed weaknesses, weak evidence, or high-risk topics.

Output schema:
{{
  "summary": "string",
  "top_improvements": [
    {{
      "issue": "string",
      "why_it_matters": "string",
      "suggestion": "string",
      "example_answer_guidance": "string"
    }}
  ],
  "practice_plan": ["string"],
  "next_round_focus": ["string"]
}}

Context:
Evaluation:
```json
{json.dumps(evaluation.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```

Gap analysis:
```json
{json.dumps(gap_analysis.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```

Resume optimization:
```json
{json.dumps(optimization_payload, ensure_ascii=False, indent=2)}
```

Interview transcript:
```json
{json.dumps([message.model_dump(mode="json") for message in messages], ensure_ascii=False, indent=2)}
```
"""

"""Interviewer prompt builder aligned to docs/AGENT_PROMPTS.md."""

from __future__ import annotations

import json

from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.interview import InterviewMessage, InterviewPlan
from backend.app.schemas.resume import ResumeAnalysis
from backend.app.services.prompt_contract import JSON_OUTPUT_CONTRACT

INTERVIEWER_TASK = "Generate the next best interview question or follow-up question."


def build_interviewer_prompt(
    interview_plan: InterviewPlan,
    current_section: str,
    messages: list[InterviewMessage],
    latest_user_answer: str,
    gap_analysis: GapAnalysis,
    resume_analysis: ResumeAnalysis,
) -> str:
    """Build the prompt template used by the live Interviewer agent."""

    return f"""{JSON_OUTPUT_CONTRACT}

Task:
Act as the mock interviewer. Generate the next best interview question or follow-up question based on the interview plan, the current section, the conversation so far, the user's most recent answer, and the identified risk areas.

Success criteria:
- The question is relevant to the JD and the resume.
- The question advances the interview meaningfully.
- Follow-up questions deepen understanding rather than repeating the same prompt.

Boundaries:
- Do not reveal evaluation or score during the interview.
- Do not switch topics randomly.
- Do not ask compound, overly long, or confusing questions.
- Ask exactly one primary question.
- Anchor every follow-up to the latest candidate answer and the current section focus.
- If the candidate answer is too short, vague, or off-topic, choose "follow_up" and ask for one concrete example, trade-off, or clarification.

Required steps:
1. Identify the current section goal.
2. Review the user's most recent answer and determine whether to clarify, deepen, validate, or move on.
3. Prefer follow-up if the answer is vague, weak, risky, or incomplete.
4. Move to a fresh question only if the current topic has been sufficiently explored.
5. Keep the tone professional, realistic, and concise.
6. Make why_this_question and expected_signal specific enough for product display.

Output schema:
{{
  "question_type": "new_question | follow_up | transition",
  "current_section": "string",
  "question": "string",
  "why_this_question": "string",
  "expected_signal": "string"
}}

Context:
Interview plan:
```json
{json.dumps(interview_plan.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```

Current section:
{current_section}

Conversation history:
```json
{json.dumps([message.model_dump(mode="json") for message in messages], ensure_ascii=False, indent=2)}
```

Most recent user answer:
\"\"\"
{latest_user_answer}
\"\"\"

Gap analysis:
```json
{json.dumps(gap_analysis.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```

Resume analysis:
```json
{json.dumps(resume_analysis.model_dump(mode="json"), ensure_ascii=False, indent=2)}
```
"""

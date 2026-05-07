"""Interview setup, plan, message, and interviewer-output schemas."""

from datetime import datetime
from enum import Enum

from pydantic import Field

from backend.app.schemas.common import (
    Difficulty,
    InterviewMessageRole,
    InterviewQuestionType,
    SchemaModel,
    new_id,
    utc_now,
)
from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.jd import JDAnalysis
from backend.app.schemas.resume import ResumeAnalysis


class InterviewSection(SchemaModel):
    name: str = Field(..., min_length=1)
    duration_minutes: int = Field(..., ge=1, le=45)
    goal: str = Field(..., min_length=1)
    focus_topics: list[str] = Field(default_factory=list)


class InterviewPlan(SchemaModel):
    interview_type: str = Field(default="targeted_mock")
    duration_minutes: int = Field(..., ge=10, le=45)
    difficulty: Difficulty = Difficulty.medium
    sections: list[InterviewSection] = Field(default_factory=list)
    max_questions: int = Field(..., ge=1, le=30)
    plan_summary: str = Field(..., min_length=1)


class InterviewPlanRequest(SchemaModel):
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    gap_analysis: GapAnalysis
    interview_type: str = "targeted_mock"
    difficulty: Difficulty = Difficulty.medium
    duration_minutes: int = Field(default=20, ge=10, le=45)


class InterviewPlannerPrompt(SchemaModel):
    task: str
    prompt: str


class InterviewPlanResponse(SchemaModel):
    interview_plan: InterviewPlan
    planner_prompt: InterviewPlannerPrompt


class InterviewControlAction(str, Enum):
    answer = "answer"
    skip = "skip"
    next = "next"
    end = "end"
    regenerate = "regenerate"


class LiveInterviewStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"


class InterviewMessage(SchemaModel):
    role: InterviewMessageRole
    content: str = Field(..., min_length=1)
    section: str | None = None
    message_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class InterviewerOutput(SchemaModel):
    question_type: InterviewQuestionType
    current_section: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    why_this_question: str = Field(..., min_length=1)
    expected_signal: str = Field(..., min_length=1)


class InterviewerPrompt(SchemaModel):
    task: str
    prompt: str


class InterviewSessionStartRequest(SchemaModel):
    interview_plan: InterviewPlan
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    gap_analysis: GapAnalysis


class InterviewSessionState(SchemaModel):
    session_id: str = Field(default_factory=lambda: new_id("live_session"))
    status: LiveInterviewStatus = LiveInterviewStatus.in_progress
    interview_plan: InterviewPlan
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    gap_analysis: GapAnalysis
    messages: list[InterviewMessage] = Field(default_factory=list)
    current_section_index: int = Field(default=0, ge=0)
    current_question_count: int = Field(default=0, ge=0)
    latest_question: InterviewerOutput | None = None
    last_action: InterviewControlAction | None = None
    started_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class InterviewTurnRequest(SchemaModel):
    action: InterviewControlAction = InterviewControlAction.answer
    answer: str | None = Field(default=None, description="Candidate answer for the current question.")


class InterviewSessionResponse(SchemaModel):
    session: InterviewSessionState
    interviewer_output: InterviewerOutput | None = None
    interviewer_prompt: InterviewerPrompt | None = None


class InterviewSessionCreate(SchemaModel):
    target_role: str = Field(..., min_length=1)
    jd_text: str = Field(..., min_length=1)
    resume_text: str = Field(..., min_length=1)
    interview_type: str = "targeted_mock"
    difficulty: Difficulty = Difficulty.medium
    duration_minutes: int = Field(default=20, ge=10, le=45)


class InterviewSessionSummary(SchemaModel):
    session_id: str
    target_role: str
    status: str

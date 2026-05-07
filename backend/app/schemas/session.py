"""Session, report, history, and orchestration-state schemas."""

from datetime import datetime

from pydantic import Field

from backend.app.schemas.coaching import Coaching
from backend.app.schemas.common import Difficulty, SchemaModel, SessionStatus, SourceText, WorkflowStep, new_id, utc_now
from backend.app.schemas.evaluation import Evaluation
from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.interview import InterviewMessage, InterviewPlan
from backend.app.schemas.jd import JDAnalysis
from backend.app.schemas.optimization import ResumeOptimization
from backend.app.schemas.resume import ResumeAnalysis


class SessionInput(SchemaModel):
    target_role: str = Field(..., min_length=1)
    jd: SourceText
    resume: SourceText
    interview_type: str = "targeted_mock"
    difficulty: Difficulty = Difficulty.medium
    duration_minutes: int = Field(default=20, ge=10, le=45)


class InterviewSessionEntity(SchemaModel):
    session_id: str = Field(default_factory=lambda: new_id("session"))
    target_role: str = Field(..., min_length=1)
    status: SessionStatus = SessionStatus.draft
    input: SessionInput
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class InterviewReportEntity(SchemaModel):
    report_id: str = Field(default_factory=lambda: new_id("report"))
    session_id: str
    evaluation: Evaluation
    coaching: Coaching
    generated_at: datetime = Field(default_factory=utc_now)


class HistoryItem(SchemaModel):
    session_id: str
    target_role: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    overall_score: int | None = Field(default=None, ge=0, le=100)
    weak_area_summary: list[str] = Field(default_factory=list)
    latest_report_id: str | None = None


class InterviewPilotState(SchemaModel):
    """Unified internal state for future backend or LangGraph orchestration."""

    session_id: str = Field(default_factory=lambda: new_id("session"))
    status: SessionStatus = SessionStatus.draft
    current_step: WorkflowStep = WorkflowStep.jd_analysis
    input: SessionInput | None = None
    jd_analysis: JDAnalysis | None = None
    resume_analysis: ResumeAnalysis | None = None
    gap_analysis: GapAnalysis | None = None
    resume_optimization: ResumeOptimization | None = None
    interview_plan: InterviewPlan | None = None
    messages: list[InterviewMessage] = Field(default_factory=list)
    evaluation: Evaluation | None = None
    coaching: Coaching | None = None
    report: InterviewReportEntity | None = None
    errors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SessionCreateRequest(SchemaModel):
    input: SessionInput


class SessionUpdateRequest(SchemaModel):
    status: SessionStatus | None = None
    current_step: WorkflowStep | None = None
    jd_analysis: JDAnalysis | None = None
    resume_analysis: ResumeAnalysis | None = None
    gap_analysis: GapAnalysis | None = None
    resume_optimization: ResumeOptimization | None = None
    interview_plan: InterviewPlan | None = None
    messages: list[InterviewMessage] | None = None
    errors: list[str] | None = None


class SessionFinishRequest(SchemaModel):
    report_id: str | None = None


class SessionResponse(SchemaModel):
    session: InterviewPilotState


class HistoryResponse(SchemaModel):
    items: list[HistoryItem] = Field(default_factory=list)

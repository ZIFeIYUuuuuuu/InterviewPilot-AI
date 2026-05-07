"""Report response schemas for user-facing practice feedback."""

from datetime import datetime

from pydantic import Field

from backend.app.schemas.coaching import CoachPrompt, Coaching
from backend.app.schemas.common import SchemaModel, new_id, utc_now
from backend.app.schemas.evaluation import Evaluation, EvaluatorPrompt
from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.interview import InterviewSessionState
from backend.app.schemas.optimization import ResumeOptimization


class PracticeReport(SchemaModel):
    session_id: str
    evaluation: Evaluation
    coaching: Coaching
    gap_analysis: GapAnalysis
    resume_optimization: ResumeOptimization | None = None
    disclaimer: str = Field(
        default="评分仅用于面试练习反馈，不代表招聘、录用或淘汰决定。"
    )


class StoredPracticeReport(SchemaModel):
    report_id: str = Field(default_factory=lambda: new_id("report"))
    session_id: str
    report: PracticeReport
    generated_at: datetime = Field(default_factory=utc_now)


class ReportGenerationRequest(SchemaModel):
    interview_session: InterviewSessionState
    resume_optimization: ResumeOptimization | None = None


class SessionReportRequest(SchemaModel):
    resume_optimization: ResumeOptimization | None = None


class ReportGenerationResponse(SchemaModel):
    report: PracticeReport
    evaluator_prompt: EvaluatorPrompt
    coach_prompt: CoachPrompt
    stored_report: StoredPracticeReport | None = None

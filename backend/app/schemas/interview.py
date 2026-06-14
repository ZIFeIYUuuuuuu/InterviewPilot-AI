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


class InterviewType(str, Enum):
    targeted_mock = "targeted_mock"
    content_focus = "content_focus"
    role_fit = "role_fit"
    project_deep_dive = "project_deep_dive"
    group = "group"


class InterviewerPersona(str, Enum):
    warm = "warm"
    technical = "technical"
    pressure = "pressure"


class VoiceProvider(str, Enum):
    disabled = "disabled"
    browser = "browser"
    aliyun = "aliyun"
    doubao = "doubao"


class InterviewPlan(SchemaModel):
    interview_type: InterviewType = InterviewType.targeted_mock
    interviewer_persona: InterviewerPersona = InterviewerPersona.technical
    duration_minutes: int = Field(..., ge=10, le=45)
    difficulty: Difficulty = Difficulty.medium
    sections: list[InterviewSection] = Field(default_factory=list)
    max_questions: int = Field(..., ge=1, le=30)
    plan_summary: str = Field(..., min_length=1)


class InterviewPlanRequest(SchemaModel):
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    gap_analysis: GapAnalysis
    interview_type: InterviewType = InterviewType.targeted_mock
    interviewer_persona: InterviewerPersona = InterviewerPersona.technical
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
    session_id: str | None = None
    interview_plan: InterviewPlan
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    gap_analysis: GapAnalysis
    voice_provider: VoiceProvider = VoiceProvider.browser


class InterviewSessionState(SchemaModel):
    session_id: str = Field(default_factory=lambda: new_id("live_session"))
    status: LiveInterviewStatus = LiveInterviewStatus.in_progress
    interview_plan: InterviewPlan
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    gap_analysis: GapAnalysis
    voice_provider: VoiceProvider = VoiceProvider.browser
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
    interview_type: InterviewType = InterviewType.targeted_mock
    interviewer_persona: InterviewerPersona = InterviewerPersona.technical
    difficulty: Difficulty = Difficulty.medium
    duration_minutes: int = Field(default=20, ge=10, le=45)


class InterviewSessionSummary(SchemaModel):
    session_id: str
    target_role: str
    status: str


class VoiceProviderStatus(SchemaModel):
    provider: VoiceProvider
    display_name: str
    configured: bool
    enabled: bool
    required_env_vars: list[str] = Field(default_factory=list)
    model: str | None = None
    voice_id: str | None = None
    note: str


class VoicePersonaProfile(SchemaModel):
    persona: InterviewerPersona
    display_name: str
    model: str
    voice_id: str
    speech_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    note: str


class InterviewVoiceConfigResponse(SchemaModel):
    default_provider: VoiceProvider
    browser_fallback_available: bool = True
    providers: list[VoiceProviderStatus] = Field(default_factory=list)
    persona_profiles: list[VoicePersonaProfile] = Field(default_factory=list)
    privacy_or_boundary_note: str


class VoiceSynthesisRequest(SchemaModel):
    text: str = Field(..., min_length=1, max_length=1200)
    provider: VoiceProvider = VoiceProvider.aliyun
    persona: InterviewerPersona = InterviewerPersona.technical
    audio_format: str = Field(default="mp3", min_length=2, max_length=8)
    sample_rate: int = Field(default=24000, ge=8000, le=48000)


class VoiceSynthesisResponse(SchemaModel):
    provider: VoiceProvider
    persona: InterviewerPersona
    model: str | None = None
    voice_id: str | None = None
    audio_url: str | None = None
    audio_base64: str | None = None
    audio_format: str = "mp3"
    sample_rate: int = 24000
    used_fallback: bool
    message: str
    request_id: str | None = None
    expires_at: int | None = None

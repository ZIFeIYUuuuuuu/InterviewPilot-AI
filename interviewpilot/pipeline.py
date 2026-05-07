"""High-level orchestration for the InterviewPilot AI MVP."""

from __future__ import annotations

from .analysis import analyze_gaps, analyze_jd, analyze_resume, suggest_resume_optimization
from .interview import create_interview_plan, starter_questions
from .models import MVPInterviewSession


def build_mvp_session(
    jd_text: str,
    resume_text: str,
    interview_type: str = "targeted_mock",
    difficulty: str = "medium",
    duration_minutes: int = 20,
) -> MVPInterviewSession:
    jd_analysis = analyze_jd(jd_text)
    resume_analysis = analyze_resume(resume_text)
    gap_analysis = analyze_gaps(jd_analysis, resume_analysis)
    resume_optimization = suggest_resume_optimization(jd_analysis, resume_analysis, gap_analysis)
    interview_plan = create_interview_plan(
        jd_analysis,
        resume_analysis,
        gap_analysis,
        interview_type=interview_type,
        difficulty=difficulty,
        duration_minutes=duration_minutes,
    )
    questions = starter_questions(interview_plan, gap_analysis, resume_analysis)
    return MVPInterviewSession(
        jd_analysis=jd_analysis,
        resume_analysis=resume_analysis,
        gap_analysis=gap_analysis,
        resume_optimization=resume_optimization,
        interview_plan=interview_plan,
        starter_questions=questions,
    )

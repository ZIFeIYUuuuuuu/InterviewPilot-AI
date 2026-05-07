"""Typed data structures for the InterviewPilot AI MVP loop."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class JDAnalysis:
    role_title: str
    required_skills: list[str]
    preferred_skills: list[str]
    responsibilities: list[str]
    interview_focus: list[str]
    uncertainty_notes: list[str]
    raw_jd_text: str


@dataclass(frozen=True)
class ResumeProject:
    name: str
    tech_stack: list[str]
    highlights: list[str]
    evidence_quality: str


@dataclass(frozen=True)
class ResumeAnalysis:
    candidate_skills: list[str]
    projects: list[ResumeProject]
    strengths: list[str]
    weaknesses: list[str]
    weak_evidence_skills: list[str]
    resume_summary: str
    uncertainty_notes: list[str]
    raw_resume_text: str


@dataclass(frozen=True)
class GapAnalysis:
    matched_skills: list[str]
    missing_skills: list[str]
    weak_evidence_skills: list[str]
    high_risk_topics: list[str]
    recommended_focus: list[str]
    summary: str


@dataclass(frozen=True)
class BulletImprovementSuggestion:
    original_issue: str
    why_it_is_weak: str
    suggested_direction: str
    example_rewrite: str


@dataclass(frozen=True)
class ResumeOptimization:
    optimization_summary: str
    rewrite_targets: list[str]
    bullet_improvement_suggestions: list[BulletImprovementSuggestion]
    skill_positioning_suggestions: list[str]
    risk_warnings: list[str]


@dataclass(frozen=True)
class InterviewSection:
    name: str
    duration_minutes: int
    goal: str
    focus_topics: list[str]


@dataclass(frozen=True)
class InterviewPlan:
    interview_type: str
    duration_minutes: int
    difficulty: str
    sections: list[InterviewSection]
    max_questions: int
    plan_summary: str


@dataclass(frozen=True)
class InterviewMessage:
    role: str
    content: str
    section: str = ""


@dataclass(frozen=True)
class InterviewQuestion:
    question_type: str
    current_section: str
    question: str
    why_this_question: str
    expected_signal: str


@dataclass(frozen=True)
class RubricScore:
    score: int
    reason: str


@dataclass(frozen=True)
class Evaluation:
    overall_score: int
    dimension_scores: dict[str, RubricScore]
    strengths: list[str]
    weaknesses: list[str]
    risk_flags: list[str]
    summary: str


@dataclass(frozen=True)
class CoachingImprovement:
    issue: str
    why_it_matters: str
    suggestion: str
    example_answer_guidance: str


@dataclass(frozen=True)
class CoachingReport:
    summary: str
    top_improvements: list[CoachingImprovement]
    practice_plan: list[str]
    next_round_focus: list[str]


@dataclass(frozen=True)
class MVPInterviewSession:
    jd_analysis: JDAnalysis
    resume_analysis: ResumeAnalysis
    gap_analysis: GapAnalysis
    resume_optimization: ResumeOptimization
    interview_plan: InterviewPlan
    starter_questions: list[InterviewQuestion] = field(default_factory=list)

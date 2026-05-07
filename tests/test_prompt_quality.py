import unittest

from backend.app.schemas import (
    Difficulty,
    Evaluation,
    EvaluationDimensionScores,
    GapAnalysis,
    InterviewMessage,
    InterviewMessageRole,
    InterviewPlan,
    InterviewSection,
    JDAnalysis,
    ResumeAnalysis,
    ResumeOptimization,
    ResumeProject,
    RubricScore,
)
from backend.app.services.coach_prompt import build_coach_prompt
from backend.app.services.evaluator_prompt import build_evaluator_prompt
from backend.app.services.gap_prompt import build_gap_analysis_prompt
from backend.app.services.interview_planner_prompt import build_interview_planner_prompt
from backend.app.services.interviewer_prompt import build_interviewer_prompt
from backend.app.services.jd_prompt import build_jd_analyzer_prompt
from backend.app.services.optimization_prompt import build_resume_optimization_prompt
from backend.app.services.prompt_contract import PROMPT_VERSION
from backend.app.services.resume_prompt import build_resume_analyzer_prompt


class PromptQualityTests(unittest.TestCase):
    def setUp(self):
        self.jd = JDAnalysis(
            role_title="Backend Engineer",
            required_skills=["Python", "FastAPI", "API design"],
            preferred_skills=["AWS"],
            responsibilities=["Build and maintain backend APIs"],
            interview_focus=["API design", "FastAPI depth"],
            uncertainty_notes=[],
        )
        self.resume = ResumeAnalysis(
            candidate_skills=["Python", "FastAPI"],
            projects=[
                ResumeProject(
                    name="Interview API",
                    tech_stack=["Python", "FastAPI"],
                    highlights=["Built endpoints for a practice app"],
                    evidence_quality="medium",
                )
            ],
            strengths=["Backend project evidence"],
            weaknesses=["Limited scale and ownership detail"],
            weak_evidence_skills=["FastAPI"],
            resume_summary="Candidate has backend project evidence with some weak areas.",
            uncertainty_notes=[],
        )
        self.gap = GapAnalysis(
            matched_skills=["Python"],
            missing_skills=["AWS"],
            weak_evidence_skills=["FastAPI"],
            high_risk_topics=["FastAPI depth", "API trade-offs"],
            recommended_focus=["Ask for one concrete FastAPI design example"],
            summary="Good Python evidence, weak FastAPI proof, and missing AWS evidence.",
        )
        self.optimization = ResumeOptimization(
            optimization_summary="Strengthen truthful FastAPI evidence.",
            rewrite_targets=["Interview API bullet"],
            bullet_improvement_suggestions=[],
            skill_positioning_suggestions=["Tie FastAPI to the project bullet."],
            risk_warnings=["FastAPI claims may trigger follow-up questions."],
        )
        self.plan = InterviewPlan(
            interview_type="targeted_mock",
            duration_minutes=20,
            difficulty=Difficulty.medium,
            sections=[
                InterviewSection(
                    name="Technical Depth",
                    duration_minutes=10,
                    goal="Probe FastAPI and API design evidence.",
                    focus_topics=["FastAPI depth", "API trade-offs"],
                )
            ],
            max_questions=5,
            plan_summary="Targeted backend mock interview.",
        )
        self.messages = [
            InterviewMessage(
                role=InterviewMessageRole.interviewer,
                content="Tell me about your FastAPI project.",
            ),
            InterviewMessage(
                role=InterviewMessageRole.candidate,
                content="I built a few endpoints but I am not sure about the details.",
            ),
        ]
        self.evaluation = Evaluation(
            overall_score=68,
            dimension_scores=EvaluationDimensionScores(
                technical_accuracy=RubricScore(score=70, reason="Mostly correct but thin."),
                depth=RubricScore(score=60, reason="Needs implementation detail."),
                structure=RubricScore(score=72, reason="Generally clear."),
                communication=RubricScore(score=75, reason="Concise and understandable."),
                role_fit=RubricScore(score=70, reason="Relevant backend evidence."),
                evidence_quality=RubricScore(score=62, reason="Weak ownership evidence."),
            ),
            strengths=["Relevant project anchor"],
            weaknesses=["Thin technical depth"],
            risk_flags=["FastAPI depth"],
            summary="Training feedback only.",
        )

    def test_core_prompts_include_shared_json_contract(self):
        prompts = [
            build_jd_analyzer_prompt("Need Python and FastAPI."),
            build_resume_analyzer_prompt("Python, FastAPI project."),
            build_gap_analysis_prompt(self.jd, self.resume),
            build_resume_optimization_prompt(self.jd, self.resume, self.gap),
            build_interview_planner_prompt(
                self.jd,
                self.resume,
                self.gap,
                "targeted_mock",
                Difficulty.medium,
                20,
            ),
            build_interviewer_prompt(
                self.plan,
                "Technical Depth",
                self.messages,
                self.messages[-1].content,
                self.gap,
                self.resume,
            ),
            build_evaluator_prompt(self.jd, self.resume, self.gap, self.plan, self.messages),
            build_coach_prompt(self.evaluation, self.gap, self.optimization, self.messages),
        ]

        for prompt in prompts:
            with self.subTest(prompt=prompt[:80]):
                self.assertIn(f"Prompt version: {PROMPT_VERSION}", prompt)
                self.assertIn("Return exactly one valid JSON object matching the Output schema", prompt)
                self.assertIn("Do not wrap the JSON in markdown fences", prompt)
                self.assertIn("do not add extra keys", prompt)
                self.assertIn("Use empty arrays [] instead of null for list fields", prompt)

    def test_prompt_schemas_align_with_domain_models(self):
        jd_prompt = build_jd_analyzer_prompt("Backend Engineer JD")
        resume_prompt = build_resume_analyzer_prompt("Backend Engineer resume")

        self.assertIn('"raw_jd_text": "string | null"', jd_prompt)
        self.assertIn('"raw_resume_text": "string | null"', resume_prompt)
        self.assertIn('"evidence_quality": "high | medium | low"', resume_prompt)

    def test_quality_guardrails_are_present_for_risky_agents(self):
        gap_prompt = build_gap_analysis_prompt(self.jd, self.resume)
        interviewer_prompt = build_interviewer_prompt(
            self.plan,
            "Technical Depth",
            self.messages,
            self.messages[-1].content,
            self.gap,
            self.resume,
        )
        evaluator_prompt = build_evaluator_prompt(self.jd, self.resume, self.gap, self.plan, self.messages)
        coach_prompt = build_coach_prompt(self.evaluation, self.gap, self.optimization, self.messages)

        self.assertIn("Do not classify a skill as missing if the evidence is merely weak", gap_prompt)
        self.assertIn("Ask exactly one primary question", interviewer_prompt)
        self.assertIn("Do not reveal evaluation or score", interviewer_prompt)
        self.assertIn("Scores must be integers from 0 to 100", evaluator_prompt)
        self.assertIn("not a hiring verdict", evaluator_prompt)
        self.assertIn("concrete next action", coach_prompt)
        self.assertIn("Do not suggest fabricated stories or fake examples", coach_prompt)


if __name__ == "__main__":
    unittest.main()

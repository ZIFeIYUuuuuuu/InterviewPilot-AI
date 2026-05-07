import unittest

from pydantic import ValidationError

from backend.app.schemas import (
    Coaching,
    CoachingImprovement,
    Evaluation,
    EvaluationDimensionScores,
    GapAnalysis,
    InterviewMessage,
    InterviewMessageRole,
    InterviewPilotState,
    InterviewPlan,
    InterviewSection,
    InterviewerOutput,
    JDAnalysis,
    ResumeAnalysis,
    ResumeOptimization,
    ResumeProject,
    RubricScore,
    SessionInput,
    SourceText,
)


class DomainSchemaTests(unittest.TestCase):
    def test_agent_prompt_outputs_validate(self):
        jd = JDAnalysis(
            role_title="Backend Engineer",
            required_skills=["Python", "FastAPI"],
            preferred_skills=["AWS"],
            responsibilities=["Build APIs"],
            interview_focus=["API design"],
            uncertainty_notes=[],
        )
        resume = ResumeAnalysis(
            candidate_skills=["Python"],
            projects=[
                ResumeProject(
                    name="API project",
                    tech_stack=["Python", "FastAPI"],
                    highlights=["Built an API service"],
                    evidence_quality="medium",
                )
            ],
            strengths=["Project experience"],
            weaknesses=["Limited scale evidence"],
            weak_evidence_skills=["FastAPI"],
            resume_summary="Candidate has backend project evidence.",
            uncertainty_notes=[],
        )
        gap = GapAnalysis(
            matched_skills=["Python"],
            missing_skills=[],
            weak_evidence_skills=["FastAPI"],
            high_risk_topics=["FastAPI depth"],
            recommended_focus=["API design"],
            summary="Mostly matched with one weak-evidence skill.",
        )
        optimization = ResumeOptimization(
            optimization_summary="Strengthen project evidence.",
            rewrite_targets=["API project bullet"],
            bullet_improvement_suggestions=[],
            skill_positioning_suggestions=["Put FastAPI near API project"],
            risk_warnings=["Do not invent metrics."],
        )
        plan = InterviewPlan(
            interview_type="targeted_mock",
            duration_minutes=20,
            difficulty="medium",
            sections=[
                InterviewSection(
                    name="Technical Depth",
                    duration_minutes=10,
                    goal="Test API design depth",
                    focus_topics=["API design"],
                )
            ],
            max_questions=6,
            plan_summary="Backend targeted mock interview.",
        )
        question = InterviewerOutput(
            question_type="new_question",
            current_section="Technical Depth",
            question="How did you design the API boundaries?",
            why_this_question="It tests JD-relevant backend design.",
            expected_signal="Trade-off reasoning.",
        )
        evaluation = Evaluation(
            overall_score=72,
            dimension_scores=EvaluationDimensionScores(
                technical_accuracy=RubricScore(score=70, reason="Mostly correct."),
                depth=RubricScore(score=68, reason="Needs more detail."),
                structure=RubricScore(score=75, reason="Readable structure."),
                communication=RubricScore(score=78, reason="Clear enough."),
                role_fit=RubricScore(score=72, reason="Relevant to backend role."),
                evidence_quality=RubricScore(score=65, reason="Needs stronger evidence."),
            ),
            strengths=["Clear API framing"],
            weaknesses=["Thin evidence"],
            risk_flags=["FastAPI depth"],
            summary="Training feedback only.",
        )
        coaching = Coaching(
            summary="Practice deeper project evidence.",
            top_improvements=[
                CoachingImprovement(
                    issue="Thin FastAPI evidence",
                    why_it_matters="The JD needs backend depth.",
                    suggestion="Prepare one implementation example.",
                    example_answer_guidance="Use context, action, trade-off, result.",
                )
            ],
            practice_plan=["Run one API design drill."],
            next_round_focus=["FastAPI depth"],
        )

        self.assertEqual("Backend Engineer", jd.role_title)
        self.assertEqual("medium", resume.projects[0].evidence_quality.value)
        self.assertEqual(["Python"], gap.matched_skills)
        self.assertIn("Do not invent metrics.", optimization.risk_warnings)
        self.assertEqual("medium", plan.difficulty.value)
        self.assertEqual("new_question", question.question_type.value)
        self.assertEqual(72, evaluation.overall_score)
        self.assertEqual(1, len(coaching.top_improvements))

    def test_strict_schema_rejects_unknown_agent_output_keys(self):
        with self.assertRaises(ValidationError):
            JDAnalysis(
                role_title="Backend Engineer",
                required_skills=[],
                preferred_skills=[],
                responsibilities=[],
                interview_focus=[],
                uncertainty_notes=[],
                hiring_recommendation="hire",
            )

    def test_unified_state_can_hold_workflow_outputs(self):
        state = InterviewPilotState(
            input=SessionInput(
                target_role="Backend Engineer",
                jd=SourceText(text="Backend JD"),
                resume=SourceText(text="Resume text"),
            ),
            messages=[
                InterviewMessage(
                    role=InterviewMessageRole.candidate,
                    content="I built a backend API with clear trade-offs.",
                )
            ],
        )

        self.assertTrue(state.session_id.startswith("session_"))
        self.assertEqual("jd_analysis", state.current_step.value)
        self.assertEqual(1, len(state.messages))


if __name__ == "__main__":
    unittest.main()

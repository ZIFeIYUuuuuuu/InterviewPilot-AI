import unittest

from interviewpilot.interview import generate_next_question
from interviewpilot.models import InterviewMessage
from interviewpilot.pipeline import build_mvp_session
from interviewpilot.report import create_coaching_report, evaluate_interview


JD_TEXT = """Backend Engineer
Requirements: Python, FastAPI, PostgreSQL, Redis, Docker, REST API.
Responsibilities: build scalable APIs, optimize database performance, and discuss system design trade-offs.
Preferred: AWS, CI/CD, testing experience.
"""

RESUME_TEXT = """Backend API Project: Built a FastAPI service with PostgreSQL and Redis caching.
Implemented REST APIs, Docker deployment, and reduced average lookup latency by 35%.
Skills: Python, FastAPI, PostgreSQL, Redis, Docker, REST API, Testing.
"""


class MVPFlowTests(unittest.TestCase):
    def test_builds_full_candidate_training_session(self):
        session = build_mvp_session(JD_TEXT, RESUME_TEXT)

        self.assertIn("Python", session.jd_analysis.required_skills)
        self.assertIn("FastAPI", session.resume_analysis.candidate_skills)
        self.assertIn("FastAPI", session.gap_analysis.matched_skills)
        self.assertGreaterEqual(len(session.interview_plan.sections), 3)
        self.assertGreaterEqual(len(session.starter_questions), 3)
        self.assertIn("不要加入", " ".join(session.resume_optimization.risk_warnings))

    def test_follow_up_is_generated_for_vague_answers(self):
        session = build_mvp_session(JD_TEXT, RESUME_TEXT)
        question = generate_next_question(
            session.interview_plan,
            [InterviewMessage(role="candidate", content="I built the backend.", section="Technical Depth")],
            session.gap_analysis,
            session.resume_analysis,
        )

        self.assertEqual("follow_up", question.question_type)
        self.assertIn("具体", question.question)

    def test_report_is_practice_feedback_not_hiring_judgment(self):
        session = build_mvp_session(JD_TEXT, RESUME_TEXT)
        messages = [
            InterviewMessage(role="interviewer", content=session.starter_questions[0].question),
            InterviewMessage(
                role="candidate",
                content=(
                    "First I would describe the FastAPI service context. Then I would explain why Redis caching "
                    "was chosen, the PostgreSQL query trade-off, and the result: latency dropped by 35%."
                ),
            ),
        ]
        evaluation = evaluate_interview(session.jd_analysis, session.gap_analysis, session.interview_plan, messages)
        coaching = create_coaching_report(evaluation, session.gap_analysis, session.resume_optimization, messages)

        self.assertGreaterEqual(evaluation.overall_score, 50)
        self.assertIn("不是招聘判断", evaluation.summary)
        self.assertGreaterEqual(len(coaching.practice_plan), 3)
        self.assertNotIn("hire", evaluation.summary.casefold())


if __name__ == "__main__":
    unittest.main()

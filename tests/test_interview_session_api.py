import unittest
import os
import tempfile
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.json_store import clear_store_for_tests


JD_ANALYSIS = {
    "role_title": "Backend Engineer",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
    "preferred_skills": ["AWS", "Testing"],
    "responsibilities": ["Build reliable APIs and optimize data access."],
    "interview_focus": ["API design", "Database trade-offs"],
    "uncertainty_notes": [],
    "raw_jd_text": "Backend Engineer requirements...",
}

RESUME_ANALYSIS = {
    "candidate_skills": ["Python", "FastAPI", "PostgreSQL"],
    "projects": [
        {
            "name": "Backend API",
            "tech_stack": ["Python", "FastAPI"],
            "highlights": ["Built a FastAPI service and explained API boundaries."],
            "evidence_quality": "medium",
        }
    ],
    "strengths": ["Has backend API project evidence."],
    "weaknesses": ["PostgreSQL evidence is thin."],
    "weak_evidence_skills": ["PostgreSQL"],
    "resume_summary": "Candidate has backend project evidence with thin database evidence.",
    "uncertainty_notes": [],
    "raw_resume_text": "Backend resume...",
}

GAP_ANALYSIS = {
    "matched_skills": ["Python", "FastAPI"],
    "missing_skills": ["Redis"],
    "weak_evidence_skills": ["PostgreSQL"],
    "high_risk_topics": [
        "Missing required JD evidence: Redis",
        "Weak resume evidence for JD skill: PostgreSQL",
    ],
    "recommended_focus": ["Redis", "PostgreSQL", "API design"],
    "summary": "Matched 2 skills; Redis missing; PostgreSQL weak.",
}


class InterviewSessionAPITests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ["INTERVIEWPILOT_STORE_PATH"] = os.path.join(self.tempdir.name, "store.json")
        clear_store_for_tests()
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.pop("INTERVIEWPILOT_STORE_PATH", None)
        self.tempdir.cleanup()

    def _plan(self, duration=20, difficulty="medium", interview_type="targeted_mock", persona="technical"):
        response = self.client.post(
            "/api/v1/interview/plan",
            json={
                "jd_analysis": JD_ANALYSIS,
                "resume_analysis": RESUME_ANALYSIS,
                "gap_analysis": GAP_ANALYSIS,
                "interview_type": interview_type,
                "interviewer_persona": persona,
                "difficulty": difficulty,
                "duration_minutes": duration,
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()["interview_plan"]

    def _start(self, duration=20, persona="technical", voice_provider="browser"):
        response = self.client.post(
            "/api/v1/interview/sessions",
            json={
                "interview_plan": self._plan(duration=duration, persona=persona),
                "jd_analysis": JD_ANALYSIS,
                "resume_analysis": RESUME_ANALYSIS,
                "gap_analysis": GAP_ANALYSIS,
                "voice_provider": voice_provider,
            },
        )
        self.assertEqual(200, response.status_code)
        return response.json()

    def test_start_session_returns_role_and_resume_anchored_question(self):
        body = self._start()
        output = body["interviewer_output"]
        session = body["session"]

        self.assertEqual("in_progress", session["status"])
        self.assertEqual(1, session["current_question_count"])
        self.assertEqual("new_question", output["question_type"])
        self.assertIn("Backend Engineer", output["question"])
        self.assertIn("Backend API", output["question"])
        self.assertIn("Generate the next best interview question", body["interviewer_prompt"]["prompt"])

    def test_short_answer_gets_contextual_follow_up_without_live_score(self):
        body = self._start()
        session_id = body["session"]["session_id"]
        response = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "answer", "answer": "I used it a bit."},
        )
        self.assertEqual(200, response.status_code)
        turn = response.json()
        output = turn["interviewer_output"]

        self.assertEqual("follow_up", output["question_type"])
        self.assertIn("I used it a bit", output["question"])
        self.assertIn("职责", output["question"])
        self.assertIn(turn["session"]["latest_question"]["current_section"], output["current_section"])
        live_text = " ".join(
            [
                output["question"],
                output["why_this_question"],
                output["expected_signal"],
            ]
        ).casefold()
        self.assertNotIn("score", live_text)
        self.assertNotIn("评分", live_text)

    def test_follow_up_is_anchored_to_latest_answer_and_context(self):
        body = self._start()
        session_id = body["session"]["session_id"]
        answer = "我只是参与了一些 Redis 相关工作。"
        response = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "answer", "answer": answer},
        )

        self.assertEqual(200, response.status_code)
        output = response.json()["interviewer_output"]
        self.assertEqual("follow_up", output["question_type"])
        self.assertIn("Redis", output["question"])
        self.assertIn(answer, output["question"])
        self.assertIn("当前环节", output["why_this_question"])

    def test_detailed_answer_moves_to_new_question_and_keeps_state_stable(self):
        body = self._start()
        session_id = body["session"]["session_id"]
        detailed_answer = (
            "In the FastAPI project, I owned the API route boundaries because the service needed "
            "clear validation and test coverage. I designed request schemas, added database access "
            "checks, measured latency around cache reads, and chose a simpler PostgreSQL query path "
            "instead of Redis because the data size was small."
        )
        response = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "answer", "answer": detailed_answer},
        )
        self.assertEqual(200, response.status_code)
        body = response.json()

        self.assertEqual("new_question", body["interviewer_output"]["question_type"])
        self.assertEqual(2, body["session"]["current_question_count"])
        self.assertEqual(3, len(body["session"]["messages"]))

    def test_controls_skip_next_regenerate_and_end(self):
        body = self._start()
        session_id = body["session"]["session_id"]
        first_question = body["interviewer_output"]["question"]

        regenerated = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "regenerate"},
        ).json()
        self.assertEqual(1, regenerated["session"]["current_question_count"])
        self.assertNotEqual(first_question, regenerated["interviewer_output"]["question"])

        skipped = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "skip"},
        ).json()
        self.assertEqual(2, skipped["session"]["current_question_count"])

        moved = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "next"},
        ).json()
        self.assertEqual(3, moved["session"]["current_question_count"])

        ended = self.client.post(
            f"/api/v1/interview/sessions/{session_id}/turn",
            json={"action": "end"},
        ).json()
        self.assertEqual("completed", ended["session"]["status"])
        self.assertIsNone(ended["interviewer_output"])

    def test_three_to_five_rounds_do_not_corrupt_state(self):
        body = self._start(duration=20)
        session_id = body["session"]["session_id"]
        for index in range(4):
            response = self.client.post(
                f"/api/v1/interview/sessions/{session_id}/turn",
                json={
                    "action": "answer",
                    "answer": (
                        f"Round {index}: I designed an API because FastAPI schemas helped validation, "
                        "tested database behavior, measured latency, and explained the trade-off."
                    ),
                },
            )
            self.assertEqual(200, response.status_code)
            body = response.json()
            self.assertGreaterEqual(body["session"]["current_section_index"], 0)
            self.assertLess(
                body["session"]["current_section_index"],
                len(body["session"]["interview_plan"]["sections"]),
            )

        session = self.client.get(f"/api/v1/interview/sessions/{session_id}").json()
        self.assertEqual(body["session"]["current_question_count"], session["current_question_count"])
        self.assertGreaterEqual(len(session["messages"]), 5)

    def test_persona_changes_question_tone_without_breaking_controls(self):
        warm = self._start(persona="warm")
        pressure = self._start(persona="pressure")

        self.assertIn("慢慢来", warm["interviewer_output"]["question"])
        self.assertIn("追得更细", pressure["interviewer_output"]["question"])
        self.assertEqual("warm", warm["session"]["interview_plan"]["interviewer_persona"])
        self.assertEqual("pressure", pressure["session"]["interview_plan"]["interviewer_persona"])

    def test_voice_provider_is_recorded_but_missing_keys_do_not_block_session(self):
        body = self._start(voice_provider="doubao")

        self.assertEqual("in_progress", body["session"]["status"])
        self.assertEqual("doubao", body["session"]["voice_provider"])
        self.assertTrue(body["interviewer_output"]["question"])

    def test_voice_config_hides_key_values_and_exposes_browser_fallback(self):
        os.environ["INTERVIEWPILOT_ALIYUN_VOICE_API_KEY"] = "secret-test-key"
        try:
            response = self.client.get("/api/v1/interview/voice/config")
        finally:
            os.environ.pop("INTERVIEWPILOT_ALIYUN_VOICE_API_KEY", None)

        self.assertEqual(200, response.status_code)
        body = response.json()
        serialized = str(body)
        self.assertTrue(body["browser_fallback_available"])
        self.assertIn("browser", [provider["provider"] for provider in body["providers"]])
        self.assertIn("aliyun", [provider["provider"] for provider in body["providers"]])
        self.assertNotIn("secret-test-key", serialized)

    def test_voice_synthesis_missing_key_returns_browser_fallback(self):
        for name in [
            "INTERVIEWPILOT_ALIYUN_VOICE_API_KEY",
            "DASHSCOPE_API_KEY",
            "INTERVIEWPILOT_LLM_API_KEY",
            "ALIYUN_VOICE_API_KEY",
        ]:
            os.environ.pop(name, None)

        response = self.client.post(
            "/api/v1/interview/voice/synthesize",
            json={"text": "请介绍你在 Redis 缓存设计里的具体职责。", "provider": "aliyun", "persona": "technical"},
        )

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertTrue(body["used_fallback"])
        self.assertIsNone(body["audio_url"])
        self.assertEqual("longshuo_v3", body["voice_id"])
        self.assertIn("兜底", body["message"])

    def test_voice_synthesis_aliyun_success_returns_audio_url_without_key(self):
        os.environ["INTERVIEWPILOT_ALIYUN_VOICE_API_KEY"] = "secret-voice-key"
        fake_response = Mock()
        fake_response.__enter__ = Mock(return_value=fake_response)
        fake_response.__exit__ = Mock(return_value=None)
        fake_response.read.return_value = (
            b'{"request_id":"req_1","output":{"audio":{"url":"https://example.test/audio.mp3"}}}'
        )
        try:
            with patch("backend.app.services.voice_synthesis.urlopen", return_value=fake_response) as mocked_urlopen:
                response = self.client.post(
                    "/api/v1/interview/voice/synthesize",
                    json={
                        "text": "请继续追问数据库索引设计的边界。",
                        "provider": "aliyun",
                        "persona": "pressure",
                    },
                )
        finally:
            os.environ.pop("INTERVIEWPILOT_ALIYUN_VOICE_API_KEY", None)

        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertFalse(body["used_fallback"])
        self.assertEqual("https://example.test/audio.mp3", body["audio_url"])
        self.assertEqual("longfei_v3", body["voice_id"])
        self.assertNotIn("secret-voice-key", str(body))
        self.assertTrue(mocked_urlopen.called)


if __name__ == "__main__":
    unittest.main()

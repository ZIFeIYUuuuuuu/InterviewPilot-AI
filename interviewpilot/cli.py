"""Command line entry point for the first InterviewPilot AI MVP loop."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path

from .models import InterviewMessage
from .pipeline import build_mvp_session
from .report import create_coaching_report, evaluate_interview


SAMPLE_JD = """Backend Engineer
Requirements: Python, FastAPI, PostgreSQL, Redis, Docker, REST API.
Responsibilities: build scalable APIs, optimize database performance, and collaborate on system design.
Preferred: AWS, CI/CD, testing experience.
"""

SAMPLE_RESUME = """Backend API Project: Built a FastAPI service with PostgreSQL and Redis caching.
Implemented REST APIs, Docker deployment, and reduced average lookup latency by 35%.
Skills: Python, FastAPI, PostgreSQL, Redis, Docker, REST API, Testing.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="运行 InterviewPilot AI 文字版 MVP 闭环。")
    parser.add_argument("--jd-file", type=Path, help="UTF-8 JD 文本文件路径。")
    parser.add_argument("--resume-file", type=Path, help="UTF-8 简历文本文件路径。")
    parser.add_argument("--sample", action="store_true", help="使用内置示例 JD 和简历运行。")
    parser.add_argument("--duration", type=int, default=20, help="面试时长，单位分钟。")
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    args = parser.parse_args()

    jd_text, resume_text = _load_inputs(args.jd_file, args.resume_file, args.sample)
    session = build_mvp_session(
        jd_text,
        resume_text,
        difficulty=args.difficulty,
        duration_minutes=args.duration,
    )
    demo_messages = _demo_transcript(session.starter_questions)
    evaluation = evaluate_interview(session.jd_analysis, session.gap_analysis, session.interview_plan, demo_messages)
    coaching = create_coaching_report(evaluation, session.gap_analysis, session.resume_optimization, demo_messages)

    print(
        json.dumps(
            {
                "jd_analysis": _to_jsonable(session.jd_analysis),
                "resume_analysis": _to_jsonable(session.resume_analysis),
                "gap_analysis": _to_jsonable(session.gap_analysis),
                "resume_optimization": _to_jsonable(session.resume_optimization),
                "interview_plan": _to_jsonable(session.interview_plan),
                "starter_questions": _to_jsonable(session.starter_questions),
                "evaluation": _to_jsonable(evaluation),
                "coaching": _to_jsonable(coaching),
            "product_boundary": "评分仅用于候选人的面试练习反馈，不代表招聘或录用决定。",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _load_inputs(jd_file: Path | None, resume_file: Path | None, use_sample: bool) -> tuple[str, str]:
    if use_sample:
        return SAMPLE_JD, SAMPLE_RESUME
    if jd_file and resume_file:
        return jd_file.read_text(encoding="utf-8"), resume_file.read_text(encoding="utf-8")
        raise SystemExit("请提供 --sample，或同时提供 --jd-file 和 --resume-file。")


def _demo_transcript(questions: list) -> list[InterviewMessage]:
    messages: list[InterviewMessage] = []
    for question in questions[:3]:
        messages.append(InterviewMessage(role="interviewer", content=question.question, section=question.current_section))
        messages.append(
            InterviewMessage(
                role="candidate",
                section=question.current_section,
        content=(
            "首先我会说明项目背景和我的实现职责。然后我会描述技术决策、取舍和结果；"
            "如果延迟优化指标属实，也会一起说明。"
        ),
            )
        )
    return messages


def _to_jsonable(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


if __name__ == "__main__":
    main()

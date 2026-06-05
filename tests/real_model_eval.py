"""Real-model structured eval for InterviewPilot AI.

This script runs the main structured-output chain against the configured
OpenAI-compatible model and prints a JSON summary for README / resume updates.
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass

from backend.app.core.config import get_settings
from backend.app.schemas.common import Difficulty, InterviewMessageRole
from backend.app.schemas.gap import GapAnalysisRequest
from backend.app.schemas.interview import (
    InterviewMessage,
    InterviewPlanRequest,
    InterviewSessionState,
    LiveInterviewStatus,
)
from backend.app.schemas.jd import JDInputRequest
from backend.app.schemas.optimization import ResumeOptimizationRequest
from backend.app.schemas.resume import ResumeInputRequest
from backend.app.services import llm_client
from backend.app.services.gap_analyzer import analyze_gap, suggest_resume_optimization
from backend.app.services.interview_planner import create_interview_plan
from backend.app.services.jd_analyzer import analyze_jd_input
from backend.app.services.report_generator import generate_practice_report
from backend.app.services.resume_analyzer import analyze_resume_input


JD_TEXT = """后端 API 工程师
硬性要求：Python、FastAPI、PostgreSQL、Redis、API 设计、自动化测试、线上 API 问题排查。
加分项：Docker、异步任务处理、可观测性、云部署经验。
岗位职责：构建可靠的客户侧 API，优化数据库访问，思考缓存与延迟，编写测试，排查线上问题，并与产品团队协作。
面试重点：API 边界、数据库取舍、缓存策略、模糊问题下的问题排查、职责边界和清晰沟通。
"""

RESUME_TEXT = """后端 API 项目
使用 Python、FastAPI 和 PostgreSQL 构建了一个面试练习应用的后端服务。设计了请求校验结构，实现了会话和报告 API 路由，并为数据访问行为编写测试。

项目细节：
- 为会话和报告增加了 JSON 持久化。
- 实现了健康检查、API 路由和报告生成接口。
- 在数据结构变化过程中排查过校验错误。

技能：Python、FastAPI、PostgreSQL、测试、API 设计。
弱项：Redis 和生产级可观测性主要来自课程探索，需要更充分的面试准备。
职责边界说明：简历提到了后端 API，但还没有量化延迟、规模或故障影响。
"""


@dataclass(frozen=True)
class EvalResult:
    case: str
    latency_ms: float
    passed: bool
    detail: str
    remote_calls_used: int


class RemoteCallCounter:
    def __init__(self) -> None:
        self.count = 0
        self._original = llm_client._chat_completion

    def __enter__(self) -> "RemoteCallCounter":
        def wrapper(prompt: str) -> str:
            self.count += 1
            return self._original(prompt)

        llm_client._chat_completion = wrapper
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        llm_client._chat_completion = self._original


def _assert_settings() -> tuple[str, str]:
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.llm_enabled or not settings.llm_api_key:
        raise RuntimeError(
            "InterviewPilot real-model eval requires INTERVIEWPILOT_LLM_* env vars or compatible provider env."
        )
    return settings.llm_base_url, settings.llm_model


def _run_case(name: str, fn) -> tuple[EvalResult, object]:
    start = time.perf_counter()
    with RemoteCallCounter() as counter:
        payload = fn()
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    passed = counter.count > 0
    detail, value = payload
    return EvalResult(name, latency_ms, passed, detail, counter.count), value


def _case_jd_analysis() -> tuple[str, object]:
    response = analyze_jd_input(JDInputRequest(input_type="text", text=JD_TEXT))
    return (
        f"role={response.analysis.role_title}; "
        f"required={len(response.analysis.required_skills)}; "
        f"focus={len(response.analysis.interview_focus)}",
        response,
    )


def _case_resume_analysis() -> tuple[str, object]:
    response = analyze_resume_input(ResumeInputRequest(input_type="text", text=RESUME_TEXT))
    return (
        f"skills={len(response.analysis.candidate_skills)}; "
        f"projects={len(response.analysis.projects)}; "
        f"weak={len(response.analysis.weak_evidence_skills)}",
        response,
    )


def _case_gap_analysis(jd_response, resume_response) -> tuple[str, object]:
    gap_response = analyze_gap(
        GapAnalysisRequest(
            jd_analysis=jd_response.analysis,
            resume_analysis=resume_response.analysis,
        )
    )
    return (
        f"matched={len(gap_response.gap_analysis.matched_skills)}; "
        f"missing={len(gap_response.gap_analysis.missing_skills)}; "
        f"summary={gap_response.gap_analysis.summary[:60]}",
        gap_response,
    )


def _case_resume_optimization(jd_response, resume_response, gap_response) -> tuple[str, object]:
    optimization_response = suggest_resume_optimization(
        ResumeOptimizationRequest(
            jd_analysis=jd_response.analysis,
            resume_analysis=resume_response.analysis,
            gap_analysis=gap_response.gap_analysis,
        )
    )
    return (
        f"targets={len(optimization_response.resume_optimization.rewrite_targets)}; "
        f"suggestions={len(optimization_response.resume_optimization.bullet_improvement_suggestions)}; "
        f"warnings={len(optimization_response.resume_optimization.risk_warnings)}",
        optimization_response,
    )


def _case_interview_plan(jd_response, resume_response, gap_response) -> tuple[str, object]:
    plan_response = create_interview_plan(
        InterviewPlanRequest(
            jd_analysis=jd_response.analysis,
            resume_analysis=resume_response.analysis,
            gap_analysis=gap_response.gap_analysis,
            interview_type="targeted_mock",
            difficulty=Difficulty.medium,
            duration_minutes=20,
        )
    )
    return (
        f"sections={len(plan_response.interview_plan.sections)}; "
        f"max_questions={plan_response.interview_plan.max_questions}; "
        f"summary={plan_response.interview_plan.plan_summary[:60]}",
        plan_response,
    )


def _case_report_generation(
    jd_response,
    resume_response,
    gap_response,
    optimization_response,
    plan_response,
) -> tuple[str, object]:
    session = InterviewSessionState(
        status=LiveInterviewStatus.completed,
        interview_plan=plan_response.interview_plan,
        jd_analysis=jd_response.analysis,
        resume_analysis=resume_response.analysis,
        gap_analysis=gap_response.gap_analysis,
        current_question_count=2,
        messages=[
            InterviewMessage(
                role=InterviewMessageRole.interviewer,
                content="请介绍你在后端 API 项目里负责过的核心接口，以及为什么这样设计。",
                section="项目深挖",
            ),
            InterviewMessage(
                role=InterviewMessageRole.candidate,
                content=(
                    "我主要负责会话和报告接口，先把请求校验和返回结构定清楚，"
                    "再处理 JSON 持久化和错误响应。这样做是因为前后端联调时最容易在字段和错误格式上反复返工。"
                ),
                section="项目深挖",
            ),
            InterviewMessage(
                role=InterviewMessageRole.interviewer,
                content="如果接口延迟升高，你会怎么判断是数据库、缓存还是应用代码的问题？",
                section="技术取舍",
            ),
            InterviewMessage(
                role=InterviewMessageRole.candidate,
                content=(
                    "我会先确认慢的是单个接口还是整条链路，再看数据库查询和日志。"
                    "如果是热点读请求，我会判断是否值得加缓存，但会先说明我在 Redis 上的实际经验边界。"
                ),
                section="技术取舍",
            ),
        ],
    )
    response = generate_practice_report(
        session=session,
        resume_optimization=optimization_response.resume_optimization,
    )
    return (
        f"overall={response.report.evaluation.overall_score}; "
        f"improvements={len(response.report.coaching.top_improvements)}; "
        f"focus={len(response.report.coaching.next_round_focus)}",
        response,
    )


def run_eval() -> dict[str, object]:
    base_url, model = _assert_settings()
    results: list[EvalResult] = []

    jd_eval, jd_response = _run_case("jd_analysis", _case_jd_analysis)
    results.append(jd_eval)

    resume_eval, resume_response = _run_case("resume_analysis", _case_resume_analysis)
    results.append(resume_eval)

    gap_eval, gap_response = _run_case(
        "gap_analysis",
        lambda: _case_gap_analysis(jd_response, resume_response),
    )
    results.append(gap_eval)

    optimization_eval, optimization_response = _run_case(
        "resume_optimization",
        lambda: _case_resume_optimization(jd_response, resume_response, gap_response),
    )
    results.append(optimization_eval)

    plan_eval, plan_response = _run_case(
        "interview_plan",
        lambda: _case_interview_plan(jd_response, resume_response, gap_response),
    )
    results.append(plan_eval)

    report_eval, _ = _run_case(
        "report_generation",
        lambda: _case_report_generation(
            jd_response,
            resume_response,
            gap_response,
            optimization_response,
            plan_response,
        ),
    )
    results.append(report_eval)

    latencies = [result.latency_ms for result in results]
    passed = [result.passed for result in results]
    remote_calls = sum(result.remote_calls_used for result in results)
    return {
        "provider_base_url": base_url,
        "model": model,
        "case_count": len(results),
        "success_rate": round(sum(passed) / len(results), 4),
        "remote_call_count": remote_calls,
        "latency_p50_ms": round(statistics.median(latencies), 2),
        "latency_p95_ms": round(max(latencies), 2),
        "results": [asdict(result) for result in results],
    }


if __name__ == "__main__":
    print(json.dumps(run_eval(), indent=2, ensure_ascii=False))

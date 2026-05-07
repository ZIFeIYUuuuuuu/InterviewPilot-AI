"""Interview Planner service."""

from __future__ import annotations

from backend.app.schemas.common import Difficulty
from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.interview import (
    InterviewPlan,
    InterviewPlanRequest,
    InterviewPlanResponse,
    InterviewPlannerPrompt,
    InterviewSection,
)
from backend.app.schemas.jd import JDAnalysis
from backend.app.schemas.resume import ResumeAnalysis
from backend.app.services.interview_planner_prompt import (
    INTERVIEW_PLANNER_TASK,
    build_interview_planner_prompt,
)
from backend.app.services.llm_client import generate_structured_output


def create_interview_plan(request: InterviewPlanRequest) -> InterviewPlanResponse:
    prompt_text = build_interview_planner_prompt(
        request.jd_analysis,
        request.resume_analysis,
        request.gap_analysis,
        request.interview_type,
        request.difficulty,
        request.duration_minutes,
    )
    plan = generate_structured_output(prompt_text, InterviewPlan) or _create_plan(
        jd=request.jd_analysis,
        resume=request.resume_analysis,
        gap=request.gap_analysis,
        interview_type=request.interview_type,
        difficulty=request.difficulty,
        duration_minutes=request.duration_minutes,
    )
    return InterviewPlanResponse(
        interview_plan=plan,
        planner_prompt=InterviewPlannerPrompt(
            task=INTERVIEW_PLANNER_TASK,
            prompt=prompt_text,
        ),
    )


def _create_plan(
    jd: JDAnalysis,
    resume: ResumeAnalysis,
    gap: GapAnalysis,
    interview_type: str,
    difficulty: Difficulty,
    duration_minutes: int,
) -> InterviewPlan:
    section_specs = _section_specs(duration_minutes, gap, resume)
    durations = _allocate_durations(duration_minutes, len(section_specs))
    sections = [
        InterviewSection(
            name=name,
            duration_minutes=duration,
            goal=_goal_for_section(name, difficulty),
            focus_topics=topics,
        )
        for (name, topics), duration in zip(section_specs, durations)
    ]
    max_questions = _max_questions(duration_minutes, difficulty)
    summary = (
        f"面向 {jd.role_title} 的 {duration_minutes} 分钟{_difficulty_label(difficulty)}模拟面试，"
        "围绕 JD 贴合度、简历证据和差距风险组织。"
    )
    return InterviewPlan(
        interview_type=interview_type,
        duration_minutes=duration_minutes,
        difficulty=difficulty,
        sections=sections,
        max_questions=max_questions,
        plan_summary=summary,
    )


def _section_specs(
    duration_minutes: int, gap: GapAnalysis, resume: ResumeAnalysis
) -> list[tuple[str, list[str]]]:
    role_fit = _focus([*gap.matched_skills[:2], *gap.recommended_focus[:2]], ["目标岗位贴合度"])
    technical = _focus(
        [*gap.missing_skills[:3], *gap.weak_evidence_skills[:3], *gap.recommended_focus[:3]],
        ["JD 关键技术深度"],
    )
    project_topics = _focus([project.name for project in resume.projects[:3]], ["最相关的简历项目"])
    risk = _focus(gap.high_risk_topics[:5] or gap.recommended_focus[:4], ["最高风险面试主题"])

    if duration_minutes <= 15:
        return [
            ("岗位匹配热身", role_fit),
            ("技术与项目深挖", _focus([*technical, *project_topics], ["技术深度"])),
            ("风险复盘", risk),
        ]
    if duration_minutes <= 30:
        return [
            ("岗位匹配热身", role_fit),
            ("技术深度", technical),
            ("项目深挖", project_topics),
            ("风险复盘", risk),
        ]
    return [
        ("岗位匹配热身", role_fit),
        ("技术基础", technical[:4]),
        ("项目深挖", project_topics),
        ("取舍与系统思考", _focus(gap.recommended_focus[:5], ["设计与取舍"])),
        ("风险复盘", risk),
    ]


def _allocate_durations(total: int, count: int) -> list[int]:
    if count == 3:
        weights = [0.22, 0.48, 0.30]
    elif count == 4:
        weights = [0.15, 0.35, 0.30, 0.20]
    else:
        weights = [0.12, 0.24, 0.26, 0.22, 0.16]
    durations = [max(2, round(total * weight)) for weight in weights]
    delta = total - sum(durations)
    durations[-1] += delta
    if durations[-1] < 1:
        durations[-2] += durations[-1] - 1
        durations[-1] = 1
    return durations


def _goal_for_section(name: str, difficulty: Difficulty) -> str:
    depth = {
        Difficulty.easy: "确认基础理解并收集真实例子",
        Difficulty.medium: "考察实践深度、职责边界和实现取舍",
        Difficulty.hard: "压力测试技术深度、模糊问题处理、取舍判断和证据质量",
    }[difficulty]
    goals = {
        "岗位匹配热身": f"把候选人最强证据连接到目标岗位，并{depth}。",
        "技术深度": f"追问 JD 关键技能，并{depth}。",
        "技术与项目深挖": f"结合 JD 关键技能和项目证据，并{depth}。",
        "技术基础": f"验证 JD 要求背后的基础能力，并{depth}。",
        "项目深挖": f"验证简历证据、实现细节，并{depth}。",
        "取舍与系统思考": f"探索设计选择、约束、替代方案，并{depth}。",
        "风险复盘": f"聚焦缺失或弱证据领域，并{depth}。",
    }
    return goals.get(name, f"执行一个结构化面试环节，用于{depth}。")


def _max_questions(duration_minutes: int, difficulty: Difficulty) -> int:
    base = max(3, duration_minutes // 4)
    adjustment = {Difficulty.easy: -1, Difficulty.medium: 0, Difficulty.hard: 1}[difficulty]
    return max(3, min(12, base + adjustment))


def _focus(items: list[str], fallback: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        clean = " ".join(str(item).split())
        key = clean.casefold()
        if clean and key not in seen:
            result.append(clean)
            seen.add(key)
    return result or fallback


def _difficulty_label(difficulty: Difficulty) -> str:
    return {
        Difficulty.easy: "简单难度",
        Difficulty.medium: "中等难度",
        Difficulty.hard: "困难难度",
    }[difficulty]

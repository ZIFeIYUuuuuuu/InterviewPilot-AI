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
    InterviewType,
    InterviewerPersona,
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
        request.interviewer_persona,
        request.difficulty,
        request.duration_minutes,
    )
    plan = generate_structured_output(prompt_text, InterviewPlan) or _create_plan(
        jd=request.jd_analysis,
        resume=request.resume_analysis,
        gap=request.gap_analysis,
        interview_type=request.interview_type,
        interviewer_persona=request.interviewer_persona,
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
    interview_type: InterviewType,
    interviewer_persona: InterviewerPersona,
    difficulty: Difficulty,
    duration_minutes: int,
) -> InterviewPlan:
    section_specs = _section_specs(duration_minutes, gap, resume, interview_type)
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
        f"面向 {jd.role_title} 的 {duration_minutes} 分钟{_difficulty_label(difficulty)}{_type_label(interview_type)}，"
        f"由{_persona_label(interviewer_persona)}主持，围绕 JD 贴合度、简历证据和差距风险组织。"
    )
    return InterviewPlan(
        interview_type=interview_type,
        interviewer_persona=interviewer_persona,
        duration_minutes=duration_minutes,
        difficulty=difficulty,
        sections=sections,
        max_questions=max_questions,
        plan_summary=summary,
    )


def _section_specs(
    duration_minutes: int, gap: GapAnalysis, resume: ResumeAnalysis, interview_type: InterviewType
) -> list[tuple[str, list[str]]]:
    project_topics = [project.name for project in resume.projects[:3]]
    opening = _focus([*project_topics[:2], *gap.matched_skills[:2], *gap.recommended_focus[:2]], ["目标岗位贴合度"])
    jd_skills = _focus(
        [*gap.missing_skills[:3], *gap.weak_evidence_skills[:3], *gap.recommended_focus[:3]],
        ["JD 关键技能追问"],
    )
    weak_evidence = _focus(
        [*gap.weak_evidence_skills[:4], *[project.name for project in resume.projects if project.evidence_quality.value == "low"]],
        ["简历弱证据追问"],
    )
    pressure = _focus(gap.high_risk_topics[:5] or gap.recommended_focus[:4], ["压力与边界场景"])
    closing = _focus([*gap.recommended_focus[:3], *gap.missing_skills[:2]], ["下一轮训练重点"])

    if interview_type == InterviewType.content_focus:
        return _fit_duration(
            duration_minutes,
            [
                ("内容理解热身", _focus([*gap.recommended_focus[:3], *gap.matched_skills[:2]], ["岗位内容理解"])),
                ("核心知识追问", jd_skills),
                ("表达结构复盘", _focus([*gap.high_risk_topics[:3], *gap.weak_evidence_skills[:2]], ["回答结构与证据"])),
                ("边界与收尾", _focus([*pressure, *closing], ["内容边界与下一轮训练"])),
            ],
        )
    if interview_type == InterviewType.role_fit:
        return _fit_duration(
            duration_minutes,
            [
                ("岗位动机与自我介绍", _focus([jd_anchor for jd_anchor in gap.recommended_focus[:2]], ["岗位匹配动机"])),
                ("经历与岗位匹配", opening),
                ("协作与边界场景", _focus([*pressure, *gap.high_risk_topics[:2]], ["协作边界与问题处理"])),
                ("短板诚实说明与收尾", closing),
            ],
        )
    if interview_type == InterviewType.project_deep_dive:
        return _fit_duration(
            duration_minutes,
            [
                ("项目背景与职责边界", opening),
                ("项目技术深挖", _focus([*project_topics, *jd_skills], ["项目实现细节"])),
                ("项目取舍与故障场景", _focus([*pressure, *gap.high_risk_topics[:3]], ["项目取舍与异常处理"])),
                ("项目证据补强收尾", _focus([*weak_evidence, *closing], ["项目证据补强"])),
            ],
        )
    if interview_type == InterviewType.group:
        return _fit_duration(
            duration_minutes,
            [
                ("群面角色定位", _focus([*gap.matched_skills[:2], *project_topics[:2]], ["观点表达与角色定位"])),
                ("观点陈述与追问", _focus([*jd_skills, *gap.recommended_focus[:3]], ["结构化表达与倾听回应"])),
                ("冲突协作场景", _focus([*pressure, *gap.high_risk_topics[:2]], ["冲突处理与团队推进"])),
                ("总结陈词与收尾", closing),
            ],
        )

    if duration_minutes <= 15:
        return [
            ("开场/项目切入", opening),
            ("JD 技能与简历弱证据追问", _focus([*jd_skills, *weak_evidence], ["JD 技能与简历证据"])),
            ("压力/边界场景追问与收尾", _focus([*pressure, *closing], ["压力边界与收尾"])),
        ]
    if duration_minutes <= 30:
        return [
            ("开场/项目切入", opening),
            ("JD 技能追问", jd_skills),
            ("简历弱证据追问", weak_evidence),
            ("压力/边界场景追问与收尾", _focus([*pressure, *closing], ["压力边界与收尾"])),
        ]
    return [
        ("开场/项目切入", opening),
        ("JD 技能追问", jd_skills[:4]),
        ("简历弱证据追问", weak_evidence),
        ("压力/边界场景追问", pressure),
        ("收尾", closing),
    ]


def _fit_duration(
    duration_minutes: int, sections: list[tuple[str, list[str]]]
) -> list[tuple[str, list[str]]]:
    if duration_minutes <= 15:
        return [
            sections[0],
            (sections[1][0], _focus([*sections[1][1], *sections[2][1]], sections[1][1])),
            (sections[-1][0], _focus([*sections[-2][1], *sections[-1][1]], sections[-1][1])),
        ]
    if duration_minutes <= 30:
        return sections[:4]
    middle = sections[:3]
    return [*middle, ("压力/边界加深", sections[-2][1]), sections[-1]]


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
        "开场/项目切入": f"从最相关项目切入，把候选人真实经历连接到目标岗位，并{depth}。",
        "JD 技能与简历弱证据追问": f"合并追问 JD 关键技能与简历弱证据，并{depth}。",
        "压力/边界场景追问与收尾": f"用压力或边界场景检验真实边界，最后沉淀下一轮训练重点，并{depth}。",
        "JD 技能追问": f"围绕 JD 关键技能追问实践深度，并{depth}。",
        "简历弱证据追问": f"针对简历中证据偏薄的技能和项目追问职责、细节与结果，并{depth}。",
        "压力/边界场景追问": f"通过模糊约束、短板说明和取舍场景进行压力测试，并{depth}。",
        "收尾": f"复盘本轮证据边界、短板补强方向和下一轮训练重点，并{depth}。",
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


def _type_label(interview_type: InterviewType) -> str:
    return {
        InterviewType.targeted_mock: "JD 定向模拟面试",
        InterviewType.content_focus: "内容理解面试",
        InterviewType.role_fit: "岗位匹配面试",
        InterviewType.project_deep_dive: "项目深挖面试",
        InterviewType.group: "群面训练",
    }[interview_type]


def _persona_label(persona: InterviewerPersona) -> str:
    return {
        InterviewerPersona.warm: "温和型 AI 面试官",
        InterviewerPersona.technical: "技术深挖型 AI 面试官",
        InterviewerPersona.pressure: "压力型 AI 面试官",
    }[persona]

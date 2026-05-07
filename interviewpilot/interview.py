"""Interview planning and question generation for the text MVP."""

from __future__ import annotations

from .models import (
    GapAnalysis,
    InterviewMessage,
    InterviewPlan,
    InterviewQuestion,
    InterviewSection,
    JDAnalysis,
    ResumeAnalysis,
)
from .text_utils import normalize_space


def create_interview_plan(
    jd: JDAnalysis,
    resume: ResumeAnalysis,
    gap: GapAnalysis,
    interview_type: str = "targeted_mock",
    difficulty: str = "medium",
    duration_minutes: int = 20,
) -> InterviewPlan:
    duration_minutes = max(10, min(duration_minutes, 45))
    focus_topics = gap.recommended_focus or jd.interview_focus or jd.required_skills or ["项目经验"]
    intro_minutes = max(3, duration_minutes // 6)
    technical_minutes = max(5, duration_minutes // 3)
    project_minutes = max(5, duration_minutes // 3)
    wrap_minutes = max(2, duration_minutes - intro_minutes - technical_minutes - project_minutes)

    sections = [
        InterviewSection(
            name="岗位匹配热身",
            duration_minutes=intro_minutes,
            goal="理解候选人如何定位目标岗位，并找到最强相关证据。",
            focus_topics=focus_topics[:2],
        ),
        InterviewSection(
            name="技术深度",
            duration_minutes=technical_minutes,
            goal="压力测试 JD 关键技能和技术取舍能力。",
            focus_topics=focus_topics[:4],
        ),
        InterviewSection(
            name="项目深挖",
            duration_minutes=project_minutes,
            goal="验证简历证据、职责边界、实现细节和结果。",
            focus_topics=[project.name for project in resume.projects[:2]] or ["最相关的简历项目"],
        ),
        InterviewSection(
            name="风险复盘",
            duration_minutes=wrap_minutes,
            goal="探索缺失或弱证据领域，并转化为下一步练习计划。",
            focus_topics=gap.high_risk_topics[:4] or focus_topics[:2],
        ),
    ]
    max_questions = max(4, min(12, duration_minutes // 3))
    return InterviewPlan(
        interview_type=interview_type,
        duration_minutes=duration_minutes,
        difficulty=difficulty,
        sections=sections,
        max_questions=max_questions,
        plan_summary=(
            f"面向 {jd.role_title} 的 {duration_minutes} 分钟候选人练习面试，"
            "优先覆盖 JD 贴合度、技术深度、项目证据和风险复盘。"
        ),
    )


def generate_next_question(
    plan: InterviewPlan,
    messages: list[InterviewMessage],
    gap: GapAnalysis,
    resume: ResumeAnalysis,
) -> InterviewQuestion:
    user_answers = [message for message in messages if message.role == "candidate"]
    current_section = _section_for_question_count(plan, len(user_answers))
    latest_answer = normalize_space(user_answers[-1].content) if user_answers else ""

    if not user_answers:
        anchor_topics = gap.matched_skills[:2] or gap.recommended_focus[:2]
        return InterviewQuestion(
            question_type="new_question",
            current_section=current_section.name,
            question=(
                "先请你讲一段简历中最能对应 "
                f"{', '.join(anchor_topics) or '目标岗位'} 的经历。"
            ),
            why_this_question="第一题先把面试锚定在真实简历证据和 JD 重点上。",
            expected_signal="岗位理解、项目选择，以及把经历连接到目标 JD 的能力。",
        )

    if _needs_follow_up(latest_answer):
        return InterviewQuestion(
            question_type="follow_up",
            current_section=current_section.name,
            question=(
                "能不能再具体一点：说明你当时做了哪个技术决策、考虑过什么取舍，以及观察到什么结果？"
            ),
            why_this_question="上一轮回答证据偏薄，还不足以支持高质量教练反馈。",
            expected_signal="具体职责、取舍 reasoning，以及可解释的项目证据。",
        )

    topic = _topic_for_section(current_section, gap, resume)
    return InterviewQuestion(
        question_type="new_question",
        current_section=current_section.name,
        question=f"我们继续深挖 {topic}。其中最难的技术问题是什么？你当时是怎么处理的？",
        why_this_question="面试需要按计划推进，同时保持和岗位风险、简历证据相关。",
        expected_signal="技术深度、结构化表达和证据质量。",
    )


def starter_questions(
    plan: InterviewPlan, gap: GapAnalysis, resume: ResumeAnalysis, count: int = 4
) -> list[InterviewQuestion]:
    messages: list[InterviewMessage] = []
    questions: list[InterviewQuestion] = []
    for index in range(count):
        question = generate_next_question(plan, messages, gap, resume)
        questions.append(question)
        messages.append(InterviewMessage(role="interviewer", content=question.question, section=question.current_section))
        messages.append(
            InterviewMessage(
                role="candidate",
                content=_placeholder_answer(index, gap, resume),
                section=question.current_section,
            )
        )
    return questions


def _section_for_question_count(plan: InterviewPlan, answered_count: int) -> InterviewSection:
    if not plan.sections:
        raise ValueError("面试计划至少需要包含一个 section。")
    section_index = min(len(plan.sections) - 1, answered_count * len(plan.sections) // max(plan.max_questions, 1))
    return plan.sections[section_index]


def _needs_follow_up(answer: str) -> bool:
    if len(answer.split()) < 28:
        return True
    lower = answer.casefold()
    has_specificity = any(marker in lower for marker in ("because", "trade-off", "result", "metric", "first", "then"))
    return not has_specificity


def _topic_for_section(section: InterviewSection, gap: GapAnalysis, resume: ResumeAnalysis) -> str:
    if section.focus_topics:
        return section.focus_topics[0]
    if gap.recommended_focus:
        return gap.recommended_focus[0]
    if resume.projects:
        return resume.projects[0].name
    return "你最相关的项目"


def _placeholder_answer(index: int, gap: GapAnalysis, resume: ResumeAnalysis) -> str:
    if index == 0 and resume.projects:
        return (
            f"我会讨论 {resume.projects[0].name}、主要实现选择，以及我从结果中复盘到的内容。"
        )
    if gap.high_risk_topics:
        return f"我需要为 {gap.high_risk_topics[0]} 准备更多细节。"
    return "我会用一个具体项目例子回答，并说明实现中的技术取舍。"

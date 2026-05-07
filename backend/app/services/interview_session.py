"""In-memory text interview session orchestration for the MVP."""

from __future__ import annotations

import re

from backend.app.schemas.common import InterviewMessageRole, InterviewQuestionType, utc_now
from backend.app.schemas.gap import GapAnalysis
from backend.app.schemas.interview import (
    InterviewControlAction,
    InterviewMessage,
    InterviewPlan,
    InterviewSessionResponse,
    InterviewSessionStartRequest,
    InterviewSessionState,
    InterviewTurnRequest,
    InterviewerOutput,
    InterviewerPrompt,
    LiveInterviewStatus,
)
from backend.app.schemas.resume import ResumeAnalysis
from backend.app.services.interviewer_prompt import INTERVIEWER_TASK, build_interviewer_prompt
from backend.app.services.json_store import get_live_interview, save_live_interview
from backend.app.services.llm_client import generate_structured_output

_SESSIONS: dict[str, InterviewSessionState] = {}
_VAGUE_MARKERS = {
    "stuff",
    "things",
    "etc",
    "handled it",
    "worked on",
    "helped with",
    "kind of",
    "basically",
    "some",
    "一些",
    "大概",
    "差不多",
    "参与",
    "帮忙",
    "做了点",
    "不太清楚",
}


def start_interview_session(request: InterviewSessionStartRequest) -> InterviewSessionResponse:
    state = InterviewSessionState(
        interview_plan=request.interview_plan,
        jd_analysis=request.jd_analysis,
        resume_analysis=request.resume_analysis,
        gap_analysis=request.gap_analysis,
    )
    output = _generate_question(state, question_type=InterviewQuestionType.new_question)
    state = _append_interviewer_output(state, output, increment_count=True)
    _SESSIONS[state.session_id] = state
    save_live_interview(state)
    return _response(state, output, latest_answer="")


def get_interview_session(session_id: str) -> InterviewSessionState | None:
    state = _SESSIONS.get(session_id)
    if state is not None:
        return state
    persisted = get_live_interview(session_id)
    if persisted is not None:
        _SESSIONS[session_id] = persisted
    return persisted


def advance_interview_session(
    session_id: str, request: InterviewTurnRequest
) -> InterviewSessionResponse | None:
    state = _SESSIONS.get(session_id)
    if state is None:
        state = get_live_interview(session_id)
        if state is not None:
            _SESSIONS[session_id] = state
    if state is None:
        return None
    if state.status == LiveInterviewStatus.completed:
        return InterviewSessionResponse(session=state)

    if request.action == InterviewControlAction.end:
        state = _append_candidate_message(state, "已结束面试。", InterviewControlAction.end)
        state.status = LiveInterviewStatus.completed
        state.updated_at = utc_now()
        _SESSIONS[session_id] = state
        save_live_interview(state)
        return InterviewSessionResponse(session=state)

    if request.action == InterviewControlAction.regenerate:
        output = _generate_question(
            state,
            question_type=InterviewQuestionType.new_question,
            latest_answer="",
            regenerate=True,
        )
        state = _replace_latest_interviewer_output(state, output)
        state.last_action = InterviewControlAction.regenerate
        state.updated_at = utc_now()
        _SESSIONS[session_id] = state
        save_live_interview(state)
        return _response(state, output, latest_answer="")

    if request.action == InterviewControlAction.skip:
        state = _append_candidate_message(state, "已跳过当前问题。", InterviewControlAction.skip)
        return _move_to_next_question(session_id, state, latest_answer="")

    if request.action == InterviewControlAction.next:
        state = _append_candidate_message(
            state, "已请求进入下一题。", InterviewControlAction.next
        )
        return _move_to_next_question(session_id, state, latest_answer="")

    answer = (request.answer or "").strip()
    if not answer:
        answer = "未提供有效回答。"
    state = _append_candidate_message(state, answer, InterviewControlAction.answer)
    if _should_follow_up(answer):
        output = _generate_question(
            state,
            question_type=InterviewQuestionType.follow_up,
            latest_answer=answer,
        )
        state = _append_interviewer_output(state, output, increment_count=True)
        _SESSIONS[session_id] = state
        save_live_interview(state)
        return _response(state, output, latest_answer=answer)
    return _move_to_next_question(session_id, state, latest_answer=answer)


def _move_to_next_question(
    session_id: str, state: InterviewSessionState, latest_answer: str
) -> InterviewSessionResponse:
    if state.current_question_count >= state.interview_plan.max_questions:
        state.status = LiveInterviewStatus.completed
        state.updated_at = utc_now()
        _SESSIONS[session_id] = state
        save_live_interview(state)
        return InterviewSessionResponse(session=state)

    state.current_section_index = _section_index_for_question(
        state.current_question_count + 1, state.interview_plan
    )
    output = _generate_question(
        state,
        question_type=InterviewQuestionType.new_question,
        latest_answer=latest_answer,
    )
    state = _append_interviewer_output(state, output, increment_count=True)
    _SESSIONS[session_id] = state
    save_live_interview(state)
    return _response(state, output, latest_answer=latest_answer)


def _response(
    state: InterviewSessionState, output: InterviewerOutput, latest_answer: str
) -> InterviewSessionResponse:
    section_name, _ = _current_section(state)
    prompt = InterviewerPrompt(
        task=INTERVIEWER_TASK,
        prompt=build_interviewer_prompt(
            state.interview_plan,
            section_name,
            state.messages,
            latest_answer,
            state.gap_analysis,
            state.resume_analysis,
        ),
    )
    return InterviewSessionResponse(
        session=state,
        interviewer_output=output,
        interviewer_prompt=prompt,
    )


def _append_interviewer_output(
    state: InterviewSessionState, output: InterviewerOutput, increment_count: bool
) -> InterviewSessionState:
    state.messages.append(
        InterviewMessage(
            role=InterviewMessageRole.interviewer,
            content=output.question,
            section=output.current_section,
        )
    )
    if increment_count:
        state.current_question_count += 1
    state.latest_question = output
    state.updated_at = utc_now()
    return state


def _replace_latest_interviewer_output(
    state: InterviewSessionState, output: InterviewerOutput
) -> InterviewSessionState:
    if state.messages and state.messages[-1].role == InterviewMessageRole.interviewer:
        state.messages[-1] = InterviewMessage(
            role=InterviewMessageRole.interviewer,
            content=output.question,
            section=output.current_section,
        )
    else:
        state.messages.append(
            InterviewMessage(
                role=InterviewMessageRole.interviewer,
                content=output.question,
                section=output.current_section,
            )
        )
    state.latest_question = output
    state.updated_at = utc_now()
    return state


def _append_candidate_message(
    state: InterviewSessionState, content: str, action: InterviewControlAction
) -> InterviewSessionState:
    state.messages.append(
        InterviewMessage(
            role=InterviewMessageRole.candidate,
            content=content,
            section=state.latest_question.current_section if state.latest_question else None,
        )
    )
    state.last_action = action
    state.updated_at = utc_now()
    return state


def _generate_question(
    state: InterviewSessionState,
    question_type: InterviewQuestionType,
    latest_answer: str = "",
    regenerate: bool = False,
) -> InterviewerOutput:
    section_name, focus_topics = _current_section(state)
    prompt_text = build_interviewer_prompt(
        state.interview_plan,
        section_name,
        state.messages,
        latest_answer,
        state.gap_analysis,
        state.resume_analysis,
    )
    llm_output = generate_structured_output(prompt_text, InterviewerOutput)
    if llm_output is not None:
        return llm_output

    topic = _topic_for_turn(state, focus_topics, latest_answer)
    project = _project_anchor(state.resume_analysis)
    jd_anchor = _jd_anchor(state)
    risk_anchor = _risk_anchor(state.gap_analysis)

    if question_type == InterviewQuestionType.follow_up:
        snippet = _answer_snippet(latest_answer)
        question = (
            f"你刚才提到{snippet}。能不能把它落到 {topic} 上，具体说明你的职责、"
            "当时做的技术选择，以及结果或取舍？"
        )
        why = (
            "上一轮回答偏短、偏模糊或证据不足，所以这次追问继续留在同一环节，要求补充具体证据。"
        )
        signal = "明确职责、实现细节、技术取舍和真实证据。"
    elif regenerate:
        question = (
            f"我们换一个角度看 {topic}。结合 {jd_anchor}，你在 {project} 中做过的哪一个决策"
            "最能证明你适合当前面试环节？"
        )
        why = "用户请求重生成问题；当前环节和题数不变。"
        signal = "更清晰地连接 JD、简历证据和当前环节目标的例子。"
    else:
        question = _new_question_text(section_name, topic, project, jd_anchor, risk_anchor)
        why = (
            f"这个问题对应“{section_name}”，把 JD 重点和简历证据连接起来，同时推进面试计划。"
        )
        signal = "相关例子、技术深度、约束、取舍，以及对真实短板的诚实说明。"

    return InterviewerOutput(
        question_type=question_type,
        current_section=section_name,
        question=question,
        why_this_question=why,
        expected_signal=signal,
    )


def _new_question_text(
    section_name: str, topic: str, project: str, jd_anchor: str, risk_anchor: str
) -> str:
    section_key = section_name.casefold()
    if "warm" in section_key or "fit" in section_key or "匹配" in section_name or "热身" in section_name:
        return (
            f"针对 {jd_anchor} 这个目标岗位，你在 {project} 中哪段经历最能对应 {topic}？"
            "你希望面试官理解你在里面的哪部分贡献？"
        )
    if "project" in section_key or "项目" in section_name:
        return (
            f"我们深挖一下 {project}。你当时如何使用或思考 {topic}？"
            "哪个技术约束影响了你的实现方案？"
        )
    if "trade" in section_key or "system" in section_key or "取舍" in section_name or "系统" in section_name:
        return (
            f"假设 {topic} 在 {jd_anchor} 岗位里变成瓶颈，你会考虑什么设计取舍？"
            f"你在 {project} 中的经验会如何影响这个判断？"
        )
    if "risk" in section_key or "风险" in section_name:
        return (
            f"当前主要风险点是：{risk_anchor}。针对 {topic}，你有什么真实动手证据？"
            "如果证据不足，真实面试前你需要补齐哪一块？"
        )
    return (
        f"JD 强调 {topic}。请用 {project} 里的一个具体例子说明你的实践深度，"
        "包括你做过的决策以及为什么这么做。"
    )


def _should_follow_up(answer: str) -> bool:
    clean = answer.strip()
    if clean in {"No substantive answer provided.", "未提供有效回答。"}:
        return True
    words = re.findall(r"[A-Za-z0-9+#.-]+|[\u4e00-\u9fff]", clean)
    if len(words) < 28 and len(clean) < 80:
        return True
    lowered = clean.casefold()
    if any(marker in lowered for marker in _VAGUE_MARKERS):
        return True
    has_specific_signal = bool(
        re.search(r"\d|because|trade[- ]?off|latency|schema|api|database|cache|test|因为|取舍|延迟|接口|数据库|缓存|测试", lowered)
    )
    return not has_specific_signal


def _current_section(state: InterviewSessionState) -> tuple[str, list[str]]:
    if not state.interview_plan.sections:
        return "通用面试", ["岗位贴合度"]
    index = min(state.current_section_index, len(state.interview_plan.sections) - 1)
    section = state.interview_plan.sections[index]
    return section.name, section.focus_topics or ["岗位贴合度"]


def _section_index_for_question(question_number: int, plan: InterviewPlan) -> int:
    if not plan.sections:
        return 0
    index = (max(1, question_number) - 1) * len(plan.sections) // max(1, plan.max_questions)
    return min(len(plan.sections) - 1, index)


def _topic_for_turn(
    state: InterviewSessionState, focus_topics: list[str], latest_answer: str
) -> str:
    if latest_answer:
        answer_lower = latest_answer.casefold()
        for topic in focus_topics:
            if topic.casefold() in answer_lower:
                return topic
    index = max(0, state.current_question_count) % max(1, len(focus_topics))
    return focus_topics[index]


def _project_anchor(resume: ResumeAnalysis) -> str:
    if resume.projects:
        return resume.projects[0].name
    if resume.strengths:
        return resume.strengths[0]
    return "你最相关的简历项目"


def _jd_anchor(state: InterviewSessionState) -> str:
    role = state.jd_analysis.role_title
    required = state.jd_analysis.required_skills[:2]
    if required:
        return f"{role} ({', '.join(required)})"
    return role


def _risk_anchor(gap: GapAnalysis) -> str:
    for items in (gap.high_risk_topics, gap.weak_evidence_skills, gap.missing_skills, gap.recommended_focus):
        if items:
            return items[0]
    return "证据最薄弱的领域"


def _answer_snippet(answer: str) -> str:
    clean = " ".join(answer.strip().split())
    if not clean or clean in {"No substantive answer provided.", "未提供有效回答。"}:
        return "你需要更多时间，或还没有提供细节"
    if len(clean) > 90:
        clean = clean[:87].rstrip() + "..."
    return f"“{clean}”"

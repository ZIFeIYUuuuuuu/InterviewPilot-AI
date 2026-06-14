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
    InterviewerPersona,
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
    state_kwargs = {
        "interview_plan": request.interview_plan,
        "jd_analysis": request.jd_analysis,
        "resume_analysis": request.resume_analysis,
        "gap_analysis": request.gap_analysis,
        "voice_provider": request.voice_provider,
    }
    if request.session_id:
        state_kwargs["session_id"] = request.session_id
    state = InterviewSessionState(**state_kwargs)
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
            _persona_opening(state.interview_plan.interviewer_persona, "follow_up")
            + " "
            + f"你刚才提到{snippet}。请把它落到 {topic} 上，具体说明你的职责、"
            + _persona_detail_prompt(state.interview_plan.interviewer_persona)
        )
        why = (
            f"上一轮回答偏短、偏模糊或证据不足，所以这次追问继续留在当前环节“{section_name}”，要求补充具体证据。"
        )
        signal = "明确职责、实现细节、技术取舍和真实证据。"
    elif regenerate:
        question = (
            _persona_opening(state.interview_plan.interviewer_persona, "regenerate")
            + " "
            + f"换一个角度看 {topic}。结合 {jd_anchor}，你在 {project} 中做过的哪一个决策"
            + _persona_regenerate_tail(state.interview_plan.interviewer_persona)
        )
        why = "用户请求重生成问题；当前环节和题数不变。"
        signal = "更清晰地连接 JD、简历证据和当前环节目标的例子。"
    else:
        question = _apply_persona_tone(
            state.interview_plan.interviewer_persona,
            _new_question_text(
                state.interview_plan.interview_type,
                section_name,
                topic,
                project,
                jd_anchor,
                risk_anchor,
            ),
            section_name,
        )
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
    interview_type: object, section_name: str, topic: str, project: str, jd_anchor: str, risk_anchor: str
) -> str:
    section_key = section_name.casefold()
    type_value = getattr(interview_type, "value", str(interview_type))
    if type_value == "content_focus":
        return (
            f"请围绕 {topic} 解释你的理解：它解决什么问题、常见误区是什么，"
            f"以及你会如何把这个知识点应用到 {jd_anchor} 的真实工作场景里？"
        )
    if type_value == "role_fit":
        return (
            f"从岗位匹配角度看，{jd_anchor} 需要的不只是技术点。请用 {project} 说明"
            f"你在 {topic} 相关场景里的职责、协作方式和真实边界。"
        )
    if type_value == "project_deep_dive":
        return (
            f"我们只深挖 {project}。围绕 {topic}，请讲清背景、你具体负责的决策、"
            "当时的约束、怎么验证，以及如果重做你会改哪里。"
        )
    if type_value == "group":
        return (
            f"模拟群面场景：如果小组围绕 {topic} 有两种不同方案，你会先提出什么观点，"
            "如何回应反对意见，并把讨论收束成可执行结论？"
        )
    if "warm" in section_key or "fit" in section_key or "匹配" in section_name or "热身" in section_name:
        return (
            f"针对 {jd_anchor} 这个目标岗位，你在 {project} 中哪段经历最能对应 {topic}？"
            "你希望面试官理解你在里面的哪部分贡献？"
        )
    if "开场" in section_name or "切入" in section_name:
        return (
            f"我们先从 {project} 切入。面向 {jd_anchor}，这段经历和 {topic} 的连接点是什么？"
            "请先讲背景、你的职责，以及你希望后面被深挖的一个技术点。"
        )
    if "jd" in section_key or "技能" in section_name:
        return (
            f"JD 里强调 {topic}。请结合 {project} 说明你是否真实做过相关实践，"
            "如果做过，请讲实现细节；如果证据不足，请说明真实边界。"
        )
    if "弱证据" in section_name:
        return (
            f"简历里 {topic} 的证据还不够厚。你能用 {project} 中的一个具体动作说明"
            "你实际负责了什么、怎么验证效果，以及哪些部分不是你做的吗？"
        )
    if "压力" in section_name or "边界" in section_name:
        return (
            f"做一个压力场景：如果面试官围绕“{risk_anchor}”继续追问，"
            f"而你在 {topic} 上证据有限，你会如何诚实说明边界，并给出可执行的补强计划？"
        )
    if "收尾" in section_name:
        return (
            f"最后收束一下：基于 {jd_anchor} 和本轮关于 {topic} 的追问，"
            "你认为真实面试前最需要补强哪一块？准备用什么具体练习补齐？"
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


def _apply_persona_tone(persona: InterviewerPersona, question: str, section_name: str) -> str:
    if persona == InterviewerPersona.warm:
        return f"我们慢慢来，先看“{section_name}”。{question} 不确定的地方也可以直接说明真实边界。"
    if persona == InterviewerPersona.pressure:
        return f"我会追得更细一点：{question} 请避免泛泛而谈，重点说清证据、边界和取舍。"
    return f"从技术细节看，{question}"


def _persona_opening(persona: InterviewerPersona, mode: str) -> str:
    if persona == InterviewerPersona.warm:
        return "这个回答可以继续补充一点。"
    if persona == InterviewerPersona.pressure:
        return "这里我需要更具体的证据。"
    if mode == "regenerate":
        return "我们切到实现细节。"
    return "我继续追问技术细节。"


def _persona_detail_prompt(persona: InterviewerPersona) -> str:
    if persona == InterviewerPersona.warm:
        return "当时做的技术选择、遇到的限制，以及你能确认的真实结果。"
    if persona == InterviewerPersona.pressure:
        return "当时做的技术选择、失败边界、替代方案，以及哪些结果不能归因到你身上。"
    return "当时做的技术选择，以及结果或取舍。"


def _persona_regenerate_tail(persona: InterviewerPersona) -> str:
    if persona == InterviewerPersona.warm:
        return "最能体现你的真实贡献？可以按背景、行动、结果来讲。"
    if persona == InterviewerPersona.pressure:
        return "经得起继续追问？请先说结论，再说明证据边界。"
    return "最能支撑当前面试环节？"


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

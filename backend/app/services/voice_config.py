"""Voice provider configuration with safe local fallback metadata."""

from __future__ import annotations

import os

from backend.app.schemas.interview import (
    InterviewerPersona,
    InterviewVoiceConfigResponse,
    VoiceProvider,
    VoicePersonaProfile,
    VoiceProviderStatus,
)


def get_voice_config() -> InterviewVoiceConfigResponse:
    """Return provider readiness without exposing API key values."""

    default_provider = _provider_from_env(os.getenv("INTERVIEWPILOT_VOICE_PROVIDER", "browser"))
    aliyun_model = os.getenv("INTERVIEWPILOT_ALIYUN_VOICE_MODEL", "cosyvoice-v3-flash").strip()
    warm_voice = os.getenv("INTERVIEWPILOT_ALIYUN_WARM_VOICE_ID", "longanxuan_v3").strip()
    technical_voice = os.getenv("INTERVIEWPILOT_ALIYUN_TECHNICAL_VOICE_ID", "longshuo_v3").strip()
    pressure_voice = os.getenv("INTERVIEWPILOT_ALIYUN_PRESSURE_VOICE_ID", "longfei_v3").strip()
    return InterviewVoiceConfigResponse(
        default_provider=default_provider,
        browser_fallback_available=True,
        providers=[
            VoiceProviderStatus(
                provider=VoiceProvider.browser,
                display_name="浏览器本地语音",
                configured=True,
                enabled=True,
                required_env_vars=[],
                note="使用浏览器 SpeechRecognition 和 speechSynthesis；不可用时自动回到文字面试。",
            ),
            VoiceProviderStatus(
                provider=VoiceProvider.aliyun,
                display_name="阿里云百炼语音合成",
                configured=_has_any(
                    "INTERVIEWPILOT_ALIYUN_VOICE_API_KEY",
                    "DASHSCOPE_API_KEY",
                    "INTERVIEWPILOT_LLM_API_KEY",
                    "ALIYUN_VOICE_API_KEY",
                ),
                enabled=default_provider == VoiceProvider.aliyun,
                required_env_vars=[
                    "INTERVIEWPILOT_ALIYUN_VOICE_API_KEY 或 DASHSCOPE_API_KEY 或 INTERVIEWPILOT_LLM_API_KEY",
                    "INTERVIEWPILOT_ALIYUN_VOICE_MODEL",
                    "INTERVIEWPILOT_ALIYUN_VOICE_ID",
                ],
                model=aliyun_model,
                voice_id=technical_voice,
                note=(
                    "默认使用阿里内置音色 longshuo_v3（龙硕/博才干练男）作为技术面试官。"
                    "未配置或调用失败时不影响文字面试和浏览器语音兜底。"
                ),
            ),
            VoiceProviderStatus(
                provider=VoiceProvider.doubao,
                display_name="豆包语音大模型预留",
                configured=_has_any("INTERVIEWPILOT_DOUBAO_VOICE_API_KEY", "DOUBAO_VOICE_API_KEY"),
                enabled=default_provider == VoiceProvider.doubao,
                required_env_vars=[
                    "INTERVIEWPILOT_DOUBAO_VOICE_API_KEY",
                    "INTERVIEWPILOT_DOUBAO_VOICE_APP_ID",
                ],
                note="已预留后端配置位；未配置或调用失败时不影响文字面试和浏览器语音兜底。",
            ),
        ],
        persona_profiles=[
            VoicePersonaProfile(
                persona=InterviewerPersona.warm,
                display_name="温柔面试官",
                model=aliyun_model,
                voice_id=warm_voice,
                speech_rate=1.0,
                note="使用龙安宣/经典直播女，适合温和、耐心的追问。",
            ),
            VoicePersonaProfile(
                persona=InterviewerPersona.technical,
                display_name="技术面试官",
                model=aliyun_model,
                voice_id=technical_voice,
                speech_rate=1.1,
                note="使用龙硕/博才干练男，适合清晰、专业、偏技术深挖的追问。",
            ),
            VoicePersonaProfile(
                persona=InterviewerPersona.pressure,
                display_name="压力面试官",
                model=aliyun_model,
                voice_id=pressure_voice,
                speech_rate=1.0,
                note="使用龙飞/热血磁性男，适合更严厉、直接但保持尊重的压力追问。",
            ),
        ],
        privacy_or_boundary_note=(
            "语音模式只用于候选人练习；实时阶段不展示评分，不做外部结果判断。"
            "密钥仅从环境变量读取，接口不会返回密钥明文。"
        ),
    )


def _provider_from_env(value: str) -> VoiceProvider:
    try:
        return VoiceProvider(value.strip().casefold())
    except ValueError:
        return VoiceProvider.browser


def _has_any(*names: str) -> bool:
    return any(os.getenv(name, "").strip() for name in names)

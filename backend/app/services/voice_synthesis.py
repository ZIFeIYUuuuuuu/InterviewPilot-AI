"""Cloud voice synthesis with deterministic browser-fallback metadata."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from time import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.app.schemas.interview import (
    InterviewerPersona,
    VoiceProvider,
    VoiceSynthesisRequest,
    VoiceSynthesisResponse,
)

ALIYUN_TTS_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"


@dataclass(frozen=True)
class PersonaVoiceSettings:
    voice_id: str
    rate: float
    pitch: float


def synthesize_voice(request: VoiceSynthesisRequest) -> VoiceSynthesisResponse:
    """Synthesize interview text when possible; otherwise return a safe fallback response."""

    if request.provider != VoiceProvider.aliyun:
        return _fallback_response(
            request,
            message="当前云语音提供方尚未接入真实合成，已切回浏览器本地朗读兜底。",
        )

    api_key = _first_env(
        "INTERVIEWPILOT_ALIYUN_VOICE_API_KEY",
        "DASHSCOPE_API_KEY",
        "INTERVIEWPILOT_LLM_API_KEY",
        "ALIYUN_VOICE_API_KEY",
    )
    if not api_key:
        return _fallback_response(
            request,
            message="未检测到阿里云 DashScope API Key，已切回浏览器本地朗读兜底。",
        )

    model = os.getenv("INTERVIEWPILOT_ALIYUN_VOICE_MODEL", "cosyvoice-v3-flash").strip()
    settings = _settings_for_persona(request.persona)
    payload = {
        "model": model,
        "input": {
            "text": request.text.strip(),
            "voice": settings.voice_id,
        },
        "parameters": {
            "format": request.audio_format,
            "sample_rate": request.sample_rate,
            "rate": settings.rate,
            "pitch": settings.pitch,
        },
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "disable",
    }

    try:
        response_payload = _post_json(ALIYUN_TTS_ENDPOINT, payload, headers)
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return _fallback_response(
            request,
            model=model,
            voice_id=settings.voice_id,
            message="阿里云语音合成暂时失败，已切回浏览器本地朗读兜底。",
        )

    output = response_payload.get("output") if isinstance(response_payload, dict) else None
    audio = output.get("audio") if isinstance(output, dict) else None
    audio_url = audio.get("url") if isinstance(audio, dict) else None
    audio_base64 = audio.get("data") if isinstance(audio, dict) else None
    if not audio_url and not audio_base64:
        return _fallback_response(
            request,
            model=model,
            voice_id=settings.voice_id,
            message="阿里云语音返回中没有可播放音频，已切回浏览器本地朗读兜底。",
        )

    return VoiceSynthesisResponse(
        provider=VoiceProvider.aliyun,
        persona=request.persona,
        model=model,
        voice_id=settings.voice_id,
        audio_url=audio_url,
        audio_base64=audio_base64,
        audio_format=request.audio_format,
        sample_rate=request.sample_rate,
        used_fallback=False,
        message="已使用阿里云百炼语音合成面试官问题。",
        request_id=_string_or_none(response_payload.get("request_id")),
        expires_at=_expires_at(output),
    )


def _post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, headers=headers, method="POST")
    timeout = float(os.getenv("INTERVIEWPILOT_ALIYUN_VOICE_TIMEOUT_SECONDS", "12"))
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _settings_for_persona(persona: InterviewerPersona) -> PersonaVoiceSettings:
    if persona == InterviewerPersona.warm:
        return PersonaVoiceSettings(
            voice_id=os.getenv("INTERVIEWPILOT_ALIYUN_WARM_VOICE_ID", "longanxuan_v3").strip(),
            rate=0.92,
            pitch=1.04,
        )
    if persona == InterviewerPersona.pressure:
        return PersonaVoiceSettings(
            voice_id=os.getenv("INTERVIEWPILOT_ALIYUN_PRESSURE_VOICE_ID", "longfei_v3").strip(),
            rate=1.12,
            pitch=0.92,
        )
    return PersonaVoiceSettings(
        voice_id=os.getenv("INTERVIEWPILOT_ALIYUN_TECHNICAL_VOICE_ID", "longshuo_v3").strip(),
        rate=1.04,
        pitch=0.98,
    )


def _fallback_response(
    request: VoiceSynthesisRequest,
    message: str,
    model: str | None = None,
    voice_id: str | None = None,
) -> VoiceSynthesisResponse:
    settings = _settings_for_persona(request.persona)
    return VoiceSynthesisResponse(
        provider=request.provider,
        persona=request.persona,
        model=model or os.getenv("INTERVIEWPILOT_ALIYUN_VOICE_MODEL", "cosyvoice-v3-flash").strip(),
        voice_id=voice_id or settings.voice_id,
        audio_url=None,
        audio_base64=None,
        audio_format=request.audio_format,
        sample_rate=request.sample_rate,
        used_fallback=True,
        message=message,
    )


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _string_or_none(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _expires_at(output: object) -> int | None:
    if isinstance(output, dict) and isinstance(output.get("expires_at"), int):
        return output["expires_at"]
    # DashScope non-streaming audio URLs are documented as temporary; expose a rough UI hint.
    return int(time()) + 24 * 60 * 60

"""Best-effort JD text extraction with graceful fallbacks."""

from __future__ import annotations

import base64
import re

from backend.app.schemas.jd import JDExtractionResult, JDExtractionStatus, JDInputRequest, JDInputType


def extract_jd_text(request: JDInputRequest) -> JDExtractionResult:
    if request.input_type == JDInputType.text:
        return _extract_text_input(request)
    if request.input_type == JDInputType.pdf:
        return _extract_pdf_input(request)
    if request.input_type == JDInputType.image:
        return _extract_image_input(request)
    return JDExtractionResult(
        input_type=request.input_type,
        status=JDExtractionStatus.manual_required,
        warnings=["暂不支持该 JD 输入类型；请手动粘贴 JD 文本。"],
        needs_manual_correction=True,
    )


def _extract_text_input(request: JDInputRequest) -> JDExtractionResult:
    text = (request.text or "").strip()
    if not text:
        return JDExtractionResult(
            input_type=JDInputType.text,
            status=JDExtractionStatus.manual_required,
            warnings=["JD 文本为空；请手动粘贴 JD 后继续。"],
            needs_manual_correction=True,
        )
    return JDExtractionResult(
        input_type=JDInputType.text,
        raw_text=text,
        status=JDExtractionStatus.extracted,
        warnings=_quality_warnings(text),
        needs_manual_correction=_is_low_quality(text),
    )


def _extract_pdf_input(request: JDInputRequest) -> JDExtractionResult:
    warnings: list[str] = []
    manual_text = (request.text or "").strip()
    if not request.content_base64 and manual_text:
        warnings.append("已使用 PDF 输入中提供的文本作为降级内容。")
        return JDExtractionResult(
            input_type=JDInputType.pdf,
            raw_text=manual_text,
            status=JDExtractionStatus.partial,
            warnings=warnings + _quality_warnings(manual_text),
            needs_manual_correction=_is_low_quality(manual_text),
        )
    if not request.content_base64:
        return JDExtractionResult(
            input_type=JDInputType.pdf,
            status=JDExtractionStatus.manual_required,
            warnings=["未提供 PDF 内容；请手动粘贴提取后的 JD 文本。"],
            needs_manual_correction=True,
        )

    try:
        data = base64.b64decode(request.content_base64, validate=True)
    except Exception:
        if manual_text:
            return JDExtractionResult(
                input_type=JDInputType.pdf,
                raw_text=manual_text,
                status=JDExtractionStatus.partial,
                warnings=["PDF 内容不是有效 base64；已改用手动文本兜底。", *_quality_warnings(manual_text)],
                needs_manual_correction=True,
            )
        return JDExtractionResult(
            input_type=JDInputType.pdf,
            status=JDExtractionStatus.failed,
            warnings=["PDF 内容不是有效 base64；请手动粘贴 JD 文本。"],
            needs_manual_correction=True,
        )

    extracted, extraction_warnings = extract_pdf_bytes(data)
    warnings.extend(extraction_warnings)
    if not extracted.strip():
        if manual_text:
            return JDExtractionResult(
                input_type=JDInputType.pdf,
                raw_text=manual_text,
                status=JDExtractionStatus.partial,
                warnings=warnings + ["PDF 文本提取没有得到可用内容；已改用手动文本兜底。", *_quality_warnings(manual_text)],
                needs_manual_correction=True,
            )
        return JDExtractionResult(
            input_type=JDInputType.pdf,
            status=JDExtractionStatus.manual_required,
            warnings=warnings + ["PDF 文本提取没有得到可用内容；请手动粘贴 JD 文本。"],
            needs_manual_correction=True,
        )

    return JDExtractionResult(
        input_type=JDInputType.pdf,
        raw_text=extracted.strip(),
        status=JDExtractionStatus.partial if warnings else JDExtractionStatus.extracted,
        warnings=warnings + _quality_warnings(extracted),
        needs_manual_correction=True if warnings else _is_low_quality(extracted),
    )


def _extract_image_input(request: JDInputRequest) -> JDExtractionResult:
    manual_text = (request.text or "").strip()
    if manual_text:
        return JDExtractionResult(
            input_type=JDInputType.image,
            raw_text=manual_text,
            status=JDExtractionStatus.partial,
            warnings=["当前暂未接入 OCR；已使用图片输入中提供的文本作为降级内容。"],
            needs_manual_correction=_is_low_quality(manual_text),
        )
    return JDExtractionResult(
        input_type=JDInputType.image,
        status=JDExtractionStatus.manual_required,
        warnings=["当前 MVP 暂未接入图片 OCR；请手动粘贴 JD 文本。"],
        needs_manual_correction=True,
    )


def extract_pdf_bytes(data: bytes) -> tuple[str, list[str]]:
    try:
        from pypdf import PdfReader  # type: ignore
        from io import BytesIO

        reader = PdfReader(BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text, []
    except ModuleNotFoundError:
        return _fallback_pdf_text_scan(data), ["未安装 pypdf；已使用低保真 PDF 字节扫描降级提取。"]
    except Exception as exc:
        return _fallback_pdf_text_scan(data), [f"PDF 解析失败（{exc}）；已使用低保真 PDF 字节扫描降级提取。"]


def _fallback_pdf_text_scan(data: bytes) -> str:
    decoded = data.decode("latin-1", errors="ignore")
    chunks = re.findall(r"\(([^()\r\n]{3,})\)", decoded)
    return "\n".join(_clean_pdf_chunk(chunk) for chunk in chunks if _clean_pdf_chunk(chunk))


def _clean_pdf_chunk(chunk: str) -> str:
    return re.sub(r"\s+", " ", chunk.replace("\\(", "(").replace("\\)", ")")).strip()


def _quality_warnings(text: str) -> list[str]:
    warnings = []
    if _is_low_quality(text):
        warnings.append("JD 文本较短或细节不足；继续前建议复查并修正。")
    if len(text.splitlines()) <= 1 and len(text.split()) < 30:
        warnings.append("JD 结构较少；必需/加分项划分可能不稳定。")
    return warnings


def _is_low_quality(text: str) -> bool:
    words = re.findall(r"\w+", text or "")
    return len(words) < 12

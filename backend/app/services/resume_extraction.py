"""Best-effort resume text extraction with manual fallback."""

from __future__ import annotations

import base64
import re

from backend.app.schemas.resume import (
    ResumeExtractionResult,
    ResumeExtractionStatus,
    ResumeInputRequest,
    ResumeInputType,
)
from backend.app.services.jd_extraction import extract_pdf_bytes


def extract_resume_text(request: ResumeInputRequest) -> ResumeExtractionResult:
    if request.input_type == ResumeInputType.text:
        return _extract_text_input(request)
    if request.input_type == ResumeInputType.pdf:
        return _extract_pdf_input(request)
    if request.input_type == ResumeInputType.image:
        return _extract_image_input(request)
    return ResumeExtractionResult(
        input_type=request.input_type,
        status=ResumeExtractionStatus.manual_required,
        warnings=["暂不支持该简历输入类型；请手动粘贴简历文本。"],
        needs_manual_correction=True,
    )


def _extract_text_input(request: ResumeInputRequest) -> ResumeExtractionResult:
    text = (request.text or "").strip()
    if not text:
        return ResumeExtractionResult(
            input_type=ResumeInputType.text,
            status=ResumeExtractionStatus.manual_required,
            warnings=["简历文本为空；请手动粘贴简历内容后继续。"],
            needs_manual_correction=True,
        )
    return ResumeExtractionResult(
        input_type=ResumeInputType.text,
        raw_text=text,
        status=ResumeExtractionStatus.extracted,
        warnings=_quality_warnings(text),
        needs_manual_correction=_is_low_quality(text),
    )


def _extract_pdf_input(request: ResumeInputRequest) -> ResumeExtractionResult:
    manual_text = (request.text or "").strip()
    if not request.content_base64 and manual_text:
        return ResumeExtractionResult(
            input_type=ResumeInputType.pdf,
            raw_text=manual_text,
            status=ResumeExtractionStatus.partial,
            warnings=["已使用 PDF 简历输入中提供的文本作为降级内容。", *_quality_warnings(manual_text)],
            needs_manual_correction=_is_low_quality(manual_text),
        )
    if request.content_base64:
        try:
            data = base64.b64decode(request.content_base64, validate=True)
        except Exception:
            if manual_text:
                return ResumeExtractionResult(
                    input_type=ResumeInputType.pdf,
                    raw_text=manual_text,
                    status=ResumeExtractionStatus.partial,
                    warnings=["PDF 内容不是有效 base64；已改用手动文本兜底。", *_quality_warnings(manual_text)],
                    needs_manual_correction=True,
                )
            return ResumeExtractionResult(
                input_type=ResumeInputType.pdf,
                status=ResumeExtractionStatus.failed,
                warnings=["PDF 内容不是有效 base64；请手动粘贴简历文本。"],
                needs_manual_correction=True,
            )

        extracted, extraction_warnings = extract_pdf_bytes(data)
        if extracted.strip():
            return ResumeExtractionResult(
                input_type=ResumeInputType.pdf,
                raw_text=extracted.strip(),
                status=ResumeExtractionStatus.partial if extraction_warnings else ResumeExtractionStatus.extracted,
                warnings=extraction_warnings + _quality_warnings(extracted),
                needs_manual_correction=True if extraction_warnings else _is_low_quality(extracted),
            )
        if manual_text:
            return ResumeExtractionResult(
                input_type=ResumeInputType.pdf,
                raw_text=manual_text,
                status=ResumeExtractionStatus.partial,
                warnings=[
                    *extraction_warnings,
                    "PDF 文本提取没有得到可用内容；已改用手动文本兜底。",
                    *_quality_warnings(manual_text),
                ],
                needs_manual_correction=True,
            )
        return ResumeExtractionResult(
            input_type=ResumeInputType.pdf,
            status=ResumeExtractionStatus.manual_required,
            warnings=[*extraction_warnings, "PDF 文本提取没有得到可用内容；请手动粘贴简历文本。"],
            needs_manual_correction=True,
        )
    return ResumeExtractionResult(
        input_type=ResumeInputType.pdf,
        status=ResumeExtractionStatus.manual_required,
        warnings=[
            "未提供 PDF 文件内容；请上传 PDF 或手动粘贴简历文本。"
        ],
        needs_manual_correction=True,
    )


def _extract_image_input(request: ResumeInputRequest) -> ResumeExtractionResult:
    manual_text = (request.text or "").strip()
    if manual_text:
        return ResumeExtractionResult(
            input_type=ResumeInputType.image,
            raw_text=manual_text,
            status=ResumeExtractionStatus.partial,
            warnings=["当前暂未接入简历图片 OCR；已使用图片输入中提供的文本作为降级内容。", *_quality_warnings(manual_text)],
            needs_manual_correction=_is_low_quality(manual_text),
        )
    return ResumeExtractionResult(
        input_type=ResumeInputType.image,
        status=ResumeExtractionStatus.manual_required,
        warnings=["当前 MVP 暂未接入简历图片 OCR；请手动粘贴简历文本。"],
        needs_manual_correction=True,
    )


def _quality_warnings(text: str) -> list[str]:
    warnings = []
    if _is_low_quality(text):
        warnings.append("简历文本较短或细节不足；系统会保守分析。")
    if not re.search(r"project|experience|skills|项目|经历|技能", text, re.I):
        warnings.append("简历结构不够清晰；项目和技能可能需要手动修正。")
    return warnings


def _is_low_quality(text: str) -> bool:
    words = re.findall(r"\w+", text or "")
    return len(words) < 18

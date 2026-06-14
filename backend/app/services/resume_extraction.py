"""Best-effort resume text extraction with manual fallback."""

from __future__ import annotations

import base64
from io import BytesIO
import re
import zipfile
from xml.etree import ElementTree

from backend.app.schemas.resume import (
    ResumeExtractionResult,
    ResumeExtractionStatus,
    ResumeInputRequest,
    ResumeInputType,
)
from backend.app.services.jd_extraction import extract_pdf_bytes
from backend.app.services.ocr import extract_pdf_ocr_text


def extract_resume_text(request: ResumeInputRequest) -> ResumeExtractionResult:
    if request.input_type == ResumeInputType.text:
        return _extract_text_input(request)
    if request.input_type == ResumeInputType.pdf:
        return _extract_pdf_input(request)
    if request.input_type == ResumeInputType.docx:
        return _extract_docx_input(request)
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
        ocr_text, ocr_warnings = extract_pdf_ocr_text(data, "简历")
        if ocr_text.strip():
            return ResumeExtractionResult(
                input_type=ResumeInputType.pdf,
                raw_text=ocr_text.strip(),
                status=ResumeExtractionStatus.partial,
                warnings=[
                    *extraction_warnings,
                    *ocr_warnings,
                    *_quality_warnings(ocr_text),
                ],
                needs_manual_correction=True,
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
            warnings=[
                *extraction_warnings,
                *ocr_warnings,
                "PDF 文本提取没有得到可用内容；请手动粘贴简历文本。",
            ],
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


def _extract_docx_input(request: ResumeInputRequest) -> ResumeExtractionResult:
    manual_text = (request.text or "").strip()
    warnings: list[str] = []
    if request.content_base64:
        try:
            data = base64.b64decode(request.content_base64, validate=True)
            extracted = _extract_docx_bytes(data)
        except Exception:
            extracted = ""
            warnings.append("DOCX 文件解析失败；请粘贴文本或转 PDF 后重试。")
        if extracted.strip():
            return ResumeExtractionResult(
                input_type=ResumeInputType.docx,
                raw_text=extracted.strip(),
                status=ResumeExtractionStatus.extracted,
                warnings=[*warnings, *_quality_warnings(extracted)],
                needs_manual_correction=_is_low_quality(extracted),
            )
        warnings.append("DOCX 中没有识别到可用文字；如果这是图片版简历，请粘贴文本或转为可复制文本的 PDF。")
    if manual_text:
        return ResumeExtractionResult(
            input_type=ResumeInputType.docx,
            raw_text=manual_text,
            status=ResumeExtractionStatus.partial,
            warnings=[*warnings, "已使用 docx 输入中提供的文本作为人工兜底内容。", *_quality_warnings(manual_text)],
            needs_manual_correction=True,
        )
    return ResumeExtractionResult(
        input_type=ResumeInputType.docx,
        status=ResumeExtractionStatus.manual_required,
        warnings=warnings or ["DOCX 中没有可用文本；请粘贴文本或上传可复制文字的 PDF。"],
        needs_manual_correction=True,
    )


def _extract_docx_bytes(data: bytes) -> str:
    """Extract visible text from a .docx package without adding a dependency."""

    parts = [
        "word/document.xml",
        "word/footnotes.xml",
        "word/endnotes.xml",
    ]
    paragraphs: list[str] = []
    with zipfile.ZipFile(BytesIO(data)) as archive:
        for part in parts:
            if part not in archive.namelist():
                continue
            root = ElementTree.fromstring(archive.read(part))
            paragraphs.extend(_docx_paragraphs(root))
    return "\n".join(line for line in paragraphs if line.strip())


def _docx_paragraphs(root: ElementTree.Element) -> list[str]:
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        runs: list[str] = []
        for child in paragraph.iter():
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "t" and child.text:
                runs.append(child.text)
            elif tag == "tab":
                runs.append("\t")
            elif tag == "br":
                runs.append("\n")
        text = "".join(runs).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


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

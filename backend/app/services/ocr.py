"""Local best-effort OCR helpers for PDF and image inputs."""

from __future__ import annotations

import os
from pathlib import Path
import shutil


def extract_pdf_ocr_text(data: bytes, label: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    try:
        import fitz  # type: ignore
    except ModuleNotFoundError:
        return "", [f"疑似扫描版或图片型 {label} PDF，但当前环境未安装 PyMuPDF，无法进一步检测 OCR。"]

    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception:
        return "", [f"{label} PDF 无法作为标准文档打开，可能需要重新导出或粘贴文本。"]

    image_pages = 0
    ocr_text_parts: list[str] = []
    ocr_available = pymupdf_ocr_available()
    try:
        for page in document:
            if page.get_images(full=True):
                image_pages += 1
            if not ocr_available:
                continue
            try:
                textpage = page.get_textpage_ocr(language="chi_sim+eng", full=True)
                text = page.get_text("text", textpage=textpage).strip()
                if text:
                    ocr_text_parts.append(text)
            except Exception:
                continue
    finally:
        document.close()

    if ocr_text_parts:
        return "\n".join(ocr_text_parts), [f"{label} PDF 没有可复制文本层，已尝试使用本地 OCR 从页面图像提取。"]
    if image_pages:
        warnings.append(f"检测到扫描版/图片型 {label} PDF，但当前运行环境没有可用 OCR 引擎；请粘贴文本或上传可复制文字的 PDF。")
    else:
        warnings.append(f"{label} PDF 没有可复制文本层；请粘贴文本或重新导出为可复制文字的 PDF。")
    return "", warnings


def extract_image_ocr_text(data: bytes, label: str) -> tuple[str, list[str]]:
    try:
        import fitz  # type: ignore
    except ModuleNotFoundError:
        return "", [f"当前环境未安装 PyMuPDF，无法对{label}图片执行 OCR；请粘贴文本。"]

    if not pymupdf_ocr_available():
        return "", [f"当前运行环境没有可用 OCR 引擎，无法识别{label}图片；请粘贴文本。"]

    document = None
    pixmap = None
    try:
        pixmap = fitz.Pixmap(data)
        width = max(1, pixmap.width)
        height = max(1, pixmap.height)
        document = fitz.open()
        page = document.new_page(width=width, height=height)
        page.insert_image(page.rect, stream=data)
        textpage = page.get_textpage_ocr(language="chi_sim+eng", full=True)
        text = page.get_text("text", textpage=textpage).strip()
    except Exception:
        return "", [f"{label}图片 OCR 识别失败；请粘贴文本或重新上传更清晰的图片。"]
    finally:
        if document is not None:
            document.close()
        pixmap = None

    if text:
        return text, [f"已尝试使用本地 OCR 识别{label}图片，结果可能需要人工校对。"]
    return "", [f"{label}图片没有识别到可用文字；请粘贴文本或上传更清晰的图片。"]


def pymupdf_ocr_available() -> bool:
    tessdata_dir = resolve_tessdata_dir()
    if tessdata_dir:
        os.environ.setdefault("TESSDATA_PREFIX", str(tessdata_dir))
        return True
    return bool(shutil.which("tesseract"))


def resolve_tessdata_dir() -> Path | None:
    candidates = [
        os.getenv("INTERVIEWPILOT_TESSDATA_PREFIX"),
        os.getenv("TESSDATA_PREFIX"),
        str(Path(__file__).resolve().parents[3] / "data" / "tessdata"),
        r"D:\Program Files\Tesseract-OCR\tessdata",
        r"C:\Program Files\Tesseract-OCR\tessdata",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if (path / "eng.traineddata").exists() or (path / "chi_sim.traineddata").exists():
            return path
    return None

"""Shared pytest fixtures and synthetic PDF builders."""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest


@pytest.fixture
def fixtures_dir(tmp_path: Path) -> Path:
    """Temporary directory for generated PDF fixtures."""
    path = tmp_path / "fixtures"
    path.mkdir(parents=True, exist_ok=True)
    return path


def make_empty_pdf(path: Path) -> Path:
    """Create a one-page PDF with no text and no images."""
    doc = fitz.open()
    doc.new_page(width=595, height=842)
    doc.save(path)
    doc.close()
    return path


def make_digital_text_pdf(path: Path, *, text: str = "Hello world") -> Path:
    """Create a one-page digital-text PDF with native text."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    # Insert multiple lines so coverage / char count are meaningful.
    y = 72.0
    for line in (text, text, text):
        page.insert_text((72, y), line, fontsize=14)
        y += 24
    doc.save(path)
    doc.close()
    return path


def make_arabic_digital_pdf(path: Path) -> Path:
    """Create a digital PDF containing Arabic Unicode text (logical order)."""
    arabic = "مرحبا بالعالم"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 100), arabic, fontsize=16, fontname="helv")
    try:
        page.insert_htmlbox(fitz.Rect(72, 160, 500, 240), f"<p>{arabic}</p>")
    except Exception:  # noqa: BLE001
        page.insert_text((72, 180), arabic, fontsize=16)
    doc.save(path)
    doc.close()
    return path


def _solid_pixmap(width: int, height: int, rgb: tuple[int, int, int]) -> fitz.Pixmap:
    """Create an opaque RGB pixmap filled with ``rgb``."""
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height), 0)
    pix.set_rect(pix.irect, rgb)
    return pix


def make_scanned_image_pdf(path: Path) -> Path:
    """Create a PDF page that is a full-page pixmap image (no native text)."""
    pix = _solid_pixmap(400, 600, (220, 220, 220))
    doc = fitz.open()
    page = doc.new_page(width=400, height=600)
    page.insert_image(page.rect, pixmap=pix)
    doc.save(path)
    doc.close()
    return path


def make_mixed_pdf(path: Path) -> Path:
    """Create a page with both native text and a sizable image."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "Digital caption text for mixed page", fontsize=14)
    page.insert_text((72, 96), "Second line of native text content", fontsize=14)
    pix = _solid_pixmap(300, 400, (180, 180, 180))
    page.insert_image(fitz.Rect(100, 120, 500, 650), pixmap=pix)
    doc.save(path)
    doc.close()
    return path


def make_bilingual_pdf(path: Path) -> Path:
    """Create a digital PDF with Latin and Arabic characters."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "English title", fontsize=14)
    page.insert_text((72, 110), "نص عربي", fontsize=14)
    try:
        page.insert_htmlbox(
            fitz.Rect(72, 140, 500, 220),
            "<p>English and عربي mixed</p>",
        )
    except Exception:  # noqa: BLE001
        page.insert_text((72, 150), "English and عربي mixed", fontsize=14)
    doc.save(path)
    doc.close()
    return path

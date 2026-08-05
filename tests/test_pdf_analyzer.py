"""Integration tests for the PDF analyzer."""

from __future__ import annotations

from pathlib import Path

import pytest

from packages.document_model.enums import PageType
from packages.pdf_analyzer import analyze_pdf
from tests.conftest import (
    make_digital_text_pdf,
    make_empty_pdf,
    make_mixed_pdf,
    make_scanned_image_pdf,
)


def test_empty_pdf_page_handling(fixtures_dir: Path) -> None:
    pdf = make_empty_pdf(fixtures_dir / "empty.pdf")
    doc = analyze_pdf(pdf)
    assert doc.page_count == 1
    assert doc.pages[0].page_type == PageType.EMPTY
    assert doc.pages[0].needs_ocr is False
    assert doc.source_sha256
    assert len(doc.source_sha256) == 64


def test_digital_text_page_classification(fixtures_dir: Path) -> None:
    pdf = make_digital_text_pdf(fixtures_dir / "digital.pdf", text="Sample digital paragraph.")
    doc = analyze_pdf(pdf)
    assert doc.pages[0].page_type == PageType.DIGITAL_TEXT
    assert doc.pages[0].needs_ocr is False
    assert any(block.text_raw for block in doc.pages[0].blocks)


def test_scanned_image_page_classification(fixtures_dir: Path) -> None:
    pdf = make_scanned_image_pdf(fixtures_dir / "scanned.pdf")
    doc = analyze_pdf(pdf)
    assert doc.pages[0].page_type in {PageType.SCANNED_IMAGE, PageType.UNKNOWN}
    if doc.pages[0].page_type == PageType.SCANNED_IMAGE:
        assert doc.pages[0].needs_ocr is True
        assert doc.pages[0].has_images is True
    else:
        assert doc.pages[0].text_coverage_ratio == 0.0


def test_mixed_page_or_digital_with_image(fixtures_dir: Path) -> None:
    pdf = make_mixed_pdf(fixtures_dir / "mixed.pdf")
    doc = analyze_pdf(pdf)
    assert doc.pages[0].page_type in {PageType.MIXED, PageType.DIGITAL_TEXT, PageType.UNKNOWN}
    assert doc.pages[0].has_images is True


def test_invalid_pdf_handling(fixtures_dir: Path) -> None:
    bad = fixtures_dir / "not.pdf"
    bad.write_bytes(b"this is not a pdf file")
    with pytest.raises(ValueError, match="Unable to open PDF"):
        analyze_pdf(bad)


def test_missing_pdf_raises(fixtures_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        analyze_pdf(fixtures_dir / "missing.pdf")


def test_deterministic_repeated_analysis(fixtures_dir: Path) -> None:
    pdf = make_digital_text_pdf(fixtures_dir / "det.pdf", text="Determinism check")
    first = analyze_pdf(pdf)
    second = analyze_pdf(pdf)
    assert first.source_sha256 == second.source_sha256
    assert first.document_id == second.document_id
    assert first.page_count == second.page_count
    assert [p.page_type for p in first.pages] == [p.page_type for p in second.pages]
    assert [b.block_id for p in first.pages for b in p.blocks] == [
        b.block_id for p in second.pages for b in p.blocks
    ]
    assert [b.reading_order for p in first.pages for b in p.blocks] == [
        b.reading_order for p in second.pages for b in p.blocks
    ]
    assert [b.text_raw for p in first.pages for b in p.blocks] == [
        b.text_raw for p in second.pages for b in p.blocks
    ]

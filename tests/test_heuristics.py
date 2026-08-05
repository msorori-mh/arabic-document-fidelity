"""Tests for Arabic/direction heuristics and SHA-256 hashing."""

from __future__ import annotations

from pathlib import Path

from packages.document_model.enums import Direction, PageType
from packages.pdf_analyzer.hashing import sha256_file
from packages.pdf_analyzer.heuristics import (
    classify_page_type,
    detect_arabic_chars,
    infer_direction,
)


def test_sha256_calculation(tmp_path: Path) -> None:
    import hashlib

    path = tmp_path / "sample.bin"
    path.write_bytes(b"arabic-document-fidelity")
    digest = sha256_file(path)
    assert len(digest) == 64
    assert digest == sha256_file(path)
    expected = hashlib.sha256(b"arabic-document-fidelity").hexdigest()
    assert digest == expected


def test_detect_arabic_chars() -> None:
    assert detect_arabic_chars("مرحبا") is True
    assert detect_arabic_chars("Hello") is False
    assert detect_arabic_chars("") is False
    assert detect_arabic_chars("mix عربي text") is True


def test_infer_direction_rtl_ltr_mixed_unknown() -> None:
    assert infer_direction("مرحبا بالعالم") == Direction.RTL
    assert infer_direction("Hello world") == Direction.LTR
    assert infer_direction("Hello مرحبا") == Direction.MIXED
    assert infer_direction("1234 !!!") == Direction.UNKNOWN
    assert infer_direction("") == Direction.UNKNOWN


def test_classify_digital_text() -> None:
    page_type, risk, _warnings = classify_page_type(
        text_coverage_ratio=0.08,
        image_coverage_ratio=0.0,
        text_char_count=40,
        image_count=0,
    )
    assert page_type == PageType.DIGITAL_TEXT
    assert risk.value in {"low", "medium"}


def test_classify_scanned_image() -> None:
    page_type, _risk, _warnings = classify_page_type(
        text_coverage_ratio=0.0,
        image_coverage_ratio=0.9,
        text_char_count=0,
        image_count=1,
    )
    assert page_type == PageType.SCANNED_IMAGE


def test_classify_empty() -> None:
    page_type, _risk, _warnings = classify_page_type(
        text_coverage_ratio=0.0,
        image_coverage_ratio=0.0,
        text_char_count=0,
        image_count=0,
    )
    assert page_type == PageType.EMPTY

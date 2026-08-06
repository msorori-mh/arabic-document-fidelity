"""Tests for the Mock OCR engine safety behavior."""

from __future__ import annotations

import pytest

from packages.document_model.enums import BlockType, Direction
from packages.document_model.models import BoundingBox
from packages.mock_ocr import MOCK_ENGINE_ID, MockOCREngine
from packages.ocr_contracts.errors import OCREngineError
from packages.ocr_contracts.models import (
    ExecutionMode,
    OCRBlockResult,
    OCRPageRequest,
    OCRPageResult,
)


def _fixture_result(document_id: str = "doc_1", page_number: int = 1) -> OCRPageResult:
    return OCRPageResult(
        document_id=document_id,
        page_number=page_number,
        engine_id=MOCK_ENGINE_ID,
        blocks=[
            OCRBlockResult(
                block_id="mock_b0",
                block_type=BlockType.PARAGRAPH,
                text_raw="مرحبا",
                direction=Direction.RTL,
                bbox=BoundingBox(x0=0, y0=0, x1=10, y1=10),
                reading_order=0,
                confidence=None,
                source_engine=MOCK_ENGINE_ID,
                metadata={"fixture": True},
            )
        ],
        page_confidence=None,
        warnings=[],
    )


def test_test_only_descriptor() -> None:
    engine = MockOCREngine()
    assert engine.descriptor.test_only is True
    assert engine.descriptor.execution_mode == ExecutionMode.MOCK
    assert engine.descriptor.requires_network is False
    assert engine.health_check() is True


def test_deterministic_fixture_response() -> None:
    engine = MockOCREngine()
    engine.set_fixture("doc_1", 1, _fixture_result())
    request = OCRPageRequest(
        document_id="doc_1",
        page_number=1,
        page_width=100,
        page_height=200,
        image_path="/tmp/ignored.png",
    )
    first = engine.process_page(request)
    second = engine.process_page(request)
    assert first.blocks[0].text_raw == "مرحبا"
    assert first.blocks[0].text_raw == second.blocks[0].text_raw
    assert "test_only: mock OCR result" in first.warnings
    assert "mock/test-only engine" in first.processing_metadata.notes


def test_refusal_without_fixture() -> None:
    engine = MockOCREngine()
    request = OCRPageRequest(
        document_id="doc_missing",
        page_number=1,
        page_width=100,
        page_height=200,
        image_path="C:/somewhere/page.png",
    )
    with pytest.raises(OCREngineError, match="refuses execution"):
        engine.process_page(request)


def test_no_fabricated_text_from_input_files() -> None:
    # Even if an image path is supplied, MockOCR never reads it.
    engine = MockOCREngine()
    request = OCRPageRequest(
        document_id="doc_1",
        page_number=1,
        page_width=100,
        page_height=200,
        image_path="definitely-not-read.png",
    )
    with pytest.raises(OCREngineError):
        engine.process_page(request)


def test_zero_network_behavior() -> None:
    engine = MockOCREngine()
    assert engine.descriptor.requires_network is False
    assert engine.health_check() is True

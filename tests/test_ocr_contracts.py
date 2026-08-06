"""Tests for OCR contract models and serialization."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from packages.document_model.enums import BlockType, Direction
from packages.document_model.models import BoundingBox
from packages.ocr_contracts.models import (
    ExecutionMode,
    OCRBlockResult,
    OCREngineDescriptor,
    OCRPageRequest,
    OCRPageResult,
)


def test_descriptor_validation_and_modes() -> None:
    descriptor = OCREngineDescriptor(
        engine_id="local_demo",
        display_name="Demo",
        version="0.0.1",
        provider="test",
        execution_mode=ExecutionMode.LOCAL,
        supported_languages=["en", "ar"],
        requires_network=False,
        test_only=False,
    )
    assert descriptor.supported_languages == ["ar", "en"]
    assert descriptor.execution_mode == ExecutionMode.LOCAL


def test_invalid_confidence_rejected() -> None:
    with pytest.raises(ValidationError):
        OCRBlockResult(
            block_id="b1",
            block_type=BlockType.PARAGRAPH,
            text_raw="مرحبا",
            direction=Direction.RTL,
            bbox=BoundingBox(x0=0, y0=0, x1=10, y1=10),
            reading_order=0,
            confidence=1.5,
            source_engine="mock_ocr_v1",
        )


def test_invalid_bbox_rejected() -> None:
    with pytest.raises(ValidationError):
        BoundingBox(x0=5, y0=0, x1=1, y1=10)


def test_unexpected_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        OCRPageRequest.model_validate(
            {
                "document_id": "doc",
                "page_number": 1,
                "page_width": 100,
                "page_height": 200,
                "unexpected": True,
            }
        )


def test_arabic_logical_text_preserved() -> None:
    arabic = "مرحبا بالعالم"
    block = OCRBlockResult(
        block_id="b1",
        block_type=BlockType.PARAGRAPH,
        text_raw=arabic,
        direction=Direction.RTL,
        bbox=BoundingBox(x0=0, y0=0, x1=10, y1=10),
        reading_order=0,
        confidence=None,
        source_engine="mock_ocr_v1",
    )
    assert block.text_raw == arabic
    assert block.text_raw != arabic[::-1]


def test_stable_serialization() -> None:
    result = OCRPageResult(
        document_id="doc_1",
        page_number=1,
        engine_id="mock_ocr_v1",
        blocks=[],
        page_confidence=None,
        warnings=["test_only: mock OCR result"],
    )
    payload = json.loads(result.model_dump_json())
    restored = OCRPageResult.model_validate(payload)
    assert restored.document_id == "doc_1"
    assert restored.page_confidence is None
    assert json.loads(restored.model_dump_json())["engine_id"] == "mock_ocr_v1"


def test_null_confidence_allowed() -> None:
    block = OCRBlockResult(
        block_id="b1",
        block_type=BlockType.PARAGRAPH,
        text_raw="Hello",
        direction=Direction.LTR,
        bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
        reading_order=0,
        confidence=None,
        source_engine="mock_ocr_v1",
    )
    assert block.confidence is None

"""Tests for document model validation and JSON serialization."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from packages.document_model import (
    SCHEMA_VERSION,
    BlockModel,
    BlockType,
    BoundingBox,
    Direction,
    DocumentModel,
    PageModel,
    PageType,
    ProcessingMetadata,
    RiskLevel,
)


def _sample_block() -> BlockModel:
    return BlockModel(
        block_id="p1_t0_0",
        block_type=BlockType.PARAGRAPH,
        text_raw="مرحبا",
        direction=Direction.RTL,
        bbox=BoundingBox(x0=10, y0=20, x1=100, y1=40),
        reading_order=0,
        confidence=None,
        source_engine="pymupdf_native",
        risk_level=RiskLevel.LOW,
        metadata={"contains_arabic": True},
    )


def test_document_model_validation() -> None:
    doc = DocumentModel(
        schema_version=SCHEMA_VERSION,
        document_id="doc_abc",
        source_filename="sample.pdf",
        source_sha256="a" * 64,
        page_count=1,
        pages=[
            PageModel(
                page_number=1,
                width=595,
                height=842,
                page_type=PageType.DIGITAL_TEXT,
                blocks=[_sample_block()],
            )
        ],
        processing_metadata=ProcessingMetadata(duration_ms=1.5),
        warnings=[],
    )
    assert doc.page_count == 1
    assert doc.pages[0].blocks[0].direction == Direction.RTL


def test_invalid_sha256_rejected() -> None:
    with pytest.raises(ValidationError):
        DocumentModel(
            document_id="doc_x",
            source_filename="a.pdf",
            source_sha256="not-a-hash",
            page_count=0,
        )


def test_invalid_bbox_rejected() -> None:
    with pytest.raises(ValidationError):
        BoundingBox(x0=10, y0=10, x1=5, y1=20)


def test_confidence_range() -> None:
    with pytest.raises(ValidationError):
        BlockModel(
            block_id="b1",
            block_type=BlockType.UNKNOWN,
            bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
            reading_order=0,
            confidence=1.5,
        )


def test_stable_json_serialization() -> None:
    doc = DocumentModel(
        document_id="doc_stable",
        source_filename="stable.pdf",
        source_sha256="b" * 64,
        page_count=1,
        pages=[
            PageModel(
                page_number=1,
                width=100,
                height=200,
                page_type=PageType.EMPTY,
                blocks=[],
            )
        ],
    )
    raw = doc.to_json()
    parsed = json.loads(raw)
    assert parsed["schema_version"] == SCHEMA_VERSION
    assert parsed["source_sha256"] == "b" * 64
    restored = DocumentModel.model_validate(parsed)
    assert restored.document_id == doc.document_id
    assert json.loads(restored.to_json())["pages"][0]["page_type"] == "empty"


def test_enums_serialize_as_strings() -> None:
    block = _sample_block()
    payload = json.loads(block.model_dump_json())
    assert payload["block_type"] == "paragraph"
    assert payload["direction"] == "rtl"
    assert payload["risk_level"] == "low"

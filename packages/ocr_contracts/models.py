"""Pydantic models for the provider-neutral OCR engine contract."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.document_model.enums import BlockType, Direction
from packages.document_model.models import BoundingBox

CONTRACT_SCHEMA_VERSION = "1.0.0"


class ExecutionMode(StrEnum):
    """Where an OCR engine is expected to execute."""

    LOCAL = "local"
    CLOUD = "cloud"
    MOCK = "mock"


class RequestedFeature(StrEnum):
    """Optional features a caller may request from an engine."""

    TEXT = "text"
    LAYOUT = "layout"
    TABLES = "tables"
    WORD_CONFIDENCE = "word_confidence"
    BLOCK_CONFIDENCE = "block_confidence"


class OCREngineDescriptor(BaseModel):
    """Static description of a registered OCR engine."""

    model_config = ConfigDict(extra="forbid")

    engine_id: str
    display_name: str
    version: str
    provider: str
    execution_mode: ExecutionMode
    supported_languages: list[str] = Field(default_factory=list)
    supports_layout: bool = False
    supports_tables: bool = False
    supports_word_confidence: bool = False
    supports_block_confidence: bool = False
    requires_network: bool = False
    test_only: bool = False

    @field_validator("engine_id")
    @classmethod
    def _engine_id_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("engine_id must be non-empty")
        return value.strip()

    @field_validator("supported_languages")
    @classmethod
    def _stable_languages(cls, value: list[str]) -> list[str]:
        return sorted({lang.strip() for lang in value if lang.strip()})


class OCRProcessingMetadata(BaseModel):
    """Processing metadata attached to an OCR page result."""

    model_config = ConfigDict(extra="forbid")

    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: float = 0.0
    notes: list[str] = Field(default_factory=list)


class OCRPageRequest(BaseModel):
    """Request payload for processing a single page with an OCR engine."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    page_number: int
    page_width: float
    page_height: float
    image_path: str | None = None
    image_ref: str | None = None
    language_hints: list[str] = Field(default_factory=list)
    requested_features: list[RequestedFeature] = Field(
        default_factory=lambda: [RequestedFeature.TEXT]
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("page_number")
    @classmethod
    def _page_number_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("page_number must be >= 1")
        return value


class OCRBlockResult(BaseModel):
    """A single OCR-extracted content block.

    ``text_raw`` must remain logical text. Engines must not reverse Arabic
    strings or apply visual bidi conversion for storage.
    """

    model_config = ConfigDict(extra="forbid")

    block_id: str
    block_type: BlockType
    text_raw: str = ""
    direction: Direction = Direction.UNKNOWN
    bbox: BoundingBox
    reading_order: int
    confidence: float | None = None
    source_engine: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reading_order")
    @classmethod
    def _reading_order_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("reading_order must be >= 0")
        return value

    @field_validator("confidence")
    @classmethod
    def _confidence_range(cls, value: float | None) -> float | None:
        if value is not None and not 0.0 <= value <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0 inclusive")
        return value


class OCRPageResult(BaseModel):
    """OCR result for a single page."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    page_number: int
    engine_id: str
    blocks: list[OCRBlockResult] = Field(default_factory=list)
    page_confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)
    processing_metadata: OCRProcessingMetadata = Field(default_factory=OCRProcessingMetadata)

    @field_validator("page_number")
    @classmethod
    def _page_number_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("page_number must be >= 1")
        return value

    @field_validator("page_confidence")
    @classmethod
    def _page_confidence_range(cls, value: float | None) -> float | None:
        if value is not None and not 0.0 <= value <= 1.0:
            raise ValueError("page_confidence must be between 0.0 and 1.0 inclusive")
        return value

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize to JSON with sorted keys for deterministic CLI/tests."""
        return self.model_dump_json(indent=indent)

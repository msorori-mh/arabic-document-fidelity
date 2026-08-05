"""Pydantic v2 models for the versioned Arabic Document IR."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from packages.document_model.enums import BlockType, Direction, PageType, RiskLevel

SCHEMA_VERSION = "1.0.0"


class BoundingBox(BaseModel):
    """Axis-aligned bounding box in PDF page coordinates (origin top-left)."""

    model_config = ConfigDict(extra="forbid")

    x0: float
    y0: float
    x1: float
    y1: float

    @field_validator("x1")
    @classmethod
    def _x1_gte_x0(cls, value: float, info: ValidationInfo) -> float:
        x0 = info.data.get("x0")
        if isinstance(x0, (int, float)) and value < float(x0):
            raise ValueError("x1 must be >= x0")
        return value

    @field_validator("y1")
    @classmethod
    def _y1_gte_y0(cls, value: float, info: ValidationInfo) -> float:
        y0 = info.data.get("y0")
        if isinstance(y0, (int, float)) and value < float(y0):
            raise ValueError("y1 must be >= y0")
        return value


class ProcessingMetadata(BaseModel):
    """Metadata describing how a document was analyzed."""

    model_config = ConfigDict(extra="forbid")

    analyzer_name: str = "pdf_analyzer"
    analyzer_version: str = "0.1.0"
    processed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: float = 0.0
    pymupdf_version: str | None = None
    notes: list[str] = Field(default_factory=list)


class BlockModel(BaseModel):
    """A single content block within a page."""

    model_config = ConfigDict(extra="forbid")

    block_id: str
    block_type: BlockType
    text_raw: str = ""
    direction: Direction = Direction.UNKNOWN
    bbox: BoundingBox
    reading_order: int
    confidence: float | None = None
    source_engine: str = "pymupdf_native"
    risk_level: RiskLevel = RiskLevel.UNKNOWN
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


class PageModel(BaseModel):
    """A single page within a document."""

    model_config = ConfigDict(extra="forbid")

    page_number: int
    width: float
    height: float
    rotation: int = 0
    page_type: PageType = PageType.UNKNOWN
    language_hints: list[str] = Field(default_factory=list)
    text_coverage_ratio: float = 0.0
    image_coverage_ratio: float = 0.0
    needs_ocr: bool = False
    has_tables: bool = False
    has_images: bool = False
    has_multiple_columns: bool = False
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    blocks: list[BlockModel] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("page_number")
    @classmethod
    def _page_number_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("page_number must be >= 1")
        return value

    @field_validator("text_coverage_ratio", "image_coverage_ratio")
    @classmethod
    def _ratio_range(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("coverage ratios must be between 0.0 and 1.0 inclusive")
        return value


class DocumentModel(BaseModel):
    """Versioned Arabic Document Intermediate Representation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    document_id: str
    source_filename: str
    source_sha256: str
    page_count: int
    pages: list[PageModel] = Field(default_factory=list)
    processing_metadata: ProcessingMetadata = Field(default_factory=ProcessingMetadata)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("page_count")
    @classmethod
    def _page_count_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("page_count must be >= 0")
        return value

    @field_validator("source_sha256")
    @classmethod
    def _sha256_format(cls, value: str) -> str:
        normalized = value.lower()
        if len(normalized) != 64 or any(c not in "0123456789abcdef" for c in normalized):
            raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
        return normalized

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize to stable, sorted-key JSON."""
        return self.model_dump_json(indent=indent)

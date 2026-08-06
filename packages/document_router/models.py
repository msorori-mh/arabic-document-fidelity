"""Routing-plan sidecar models (does not mutate Arabic Document IR)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.document_model.enums import PageType, RiskLevel

ROUTING_SCHEMA_VERSION = "1.0.0"


class RoutingAction(StrEnum):
    """Action selected for a page by the routing policy."""

    USE_NATIVE_TEXT = "use_native_text"
    RUN_OCR = "run_ocr"
    REVIEW_REQUIRED = "review_required"
    SKIP_EMPTY = "skip_empty"
    UNSUPPORTED = "unsupported"


class RoutingReason(StrEnum):
    """Stable reason codes explaining a routing decision."""

    SUFFICIENT_NATIVE_TEXT = "sufficient_native_text"
    SCANNED_PAGE = "scanned_page"
    MIXED_PAGE_REQUIRES_OCR = "mixed_page_requires_ocr"
    UNKNOWN_PAGE_TYPE = "unknown_page_type"
    EMPTY_PAGE = "empty_page"
    HIGH_RISK_PAGE = "high_risk_page"
    NO_ELIGIBLE_ENGINE = "no_eligible_engine"
    TEST_ENGINE_ONLY = "test_engine_only"


class PageRoutingDecision(BaseModel):
    """Per-page routing decision sidecar."""

    model_config = ConfigDict(extra="forbid")

    page_number: int
    page_type: PageType
    needs_ocr: bool
    risk_level: RiskLevel
    action: RoutingAction
    reason: RoutingReason
    selected_engine_id: str | None = None
    fallback_engine_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("page_number")
    @classmethod
    def _page_number_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("page_number must be >= 1")
        return value


class RoutingPlanSummary(BaseModel):
    """Aggregate counts for a document routing plan."""

    model_config = ConfigDict(extra="forbid")

    total_pages: int = 0
    native_pages: int = 0
    pages_requiring_ocr: int = 0
    review_required_pages: int = 0
    skipped_empty_pages: int = 0
    unsupported_pages: int = 0
    selected_engines: list[str] = Field(default_factory=list)


class DocumentRoutingPlan(BaseModel):
    """Document-level OCR routing plan (sidecar; IR unchanged)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = ROUTING_SCHEMA_VERSION
    document_id: str
    source_sha256: str
    policy_version: str
    page_decisions: list[PageRoutingDecision] = Field(default_factory=list)
    summary: RoutingPlanSummary = Field(default_factory=RoutingPlanSummary)
    warnings: list[str] = Field(default_factory=list)

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize deterministically for CLI/tests (sorted keys via dumps)."""
        # model_dump_json does not sort keys; callers that need sorted output
        # should use json.dumps(..., sort_keys=True) — same Foundation-01 pattern.
        return self.model_dump_json(indent=indent)

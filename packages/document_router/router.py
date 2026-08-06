"""Document router: DocumentModel → DocumentRoutingPlan (no IR mutation)."""

from __future__ import annotations

from packages.document_model.models import DocumentModel
from packages.document_router.models import (
    ROUTING_SCHEMA_VERSION,
    DocumentRoutingPlan,
    PageRoutingDecision,
    RoutingAction,
    RoutingPlanSummary,
)
from packages.document_router.policy import POLICY_VERSION, RoutingPolicy
from packages.ocr_registry.registry import OCREngineRegistry


class DocumentRouter:
    """Build a deterministic OCR routing plan from a diagnosed document."""

    def __init__(
        self,
        registry: OCREngineRegistry,
        *,
        policy: RoutingPolicy | None = None,
        allow_test_engines: bool = False,
    ) -> None:
        self._registry = registry
        self._policy = policy or RoutingPolicy()
        self._allow_test_engines = allow_test_engines

    @property
    def allow_test_engines(self) -> bool:
        return self._allow_test_engines

    def plan(self, document: DocumentModel) -> DocumentRoutingPlan:
        """Produce a routing plan without mutating ``document``."""
        decisions: list[PageRoutingDecision] = [
            self._policy.decide_page(
                page,
                self._registry,
                allow_test_engines=self._allow_test_engines,
            )
            for page in document.pages
        ]
        summary = self._summarize(decisions)
        warnings: list[str] = []
        if any(d.action == RoutingAction.REVIEW_REQUIRED for d in decisions):
            warnings.append("one or more pages require human review before OCR execution")
        if not self._allow_test_engines:
            warnings.append("test-only OCR engines are excluded from this routing plan")

        return DocumentRoutingPlan(
            schema_version=ROUTING_SCHEMA_VERSION,
            document_id=document.document_id,
            source_sha256=document.source_sha256,
            policy_version=POLICY_VERSION,
            page_decisions=decisions,
            summary=summary,
            warnings=warnings,
        )

    @staticmethod
    def _summarize(decisions: list[PageRoutingDecision]) -> RoutingPlanSummary:
        selected: set[str] = set()
        native = ocr = review = empty = unsupported = 0
        for decision in decisions:
            if decision.selected_engine_id:
                selected.add(decision.selected_engine_id)
            if decision.action == RoutingAction.USE_NATIVE_TEXT:
                native += 1
            elif decision.action == RoutingAction.RUN_OCR:
                ocr += 1
            elif decision.action == RoutingAction.REVIEW_REQUIRED:
                review += 1
            elif decision.action == RoutingAction.SKIP_EMPTY:
                empty += 1
            elif decision.action == RoutingAction.UNSUPPORTED:
                unsupported += 1

        return RoutingPlanSummary(
            total_pages=len(decisions),
            native_pages=native,
            pages_requiring_ocr=ocr,
            review_required_pages=review,
            skipped_empty_pages=empty,
            unsupported_pages=unsupported,
            selected_engines=sorted(selected),
        )

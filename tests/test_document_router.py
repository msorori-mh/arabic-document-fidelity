"""Tests for conservative document OCR routing."""

from __future__ import annotations

from packages.document_model.enums import PageType, RiskLevel
from packages.document_model.models import DocumentModel, PageModel
from packages.document_router import DocumentRouter, RoutingAction, RoutingReason
from packages.mock_ocr import MOCK_ENGINE_ID, MockOCREngine
from packages.ocr_contracts.models import (
    ExecutionMode,
    OCREngineDescriptor,
    OCRPageRequest,
    OCRPageResult,
)
from packages.ocr_registry import OCREngineRegistry


def _page(
    *,
    number: int = 1,
    page_type: PageType,
    needs_ocr: bool = False,
    risk: RiskLevel = RiskLevel.LOW,
) -> PageModel:
    return PageModel(
        page_number=number,
        width=595,
        height=842,
        page_type=page_type,
        needs_ocr=needs_ocr,
        risk_level=risk,
    )


def _document(*pages: PageModel) -> DocumentModel:
    return DocumentModel(
        document_id="doc_test",
        source_filename="test.pdf",
        source_sha256="a" * 64,
        page_count=len(pages),
        pages=list(pages),
    )


class _StubEngine:
    def __init__(self, engine_id: str, *, layout: bool = False, test_only: bool = False) -> None:
        self._descriptor = OCREngineDescriptor(
            engine_id=engine_id,
            display_name=engine_id,
            version="0.0.1",
            provider="stub",
            execution_mode=ExecutionMode.LOCAL,
            supports_layout=layout,
            requires_network=False,
            test_only=test_only,
        )

    @property
    def descriptor(self) -> OCREngineDescriptor:
        return self._descriptor

    def health_check(self) -> bool:
        return True

    def process_page(self, request: OCRPageRequest) -> OCRPageResult:
        raise NotImplementedError(f"stub engine does not process pages: {request.document_id}")


def test_digital_page_uses_native() -> None:
    router = DocumentRouter(OCREngineRegistry())
    plan = router.plan(_document(_page(page_type=PageType.DIGITAL_TEXT, needs_ocr=False)))
    decision = plan.page_decisions[0]
    assert decision.action == RoutingAction.USE_NATIVE_TEXT
    assert decision.reason == RoutingReason.SUFFICIENT_NATIVE_TEXT
    assert decision.selected_engine_id is None


def test_scanned_without_real_engine_requires_review() -> None:
    router = DocumentRouter(OCREngineRegistry())
    plan = router.plan(
        _document(_page(page_type=PageType.SCANNED_IMAGE, needs_ocr=True, risk=RiskLevel.MEDIUM))
    )
    decision = plan.page_decisions[0]
    assert decision.action == RoutingAction.REVIEW_REQUIRED
    assert decision.reason == RoutingReason.NO_ELIGIBLE_ENGINE


def test_mixed_without_layout_engine_requires_review() -> None:
    registry = OCREngineRegistry()
    registry.register(_StubEngine("text_only", layout=False))
    router = DocumentRouter(registry)
    plan = router.plan(
        _document(_page(page_type=PageType.MIXED, needs_ocr=True, risk=RiskLevel.HIGH))
    )
    decision = plan.page_decisions[0]
    assert decision.action == RoutingAction.REVIEW_REQUIRED


def test_empty_page_skipped() -> None:
    router = DocumentRouter(OCREngineRegistry())
    plan = router.plan(_document(_page(page_type=PageType.EMPTY)))
    assert plan.page_decisions[0].action == RoutingAction.SKIP_EMPTY
    assert plan.page_decisions[0].reason == RoutingReason.EMPTY_PAGE


def test_unknown_page_requires_review() -> None:
    router = DocumentRouter(OCREngineRegistry())
    plan = router.plan(_document(_page(page_type=PageType.UNKNOWN, needs_ocr=True)))
    assert plan.page_decisions[0].action == RoutingAction.REVIEW_REQUIRED
    assert plan.page_decisions[0].reason == RoutingReason.UNKNOWN_PAGE_TYPE


def test_high_risk_never_silently_native() -> None:
    router = DocumentRouter(OCREngineRegistry())
    plan = router.plan(
        _document(
            _page(
                page_type=PageType.DIGITAL_TEXT,
                needs_ocr=False,
                risk=RiskLevel.HIGH,
            )
        )
    )
    decision = plan.page_decisions[0]
    assert decision.action != RoutingAction.USE_NATIVE_TEXT
    assert decision.action == RoutingAction.REVIEW_REQUIRED


def test_deterministic_repeated_plans() -> None:
    registry = OCREngineRegistry()
    doc = _document(
        _page(number=1, page_type=PageType.DIGITAL_TEXT),
        _page(number=2, page_type=PageType.EMPTY),
        _page(number=3, page_type=PageType.SCANNED_IMAGE, needs_ocr=True),
    )
    router = DocumentRouter(registry)
    first = router.plan(doc)
    second = router.plan(doc)
    assert [d.model_dump() for d in first.page_decisions] == [
        d.model_dump() for d in second.page_decisions
    ]
    assert first.summary.model_dump() == second.summary.model_dump()


def test_routing_does_not_mutate_ir() -> None:
    doc = _document(_page(page_type=PageType.DIGITAL_TEXT))
    before = doc.model_dump()
    DocumentRouter(OCREngineRegistry()).plan(doc)
    assert doc.model_dump() == before


def test_test_engine_excluded_by_default() -> None:
    registry = OCREngineRegistry()
    registry.register(MockOCREngine())
    router = DocumentRouter(registry, allow_test_engines=False)
    plan = router.plan(
        _document(_page(page_type=PageType.SCANNED_IMAGE, needs_ocr=True, risk=RiskLevel.MEDIUM))
    )
    decision = plan.page_decisions[0]
    assert decision.action == RoutingAction.REVIEW_REQUIRED
    assert decision.reason == RoutingReason.TEST_ENGINE_ONLY
    assert decision.selected_engine_id is None


def test_test_engine_allowed_only_explicitly() -> None:
    registry = OCREngineRegistry()
    registry.register(MockOCREngine())
    router = DocumentRouter(registry, allow_test_engines=True)
    plan = router.plan(
        _document(_page(page_type=PageType.SCANNED_IMAGE, needs_ocr=True, risk=RiskLevel.MEDIUM))
    )
    decision = plan.page_decisions[0]
    assert decision.action == RoutingAction.RUN_OCR
    assert decision.selected_engine_id == MOCK_ENGINE_ID


def test_real_layout_engine_selected_for_mixed() -> None:
    registry = OCREngineRegistry()
    registry.register(_StubEngine("layout_engine", layout=True))
    router = DocumentRouter(registry)
    plan = router.plan(
        _document(_page(page_type=PageType.MIXED, needs_ocr=True, risk=RiskLevel.MEDIUM))
    )
    decision = plan.page_decisions[0]
    assert decision.action == RoutingAction.RUN_OCR
    assert decision.selected_engine_id == "layout_engine"
    assert decision.reason == RoutingReason.MIXED_PAGE_REQUIRES_OCR

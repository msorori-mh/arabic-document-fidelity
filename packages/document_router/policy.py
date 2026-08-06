"""Conservative OCR routing policy rules."""

from __future__ import annotations

from packages.document_model.enums import PageType, RiskLevel
from packages.document_model.models import PageModel
from packages.document_router.models import (
    PageRoutingDecision,
    RoutingAction,
    RoutingReason,
)
from packages.ocr_registry.registry import OCREngineRegistry

POLICY_VERSION = "1.0.0"


class RoutingPolicy:
    """Fail-closed page routing policy for OCR-ROUTER-01A."""

    def decide_page(
        self,
        page: PageModel,
        registry: OCREngineRegistry,
        *,
        allow_test_engines: bool = False,
    ) -> PageRoutingDecision:
        """Return a conservative routing decision for a single page."""
        if page.page_type == PageType.EMPTY:
            return PageRoutingDecision(
                page_number=page.page_number,
                page_type=page.page_type,
                needs_ocr=page.needs_ocr,
                risk_level=page.risk_level,
                action=RoutingAction.SKIP_EMPTY,
                reason=RoutingReason.EMPTY_PAGE,
            )

        if page.page_type == PageType.UNKNOWN:
            return PageRoutingDecision(
                page_number=page.page_number,
                page_type=page.page_type,
                needs_ocr=page.needs_ocr,
                risk_level=page.risk_level,
                action=RoutingAction.REVIEW_REQUIRED,
                reason=RoutingReason.UNKNOWN_PAGE_TYPE,
                warnings=["unknown page type fails closed; review required"],
            )

        # High-risk pages never silently pass as native-only.
        if page.risk_level == RiskLevel.HIGH:
            return self._decide_ocr_or_review(
                page,
                registry,
                allow_test_engines=allow_test_engines,
                primary_reason=RoutingReason.HIGH_RISK_PAGE,
                require_layout=page.page_type == PageType.MIXED,
            )

        if page.page_type == PageType.DIGITAL_TEXT and not page.needs_ocr:
            return PageRoutingDecision(
                page_number=page.page_number,
                page_type=page.page_type,
                needs_ocr=page.needs_ocr,
                risk_level=page.risk_level,
                action=RoutingAction.USE_NATIVE_TEXT,
                reason=RoutingReason.SUFFICIENT_NATIVE_TEXT,
            )

        if page.page_type == PageType.SCANNED_IMAGE:
            return self._decide_ocr_or_review(
                page,
                registry,
                allow_test_engines=allow_test_engines,
                primary_reason=RoutingReason.SCANNED_PAGE,
                require_layout=False,
            )

        if page.page_type == PageType.MIXED:
            return self._decide_ocr_or_review(
                page,
                registry,
                allow_test_engines=allow_test_engines,
                primary_reason=RoutingReason.MIXED_PAGE_REQUIRES_OCR,
                require_layout=True,
            )

        return PageRoutingDecision(
            page_number=page.page_number,
            page_type=page.page_type,
            needs_ocr=page.needs_ocr,
            risk_level=page.risk_level,
            action=RoutingAction.UNSUPPORTED,
            reason=RoutingReason.UNKNOWN_PAGE_TYPE,
            warnings=["page did not match a supported routing rule"],
        )

    def _decide_ocr_or_review(
        self,
        page: PageModel,
        registry: OCREngineRegistry,
        *,
        allow_test_engines: bool,
        primary_reason: RoutingReason,
        require_layout: bool,
    ) -> PageRoutingDecision:
        eligible = registry.list_eligible_engine_ids(
            allow_test_engines=allow_test_engines,
            require_layout=require_layout,
        )
        warnings: list[str] = []
        if primary_reason == RoutingReason.HIGH_RISK_PAGE:
            warnings.append("high-risk page cannot silently use native-only path")

        if eligible:
            selected, *fallback = eligible
            return PageRoutingDecision(
                page_number=page.page_number,
                page_type=page.page_type,
                needs_ocr=page.needs_ocr,
                risk_level=page.risk_level,
                action=RoutingAction.RUN_OCR,
                reason=primary_reason,
                selected_engine_id=selected,
                fallback_engine_ids=list(fallback),
                warnings=warnings,
            )

        reason = self._no_engine_reason(
            registry,
            allow_test_engines=allow_test_engines,
            require_layout=require_layout,
            primary_reason=primary_reason,
        )
        if reason == RoutingReason.TEST_ENGINE_ONLY:
            warnings.append("test-only OCR engines are excluded from default routing")
        else:
            warnings.append("no eligible non-test OCR engine is registered")
        if require_layout:
            warnings.append("mixed pages require an engine with supports_layout=true")

        return PageRoutingDecision(
            page_number=page.page_number,
            page_type=page.page_type,
            needs_ocr=page.needs_ocr,
            risk_level=page.risk_level,
            action=RoutingAction.REVIEW_REQUIRED,
            reason=reason,
            selected_engine_id=None,
            fallback_engine_ids=[],
            warnings=warnings,
            metadata={"policy_primary_reason": primary_reason.value},
        )

    @staticmethod
    def _no_engine_reason(
        registry: OCREngineRegistry,
        *,
        allow_test_engines: bool,
        require_layout: bool,
        primary_reason: RoutingReason,
    ) -> RoutingReason:
        """Choose reason when no eligible engine is available."""
        if primary_reason == RoutingReason.HIGH_RISK_PAGE:
            # Preserve high-risk signal when failing closed without an engine.
            test_only_present = any(
                d.test_only and (not require_layout or d.supports_layout)
                for d in registry.list_descriptors()
            )
            if test_only_present and not allow_test_engines:
                return RoutingReason.TEST_ENGINE_ONLY
            return RoutingReason.HIGH_RISK_PAGE

        test_only_present = any(
            d.test_only and (not require_layout or d.supports_layout)
            for d in registry.list_descriptors()
        )
        if test_only_present and not allow_test_engines:
            return RoutingReason.TEST_ENGINE_ONLY
        return RoutingReason.NO_ELIGIBLE_ENGINE

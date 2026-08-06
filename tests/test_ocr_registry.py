"""Tests for the OCR engine registry."""

from __future__ import annotations

import pytest

from packages.mock_ocr import MOCK_ENGINE_ID, MockOCREngine
from packages.ocr_contracts.errors import DuplicateEngineError, UnknownEngineError
from packages.ocr_contracts.models import (
    ExecutionMode,
    OCREngineDescriptor,
    OCRPageRequest,
    OCRPageResult,
)
from packages.ocr_registry import OCREngineRegistry


class _StubEngine:
    def __init__(self, engine_id: str, *, test_only: bool = False, layout: bool = False) -> None:
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


def test_register_and_lookup() -> None:
    registry = OCREngineRegistry()
    engine = _StubEngine("alpha")
    registry.register(engine)
    assert registry.get("alpha") is engine
    assert registry.is_registered("alpha")


def test_duplicate_rejection() -> None:
    registry = OCREngineRegistry()
    registry.register(_StubEngine("alpha"))
    with pytest.raises(DuplicateEngineError):
        registry.register(_StubEngine("alpha"))


def test_unknown_engine_error() -> None:
    registry = OCREngineRegistry()
    with pytest.raises(UnknownEngineError):
        registry.get("missing")


def test_stable_listing_order() -> None:
    registry = OCREngineRegistry()
    registry.register(_StubEngine("zeta"))
    registry.register(_StubEngine("alpha"))
    registry.register(_StubEngine("mu"))
    assert [d.engine_id for d in registry.list_descriptors()] == ["alpha", "mu", "zeta"]


def test_test_only_engine_not_production_available() -> None:
    registry = OCREngineRegistry()
    registry.register(MockOCREngine())
    assert registry.is_available(MOCK_ENGINE_ID, allow_test_engines=False) is False
    assert registry.is_available(MOCK_ENGINE_ID, allow_test_engines=True) is True
    assert registry.list_eligible_engine_ids(allow_test_engines=False) == []
    assert registry.list_eligible_engine_ids(allow_test_engines=True) == [MOCK_ENGINE_ID]

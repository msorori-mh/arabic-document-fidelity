"""Mock OCR engine — tests only; no image analysis or OCR libraries."""

from __future__ import annotations

from packages.ocr_contracts.errors import OCREngineError
from packages.ocr_contracts.models import (
    ExecutionMode,
    OCREngineDescriptor,
    OCRPageRequest,
    OCRPageResult,
)

MOCK_ENGINE_ID = "mock_ocr_v1"


class MockOCREngine:
    """Deterministic fixture-driven OCR engine for unit/integration tests.

    Safety rules:
    - ``test_only=True`` and ``execution_mode=mock``
    - no network, no OCR libraries, no image analysis
    - does not fabricate text from input files
    - accepts only explicitly supplied fixture responses
    - refuses requests without a matching fixture
    """

    def __init__(
        self,
        fixtures: dict[tuple[str, int], OCRPageResult] | None = None,
    ) -> None:
        self._fixtures: dict[tuple[str, int], OCRPageResult] = dict(fixtures or {})
        self._descriptor = OCREngineDescriptor(
            engine_id=MOCK_ENGINE_ID,
            display_name="Mock OCR Engine",
            version="0.1.0",
            provider="arabic-document-fidelity",
            execution_mode=ExecutionMode.MOCK,
            supported_languages=["ar", "en"],
            supports_layout=True,
            supports_tables=False,
            supports_word_confidence=False,
            supports_block_confidence=False,
            requires_network=False,
            test_only=True,
        )

    @property
    def descriptor(self) -> OCREngineDescriptor:
        return self._descriptor

    def health_check(self) -> bool:
        """Mock engine is always locally available (no network)."""
        return True

    def set_fixture(self, document_id: str, page_number: int, result: OCRPageResult) -> None:
        """Register or replace a deterministic fixture response."""
        if result.engine_id != MOCK_ENGINE_ID:
            raise OCREngineError(
                f"mock fixture engine_id must be {MOCK_ENGINE_ID!r}, got {result.engine_id!r}"
            )
        self._fixtures[(document_id, page_number)] = result

    def process_page(self, request: OCRPageRequest) -> OCRPageResult:
        """Return a predefined fixture result; never invent OCR text."""
        key = (request.document_id, request.page_number)
        if key not in self._fixtures:
            raise OCREngineError(
                "MockOCREngine refuses execution without an explicit fixture "
                f"for document_id={request.document_id!r} page_number={request.page_number}"
            )

        result = self._fixtures[key].model_copy(deep=True)
        warnings = list(result.warnings)
        if "test_only: mock OCR result" not in warnings:
            warnings.append("test_only: mock OCR result")
        result.warnings = warnings

        notes = list(result.processing_metadata.notes)
        if "mock/test-only engine" not in notes:
            notes.append("mock/test-only engine")
        result.processing_metadata.notes = notes
        return result

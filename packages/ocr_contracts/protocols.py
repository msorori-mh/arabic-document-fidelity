"""Protocol defining the pluggable OCR engine interface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from packages.ocr_contracts.models import OCREngineDescriptor, OCRPageRequest, OCRPageResult


@runtime_checkable
class OCREngine(Protocol):
    """Provider-neutral OCR engine contract.

    Implementations must preserve logical text order (no Arabic string
    reversal / visual bidi conversion for stored ``text_raw``) and must not
    fabricate confidence scores.
    """

    @property
    def descriptor(self) -> OCREngineDescriptor:
        """Return the static engine descriptor."""

    def health_check(self) -> bool:
        """Return True when the engine is ready to process pages."""

    def process_page(self, request: OCRPageRequest) -> OCRPageResult:
        """Process a single page request and return structured OCR results."""

"""Provider-neutral OCR engine contract package."""

from packages.ocr_contracts.errors import (
    DuplicateEngineError,
    OCRContractError,
    OCREngineError,
    OCREngineUnavailableError,
    UnknownEngineError,
)
from packages.ocr_contracts.models import (
    CONTRACT_SCHEMA_VERSION,
    ExecutionMode,
    OCRBlockResult,
    OCREngineDescriptor,
    OCRPageRequest,
    OCRPageResult,
    OCRProcessingMetadata,
    RequestedFeature,
)
from packages.ocr_contracts.protocols import OCREngine

__all__ = [
    "CONTRACT_SCHEMA_VERSION",
    "DuplicateEngineError",
    "ExecutionMode",
    "OCRBlockResult",
    "OCRContractError",
    "OCREngine",
    "OCREngineDescriptor",
    "OCREngineError",
    "OCREngineUnavailableError",
    "OCRPageRequest",
    "OCRPageResult",
    "OCRProcessingMetadata",
    "RequestedFeature",
    "UnknownEngineError",
]

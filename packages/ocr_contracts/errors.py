"""Typed exceptions for the OCR contract and registry."""

from __future__ import annotations


class OCRContractError(Exception):
    """Base class for OCR contract and routing errors."""


class OCREngineError(OCRContractError):
    """Raised when an OCR engine fails to process a request."""


class OCREngineUnavailableError(OCREngineError):
    """Raised when an engine fails a health check or is unavailable."""


class DuplicateEngineError(OCRContractError):
    """Raised when registering an engine ID that already exists."""


class UnknownEngineError(OCRContractError):
    """Raised when looking up an engine ID that is not registered."""

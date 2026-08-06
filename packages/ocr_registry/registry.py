"""Deterministic in-memory OCR engine registry.

No dynamic package discovery, plugin path loading, or network calls.
"""

from __future__ import annotations

from packages.ocr_contracts.errors import DuplicateEngineError, UnknownEngineError
from packages.ocr_contracts.models import OCREngineDescriptor
from packages.ocr_contracts.protocols import OCREngine


class OCREngineRegistry:
    """Register and look up OCR engines by stable engine ID."""

    def __init__(self) -> None:
        self._engines: dict[str, OCREngine] = {}

    def register(self, engine: OCREngine) -> None:
        """Register an engine. Rejects duplicate ``engine_id`` values."""
        engine_id = engine.descriptor.engine_id
        if engine_id in self._engines:
            raise DuplicateEngineError(f"engine already registered: {engine_id}")
        self._engines[engine_id] = engine

    def get(self, engine_id: str) -> OCREngine:
        """Return a registered engine or raise :class:`UnknownEngineError`."""
        try:
            return self._engines[engine_id]
        except KeyError as exc:
            raise UnknownEngineError(f"unknown engine: {engine_id}") from exc

    def list_descriptors(self) -> list[OCREngineDescriptor]:
        """Return descriptors sorted by ``engine_id`` for stable listing."""
        return [self._engines[engine_id].descriptor for engine_id in sorted(self._engines.keys())]

    def is_registered(self, engine_id: str) -> bool:
        """Return True when ``engine_id`` is registered."""
        return engine_id in self._engines

    def is_available(self, engine_id: str, *, allow_test_engines: bool = False) -> bool:
        """Return True when the engine is registered, healthy, and eligible.

        Test-only engines are treated as unavailable unless
        ``allow_test_engines`` is True. This prevents Mock/test engines from
        being considered production-capable by default.
        """
        if engine_id not in self._engines:
            return False
        engine = self._engines[engine_id]
        descriptor = engine.descriptor
        if descriptor.test_only and not allow_test_engines:
            return False
        return engine.health_check()

    def list_eligible_engine_ids(
        self,
        *,
        allow_test_engines: bool = False,
        require_layout: bool = False,
    ) -> list[str]:
        """Return eligible engine IDs in stable sorted order."""
        eligible: list[str] = []
        for engine_id in sorted(self._engines.keys()):
            if not self.is_available(engine_id, allow_test_engines=allow_test_engines):
                continue
            descriptor = self._engines[engine_id].descriptor
            if require_layout and not descriptor.supports_layout:
                continue
            eligible.append(engine_id)
        return eligible

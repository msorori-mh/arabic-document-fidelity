"""Deterministic summary helpers for diagnosis output."""

from __future__ import annotations

from collections import Counter
from typing import Any

from packages.document_model.enums import Direction, PageType
from packages.document_model.models import DocumentModel


def summarize_document(document: DocumentModel) -> dict[str, Any]:
    """Build a plain dict summary suitable for text and JSON reporting."""
    page_type_counts = Counter(page.page_type.value for page in document.pages)
    ocr_pages = [page.page_number for page in document.pages if page.needs_ocr]

    arabic_pages = [page.page_number for page in document.pages if "ar" in page.language_hints]
    rtl_blocks = sum(
        1 for page in document.pages for block in page.blocks if block.direction == Direction.RTL
    )
    mixed_blocks = sum(
        1 for page in document.pages for block in page.blocks if block.direction == Direction.MIXED
    )

    all_warnings: list[str] = list(document.warnings)
    for page in document.pages:
        for warning in page.warnings:
            all_warnings.append(f"page {page.page_number}: {warning}")

    return {
        "filename": document.source_filename,
        "document_id": document.document_id,
        "schema_version": document.schema_version,
        "source_sha256": document.source_sha256,
        "page_count": document.page_count,
        "page_type_counts": dict(sorted(page_type_counts.items())),
        "pages_requiring_ocr": ocr_pages,
        "arabic_page_numbers": arabic_pages,
        "rtl_block_count": rtl_blocks,
        "mixed_direction_block_count": mixed_blocks,
        "warnings": all_warnings,
        "processing_duration_ms": document.processing_metadata.duration_ms,
        "empty_page_count": page_type_counts.get(PageType.EMPTY.value, 0),
    }


def format_summary_text(summary: dict[str, Any]) -> str:
    """Render a human-readable diagnosis summary."""
    page_types = summary.get("page_type_counts") or {}
    page_type_lines = (
        "\n".join(f"  - {name}: {count}" for name, count in page_types.items())
        if page_types
        else "  (none)"
    )
    warnings = summary.get("warnings") or []
    warning_lines = "\n".join(f"  - {item}" for item in warnings) if warnings else "  (none)"
    ocr_pages = summary.get("pages_requiring_ocr") or []
    arabic_pages = summary.get("arabic_page_numbers") or []

    return "\n".join(
        [
            "Arabic Document Fidelity — Diagnosis Summary",
            "=" * 48,
            f"Filename:              {summary.get('filename')}",
            f"Document ID:           {summary.get('document_id')}",
            f"Schema version:        {summary.get('schema_version')}",
            f"SHA-256:               {summary.get('source_sha256')}",
            f"Page count:            {summary.get('page_count')}",
            "Page-type counts:",
            page_type_lines,
            f"Pages requiring OCR:   {ocr_pages if ocr_pages else '(none)'}",
            f"Arabic pages:          {arabic_pages if arabic_pages else '(none)'}",
            f"RTL block count:       {summary.get('rtl_block_count')}",
            f"Mixed-direction blocks:{summary.get('mixed_direction_block_count')}",
            f"Processing duration:   {summary.get('processing_duration_ms')} ms",
            "Warnings:",
            warning_lines,
            "",
        ]
    )

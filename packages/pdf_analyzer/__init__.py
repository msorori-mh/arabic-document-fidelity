"""PDF analyzer package: read-only native PDF inspection without OCR."""

from packages.pdf_analyzer.analyzer import PdfAnalyzer, analyze_pdf
from packages.pdf_analyzer.hashing import sha256_file
from packages.pdf_analyzer.heuristics import (
    classify_page_type,
    detect_arabic_chars,
    infer_direction,
)

__all__ = [
    "PdfAnalyzer",
    "analyze_pdf",
    "classify_page_type",
    "detect_arabic_chars",
    "infer_direction",
    "sha256_file",
]

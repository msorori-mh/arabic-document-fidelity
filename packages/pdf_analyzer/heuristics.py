"""Conservative heuristics for Arabic PDF page and text analysis.

Limitations (foundation package):
- Table detection is NOT implemented; ``has_tables`` stays False unless a future
  heuristic confidently marks a table.
- Multi-column detection uses a simple x-clustering heuristic and may mislabel
  complex layouts; uncertain cases remain unlabeled.
- Coverage ratios are approximate (union of block/image bboxes vs page area).
- Direction inference uses Unicode script inventory only — no bidi algorithm,
  reshaping, or visual reordering is applied to stored text.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from packages.document_model.enums import Direction, PageType, RiskLevel

# Arabic script block (basic Arabic + presentation forms commonly in PDFs)
_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
_LATIN_RE = re.compile(r"[A-Za-z]")

# Coverage thresholds for conservative page classification
_TEXT_DIGITAL_MIN = 0.02
_TEXT_CHAR_DIGITAL_MIN = 8
_IMAGE_SCAN_MIN = 0.45
_TEXT_SCAN_MAX = 0.01
_MIXED_TEXT_MIN = 0.01
_MIXED_IMAGE_MIN = 0.15


def detect_arabic_chars(text: str) -> bool:
    """Return True if ``text`` contains at least one Arabic Unicode character."""
    return _ARABIC_RE.search(text) is not None


def count_script_chars(text: str) -> tuple[int, int]:
    """Return ``(arabic_count, latin_count)`` for direction heuristics."""
    arabic = len(_ARABIC_RE.findall(text))
    latin = len(_LATIN_RE.findall(text))
    return arabic, latin


def infer_direction(text: str) -> Direction:
    """Infer likely text direction from character inventory.

    Does not reshape, reverse, or apply the Unicode Bidirectional Algorithm.
    Stored ``text_raw`` remains logical PDF extraction order.
    """
    arabic, latin = count_script_chars(text)
    if arabic == 0 and latin == 0:
        return Direction.UNKNOWN
    if arabic > 0 and latin > 0:
        return Direction.MIXED
    if arabic > 0:
        return Direction.RTL
    return Direction.LTR


def language_hints_from_text(text: str) -> list[str]:
    """Return sorted language hint tags based on character presence."""
    hints: list[str] = []
    arabic, latin = count_script_chars(text)
    if arabic > 0:
        hints.append("ar")
    if latin > 0:
        hints.append("en")
    return hints


def classify_page_type(
    *,
    text_coverage_ratio: float,
    image_coverage_ratio: float,
    text_char_count: int,
    image_count: int,
) -> tuple[PageType, RiskLevel, list[str]]:
    """Classify a page conservatively; prefer UNKNOWN over overconfident labels.

    Returns ``(page_type, risk_level, warnings)``.
    """
    warnings: list[str] = []

    if text_char_count == 0 and image_count == 0 and text_coverage_ratio < 0.001:
        return PageType.EMPTY, RiskLevel.LOW, warnings

    if (
        image_coverage_ratio < _MIXED_IMAGE_MIN
        and text_char_count > 0
        and (text_coverage_ratio >= _TEXT_DIGITAL_MIN or text_char_count >= _TEXT_CHAR_DIGITAL_MIN)
    ):
        risk = RiskLevel.LOW if text_coverage_ratio >= 0.05 else RiskLevel.MEDIUM
        return PageType.DIGITAL_TEXT, risk, warnings

    if (
        image_coverage_ratio >= _IMAGE_SCAN_MIN
        and text_coverage_ratio <= _TEXT_SCAN_MAX
        and text_char_count == 0
    ):
        return PageType.SCANNED_IMAGE, RiskLevel.MEDIUM, warnings

    if (
        text_coverage_ratio >= _MIXED_TEXT_MIN
        and image_coverage_ratio >= _MIXED_IMAGE_MIN
        and text_char_count > 0
        and image_count > 0
    ):
        warnings.append(
            "mixed page classification is heuristic; OCR may still be needed for image regions"
        )
        return PageType.MIXED, RiskLevel.HIGH, warnings

    # Near-empty with tiny artifacts
    if text_char_count == 0 and image_count == 0:
        return PageType.EMPTY, RiskLevel.MEDIUM, warnings

    warnings.append("page type could not be classified confidently; labeled unknown")
    return PageType.UNKNOWN, RiskLevel.HIGH, warnings


def needs_ocr_estimate(page_type: PageType, text_char_count: int) -> bool:
    """Estimate whether OCR will be required for usable text extraction."""
    if page_type in (PageType.SCANNED_IMAGE, PageType.MIXED):
        return True
    return page_type == PageType.UNKNOWN and text_char_count == 0


def approximate_multi_column(
    bboxes: Sequence[tuple[float, float, float, float]],
    page_width: float,
) -> tuple[bool, list[str]]:
    """Conservative multi-column heuristic via x-midpoint clustering.

    Returns ``(has_multiple_columns, warnings)``. Uncertain layouts stay False
    with a warning rather than a false positive.
    """
    warnings: list[str] = []
    if page_width <= 0 or len(bboxes) < 4:
        return False, warnings

    midpoints = sorted((x0 + x1) / 2.0 for x0, _y0, x1, _y1 in bboxes)
    gap_threshold = page_width * 0.18
    clusters = 1
    for prev, curr in zip(midpoints, midpoints[1:], strict=False):
        if curr - prev >= gap_threshold:
            clusters += 1

    if clusters >= 2:
        warnings.append("multi-column detection is heuristic and may mislabel complex layouts")
        return True, warnings
    return False, warnings


def clamp_ratio(value: float) -> float:
    """Clamp a coverage ratio into ``[0.0, 1.0]``."""
    return max(0.0, min(1.0, value))

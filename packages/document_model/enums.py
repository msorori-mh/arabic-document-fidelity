"""Enumerations for the Arabic Document Intermediate Representation."""

from enum import StrEnum


class PageType(StrEnum):
    """Conservative classification of a PDF page's content nature."""

    DIGITAL_TEXT = "digital_text"
    SCANNED_IMAGE = "scanned_image"
    MIXED = "mixed"
    EMPTY = "empty"
    UNKNOWN = "unknown"


class BlockType(StrEnum):
    """Structural role of an extracted content block."""

    PARAGRAPH = "paragraph"
    HEADING = "heading"
    TABLE = "table"
    IMAGE = "image"
    HEADER = "header"
    FOOTER = "footer"
    LIST = "list"
    UNKNOWN = "unknown"


class Direction(StrEnum):
    """Likely text direction inferred from character inventory."""

    RTL = "rtl"
    LTR = "ltr"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class RiskLevel(StrEnum):
    """Heuristic confidence / risk label for analysis quality."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"

"""Read-only PDF analyzer using PyMuPDF (fitz).

Produces a versioned :class:`~packages.document_model.models.DocumentModel`
without OCR, text reshaping, or bidirectional visual conversion.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import fitz

from packages.document_model.enums import BlockType, Direction, RiskLevel
from packages.document_model.models import (
    SCHEMA_VERSION,
    BlockModel,
    BoundingBox,
    DocumentModel,
    PageModel,
    ProcessingMetadata,
)
from packages.pdf_analyzer.hashing import sha256_file
from packages.pdf_analyzer.heuristics import (
    approximate_multi_column,
    clamp_ratio,
    classify_page_type,
    detect_arabic_chars,
    infer_direction,
    language_hints_from_text,
    needs_ocr_estimate,
)

ANALYZER_VERSION = "0.1.0"


def analyze_pdf(path: Path | str) -> DocumentModel:
    """Analyze a PDF file and return a :class:`DocumentModel`."""
    return PdfAnalyzer().analyze(Path(path))


class PdfAnalyzer:
    """Deterministic, read-only PDF inspector."""

    def analyze(self, path: Path) -> DocumentModel:
        """Open ``path``, inspect pages, and return a structured IR document."""
        started = time.perf_counter()
        warnings: list[str] = []

        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        source_sha256 = sha256_file(path)
        document_id = f"doc_{source_sha256[:16]}"

        try:
            doc = fitz.open(path)
        except Exception as exc:  # noqa: BLE001 - surface as analysis failure
            raise ValueError(f"Unable to open PDF: {path}") from exc

        try:
            if doc.is_encrypted and not doc.is_unlocked:
                raise ValueError(f"PDF is encrypted and locked: {path}")

            pages: list[PageModel] = []
            for index in range(doc.page_count):
                page = doc.load_page(index)
                pages.append(self._analyze_page(page, page_number=index + 1))

            if doc.page_count == 0:
                warnings.append("PDF contains zero pages")

            duration_ms = (time.perf_counter() - started) * 1000.0
            try:
                pymupdf_version: str | None = str(fitz.version[0])
            except Exception:  # noqa: BLE001
                bind = getattr(fitz, "VersionBind", None)
                pymupdf_version = str(bind) if bind is not None else None

            metadata = ProcessingMetadata(
                analyzer_name="pdf_analyzer",
                analyzer_version=ANALYZER_VERSION,
                duration_ms=round(duration_ms, 3),
                pymupdf_version=pymupdf_version,
                notes=[
                    "Native text extraction only; OCR not performed.",
                    "Arabic text stored as logical extraction; no reshape/bidi applied.",
                    "Table detection is not implemented in this foundation package.",
                ],
            )

            return DocumentModel(
                schema_version=SCHEMA_VERSION,
                document_id=document_id,
                source_filename=path.name,
                source_sha256=source_sha256,
                page_count=doc.page_count,
                pages=pages,
                processing_metadata=metadata,
                warnings=warnings,
            )
        finally:
            doc.close()

    def _analyze_page(self, page: fitz.Page, *, page_number: int) -> PageModel:
        page_warnings: list[str] = []
        rect = page.rect
        width = float(rect.width)
        height = float(rect.height)
        page_area = max(width * height, 1.0)
        rotation = int(page.rotation)

        text_blocks = self._extract_text_blocks(page, page_number=page_number)
        image_blocks, image_area = self._extract_image_blocks(page, page_number=page_number)

        text_area = sum(
            max(0.0, b.bbox.x1 - b.bbox.x0) * max(0.0, b.bbox.y1 - b.bbox.y0) for b in text_blocks
        )
        text_coverage = clamp_ratio(text_area / page_area)
        image_coverage = clamp_ratio(image_area / page_area)

        all_text = "\n".join(b.text_raw for b in text_blocks if b.text_raw)
        text_char_count = sum(1 for ch in all_text if not ch.isspace())
        language_hints = language_hints_from_text(all_text)

        page_type, risk_level, type_warnings = classify_page_type(
            text_coverage_ratio=text_coverage,
            image_coverage_ratio=image_coverage,
            text_char_count=text_char_count,
            image_count=len(image_blocks),
        )
        page_warnings.extend(type_warnings)

        multi_col, multi_warnings = approximate_multi_column(
            [(b.bbox.x0, b.bbox.y0, b.bbox.x1, b.bbox.y1) for b in text_blocks],
            width,
        )
        page_warnings.extend(multi_warnings)

        if detect_arabic_chars(all_text):
            page_warnings.append(
                "Arabic characters detected; logical order preserved without reshape"
            )

        blocks = sorted(
            [*text_blocks, *image_blocks],
            key=lambda b: (b.bbox.y0, b.bbox.x0, b.block_id),
        )
        for order, block in enumerate(blocks):
            block.reading_order = order

        has_tables = False
        page_warnings.append("table detection not implemented; has_tables remains false")

        return PageModel(
            page_number=page_number,
            width=width,
            height=height,
            rotation=rotation,
            page_type=page_type,
            language_hints=language_hints,
            text_coverage_ratio=round(text_coverage, 6),
            image_coverage_ratio=round(image_coverage, 6),
            needs_ocr=needs_ocr_estimate(page_type, text_char_count),
            has_tables=has_tables,
            has_images=len(image_blocks) > 0,
            has_multiple_columns=multi_col,
            risk_level=risk_level,
            blocks=blocks,
            warnings=page_warnings,
        )

    def _extract_text_blocks(self, page: fitz.Page, *, page_number: int) -> list[BlockModel]:
        blocks: list[BlockModel] = []
        raw: list[Any] = page.get_text("blocks")
        # Each block: (x0, y0, x1, y1, text, block_no, block_type)
        # block_type 0 = text, 1 = image
        text_entries: list[tuple[float, float, float, float, str, int]] = []
        for entry in raw:
            if len(entry) < 7:
                continue
            x0, y0, x1, y1, text, block_no, block_type = entry[:7]
            if int(block_type) != 0:
                continue
            text_str = str(text).replace("\x00", "").strip("\n")
            if not text_str.strip():
                continue
            text_entries.append(
                (float(x0), float(y0), float(x1), float(y1), text_str, int(block_no))
            )

        text_entries.sort(key=lambda e: (e[1], e[0], e[5]))

        for idx, (x0, y0, x1, y1, text_str, block_no) in enumerate(text_entries):
            direction = infer_direction(text_str)
            block_type = self._guess_block_type(
                text_str, y0=y0, page_height=float(page.rect.height)
            )
            risk = RiskLevel.LOW if direction != Direction.UNKNOWN else RiskLevel.MEDIUM
            blocks.append(
                BlockModel(
                    block_id=f"p{page_number}_t{idx}_{block_no}",
                    block_type=block_type,
                    text_raw=text_str,
                    direction=direction,
                    bbox=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1),
                    reading_order=idx,
                    confidence=None,
                    source_engine="pymupdf_native",
                    risk_level=risk,
                    metadata={
                        "pymupdf_block_no": block_no,
                        "contains_arabic": detect_arabic_chars(text_str),
                    },
                )
            )
        return blocks

    def _extract_image_blocks(
        self, page: fitz.Page, *, page_number: int
    ) -> tuple[list[BlockModel], float]:
        blocks: list[BlockModel] = []
        total_area = 0.0
        images = page.get_images(full=True)
        image_info = page.get_image_info(xrefs=True)

        for idx, info in enumerate(image_info):
            bbox = info.get("bbox")
            xref = int(info.get("xref") or 0)
            if bbox is None:
                continue
            x0, y0, x1, y1 = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
            area = max(0.0, x1 - x0) * max(0.0, y1 - y0)
            total_area += area
            blocks.append(
                BlockModel(
                    block_id=f"p{page_number}_img{idx}_{xref}",
                    block_type=BlockType.IMAGE,
                    text_raw="",
                    direction=Direction.UNKNOWN,
                    bbox=BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1),
                    reading_order=idx,
                    confidence=None,
                    source_engine="pymupdf_native",
                    risk_level=RiskLevel.MEDIUM,
                    metadata={
                        "xref": xref,
                        "width": info.get("width"),
                        "height": info.get("height"),
                    },
                )
            )

        # Fallback when image_info lacks bboxes but get_images found one image.
        if not blocks and images and len(images) == 1:
            rect = page.rect
            total_area = float(rect.width) * float(rect.height)
            blocks.append(
                BlockModel(
                    block_id=f"p{page_number}_img0_approx",
                    block_type=BlockType.IMAGE,
                    text_raw="",
                    direction=Direction.UNKNOWN,
                    bbox=BoundingBox(
                        x0=float(rect.x0),
                        y0=float(rect.y0),
                        x1=float(rect.x1),
                        y1=float(rect.y1),
                    ),
                    reading_order=0,
                    confidence=None,
                    source_engine="pymupdf_native",
                    risk_level=RiskLevel.HIGH,
                    metadata={
                        "approx_full_page": True,
                        "note": "bbox approximated; image_info unavailable",
                    },
                )
            )

        return blocks, total_area

    @staticmethod
    def _guess_block_type(text: str, *, y0: float, page_height: float) -> BlockType:
        """Conservative structural guess; defaults to paragraph/unknown."""
        stripped = text.strip()
        if not stripped:
            return BlockType.UNKNOWN

        # Header / footer bands (top/bottom 8% of page)
        if page_height > 0:
            top_band = page_height * 0.08
            bottom_band = page_height * 0.92
            short = len(stripped) < 80
            if y0 <= top_band and short:
                return BlockType.HEADER
            if y0 >= bottom_band and short:
                return BlockType.FOOTER

        lines = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
        if len(lines) >= 2 and all(
            ln.startswith(("-", "•", "*", "–")) or (ln[:2].isdigit() and "." in ln[:4])
            for ln in lines
        ):
            return BlockType.LIST

        if len(lines) == 1 and len(stripped) <= 80 and not stripped.endswith((".", "。", "؟", "?")):
            return BlockType.HEADING

        return BlockType.PARAGRAPH

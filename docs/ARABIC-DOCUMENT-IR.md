# Arabic Document Intermediate Representation (IR)

**Schema version:** `1.0.0`

Stable, versioned JSON-serializable model for Arabic (and bilingual) PDF
analysis. Foundation-01 populates the IR from native PDF extraction only.

## Design rules

1. Schema is versioned via `schema_version`.
2. Models forbid unexpected fields (`extra = "forbid"`).
3. Enumerations serialize as stable lowercase strings.
4. `text_raw` is **logical** extraction text — no reshape, no manual reverse,
   no visual bidi conversion for storage.
5. `confidence` is optional and must not be fabricated; Foundation-01 leaves it
   `null` for native blocks.
6. Warnings are preferred over silent failure.

## Enumerations

### PageType

| Value | Meaning |
|-------|---------|
| `digital_text` | Meaningful native text; image coverage low |
| `scanned_image` | Large image coverage; little/no native text |
| `mixed` | Both native text and substantial imagery |
| `empty` | No meaningful text or images |
| `unknown` | Heuristics inconclusive |

### BlockType

`paragraph`, `heading`, `table`, `image`, `header`, `footer`, `list`, `unknown`

> Table detection is **not** implemented in Foundation-01. Blocks are not labeled
> `table` by the analyzer yet; `has_tables` remains `false` with a warning.

### Direction

`rtl`, `ltr`, `mixed`, `unknown` — inferred from Unicode script inventory only.

### RiskLevel

`low`, `medium`, `high`, `unknown`

## DocumentModel

| Field | Type | Notes |
|-------|------|-------|
| `schema_version` | string | Currently `1.0.0` |
| `document_id` | string | Derived from SHA-256 prefix |
| `source_filename` | string | Basename of input |
| `source_sha256` | string | 64-char lowercase hex |
| `page_count` | int | ≥ 0 |
| `pages` | PageModel[] | Ordered by page number |
| `processing_metadata` | object | Analyzer name/version/duration |
| `warnings` | string[] | Document-level warnings |

## PageModel

| Field | Type | Notes |
|-------|------|-------|
| `page_number` | int | 1-based |
| `width` / `height` | float | Page dimensions |
| `rotation` | int | PDF rotation |
| `page_type` | PageType | Conservative class |
| `language_hints` | string[] | e.g. `ar`, `en` |
| `text_coverage_ratio` | float | 0–1 approximate |
| `image_coverage_ratio` | float | 0–1 approximate |
| `needs_ocr` | bool | Heuristic estimate |
| `has_tables` | bool | Always false in Foundation-01 |
| `has_images` | bool | |
| `has_multiple_columns` | bool | Heuristic; may warn |
| `risk_level` | RiskLevel | |
| `blocks` | BlockModel[] | Reading-order sorted |
| `warnings` | string[] | |

## BlockModel

| Field | Type | Notes |
|-------|------|-------|
| `block_id` | string | Stable within a document analysis |
| `block_type` | BlockType | Conservative guess |
| `text_raw` | string | Logical text; empty for images |
| `direction` | Direction | |
| `bbox` | `{x0,y0,x1,y1}` | Page coordinates |
| `reading_order` | int | ≥ 0, deterministic |
| `confidence` | float \| null | null in Foundation-01 |
| `source_engine` | string | `pymupdf_native` |
| `risk_level` | RiskLevel | |
| `metadata` | object | Engine-specific extras |

## ProcessingMetadata

| Field | Type |
|-------|------|
| `analyzer_name` | string |
| `analyzer_version` | string |
| `processed_at` | ISO-8601 datetime (UTC) |
| `duration_ms` | float |
| `pymupdf_version` | string \| null |
| `notes` | string[] |

## JSON stability

- Enum values are stable strings.
- Coverage ratios are rounded to 6 decimal places by the analyzer.
- `document_id` is `doc_{sha256[:16]}`.
- Repeated analysis of the same file yields the same structural fields
  (`source_sha256`, block ids, reading order, page types). `processed_at` and
  `duration_ms` vary by run.

## Example (abridged)

```json
{
  "schema_version": "1.0.0",
  "document_id": "doc_abcdef0123456789",
  "source_filename": "sample.pdf",
  "source_sha256": "ab...64 hex...",
  "page_count": 1,
  "pages": [
    {
      "page_number": 1,
      "width": 595.0,
      "height": 842.0,
      "rotation": 0,
      "page_type": "digital_text",
      "language_hints": ["ar"],
      "text_coverage_ratio": 0.042,
      "image_coverage_ratio": 0.0,
      "needs_ocr": false,
      "has_tables": false,
      "has_images": false,
      "has_multiple_columns": false,
      "risk_level": "low",
      "blocks": [],
      "warnings": []
    }
  ],
  "processing_metadata": {
    "analyzer_name": "pdf_analyzer",
    "analyzer_version": "0.1.0",
    "duration_ms": 12.5,
    "notes": []
  },
  "warnings": []
}
```

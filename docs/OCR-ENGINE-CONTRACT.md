# OCR Engine Contract

**Contract schema version:** `1.0.0`

Provider-neutral abstraction for OCR engines used by Arabic Document Fidelity.

## Purpose

Decouple document routing from any specific OCR vendor. Engines implement a
small synchronous interface and exchange versioned Pydantic models.

## Engine abstraction

```text
OCREngine (Protocol)
  ├── descriptor: OCREngineDescriptor
  ├── health_check() -> bool
  └── process_page(OCRPageRequest) -> OCRPageResult
```

### OCREngineDescriptor

| Field | Notes |
|-------|-------|
| `engine_id` | Stable unique ID |
| `display_name` | Human label |
| `version` | Engine package/version string |
| `provider` | Vendor or local package name |
| `execution_mode` | `local` \| `cloud` \| `mock` |
| `supported_languages` | Sorted unique tags (e.g. `ar`, `en`) |
| `supports_layout` | Required for mixed-page OCR routing |
| `supports_tables` | Capability flag only |
| `supports_word_confidence` / `supports_block_confidence` | Capability flags |
| `requires_network` | Must be `false` for local/mock engines |
| `test_only` | When true, excluded from default routing |

## Request / result models

- `OCRPageRequest` — page identity, dimensions, optional `image_path` /
  `image_ref`, language hints, requested features, metadata.
- `OCRBlockResult` — block text, type, direction, bbox, reading order,
  optional confidence, `source_engine`.
- `OCRPageResult` — page blocks, optional `page_confidence`, warnings,
  processing metadata.

Unexpected fields are forbidden (`extra = "forbid"`).

## Logical Arabic text rules

1. `text_raw` stores **logical** text only.
2. Engines must **not** reverse Arabic strings for storage.
3. Engines must **not** apply visual bidi / reshape conversion for stored text.
4. Direction may be tagged (`rtl` / `ltr` / `mixed` / `unknown`) without
   mutating stored character order.

## Confidence rules

- Confidence is optional (`null` allowed).
- Confidence must not be fabricated.
- When present, values must be in `[0.0, 1.0]`.

## Test-only behavior

Engines with `test_only=true` (including Mock OCR) are:

- registerable in the registry for tests;
- **not** treated as production-capable by default;
- selectable only when a router is constructed with `allow_test_engines=True`.

## Errors

Typed exceptions in `packages.ocr_contracts.errors`:

- `OCRContractError`
- `OCREngineError`
- `OCREngineUnavailableError`
- `DuplicateEngineError`
- `UnknownEngineError`

## Future integration boundary

| Future engine | Boundary |
|---------------|----------|
| PaddleOCR (local) | Implement `OCREngine`; `execution_mode=local`; `requires_network=false` |
| Tesseract (local) | Same local boundary |
| Cloud OCR (Mistral/Gemini/etc.) | Separate engine package; `execution_mode=cloud`; never implied by this contract package |

OCR-ROUTER-01A ships the contract only. It does **not** integrate PaddleOCR,
Tesseract, or any cloud OCR API.

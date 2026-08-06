# Architecture

## Current pipeline (through OCR-ROUTER-01A)

```text
PDF input
  → native PDF analyzer (PyMuPDF, read-only)
  → Arabic Document IR (versioned Pydantic models)
  → OCR routing plan (sidecar; IR unchanged)
  → future OCR execution (not implemented in 01A)
```

Diagnosis CLI still emits `diagnosis.json` + `summary.txt`.
Plan-OCR CLI emits `diagnosis.json` + `routing-plan.json` + `routing-summary.txt`.

### PDF input

Local filesystem PDF. SHA-256 identity; encrypted/locked PDFs fail closed.

### Native PDF analyzer

`packages/pdf_analyzer` inspects pages for native text/images, coverage,
conservative page types, OCR-need estimates, Arabic/direction hints, and
deterministic reading order. No OCR execution.

### Arabic Document IR

`packages/document_model` — schema `1.0.0`. See [`ARABIC-DOCUMENT-IR.md`](ARABIC-DOCUMENT-IR.md).

### OCR routing plan

`packages/document_router` consumes IR fields and an `OCREngineRegistry` to
produce a `DocumentRoutingPlan` sidecar. Default routing excludes test-only
engines. See [`OCR-ROUTER-01A.md`](OCR-ROUTER-01A.md).

### Future OCR execution

Not implemented. A later package may invoke eligible `OCREngine` implementations
for `run_ocr` decisions only.

## Component boundaries

| Component | Status |
|-----------|--------|
| OCR engine contract + registry | Implemented (01A) |
| Mock OCR (tests only) | Implemented (01A) |
| Document router (plan only) | Implemented (01A) |
| Real OCR engines (Paddle/Tesseract/cloud) | **Not** implemented |
| DOCX compiler | Future |
| Round-trip validator | Future |
| Visual review studio | Future |

## Design principles

1. **Deterministic** — same inputs → same structural plans (timestamps aside).
2. **Conservative** — prefer `review_required` / `unknown` over overconfidence.
3. **Logical text** — never reverse Arabic for storage; no visual bidi conversion.
4. **No fabricated confidence** — `null` unless a real score exists.
5. **Local-first** — no external services in current packages.
6. **Fail closed** — high-risk and unknown pages never silently pass as native-only.

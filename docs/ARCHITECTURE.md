# Architecture — Foundation-01

## Current pipeline

```text
PDF input
    → PDF analyzer (PyMuPDF, read-only)
    → Arabic Document IR (versioned Pydantic models)
    → diagnosis output (diagnosis.json + summary.txt)
```

### PDF input

Local filesystem PDF. The analyzer computes SHA-256 of the source bytes and
opens the file with PyMuPDF. Encrypted/locked PDFs fail with a clear error.

### PDF analyzer

`packages/pdf_analyzer` inspects each page:

- native text blocks and bounding boxes
- embedded images and approximate coverage
- conservative page-type classification
- OCR-need estimate (heuristic only)
- Arabic character detection and RTL/LTR/mixed direction tags
- deterministic reading-order indices

No OCR, no network, no text reshaping, no visual bidi conversion of stored text.

### Arabic Document IR

`packages/document_model` defines `DocumentModel` / `PageModel` / `BlockModel`
with schema version `1.0.0`. See [`ARABIC-DOCUMENT-IR.md`](ARABIC-DOCUMENT-IR.md).

### Diagnosis output

The CLI writes only under the selected `--output` directory:

- `diagnosis.json` — full IR plus summary dict
- `summary.txt` — human-readable aggregates

## Future boundaries

| Component | Boundary |
|-----------|----------|
| **OCR engines** | Separate package; consume page images / regions; write OCR blocks into IR with `source_engine` tags. Not invoked by Foundation-01. |
| **Document router** | Chooses digital-only vs OCR vs hybrid based on page_type / needs_ocr / risk. Lives above the analyzer. |
| **DOCX compiler** | Reads IR only; emits DOCX. Must not re-parse PDF ad hoc. |
| **Round-trip validator** | Compares source PDF signals, IR, and compiled DOCX for fidelity metrics. |
| **Visual review studio** | UI for humans to inspect risky pages/blocks; reads IR + renders; does not replace the IR contract. |

## Design principles

1. **Deterministic** — same bytes → same structural diagnosis (timestamps/duration aside).
2. **Conservative** — prefer `unknown` / warnings over overconfident labels.
3. **Logical text** — store extraction order; do not reverse Arabic strings.
4. **No fabricated confidence** — `confidence` is `null` unless a real score exists.
5. **Local-first** — no external services in this foundation package.

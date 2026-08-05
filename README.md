# Arabic Document Fidelity

Local-first foundation for analyzing Arabic PDF documents and representing them
as a **stable intermediate document model** (Arabic Document IR).

This repository currently ships **Foundation-01**: read-only PDF inspection,
conservative page classification, and a diagnosis CLI. It does **not** perform
OCR, call cloud APIs, or produce editable DOCX output.

## Product purpose

Arabic Document Fidelity aims to preserve layout and reading fidelity when
processing Arabic (and bilingual) documents — from PDF intake through
structured IR, optional OCR routing, DOCX compilation, and round-trip
validation. Foundation-01 establishes the IR and the native-PDF analyzer only.

## Current foundation scope (Foundation-01)

| Included | Not included |
|----------|--------------|
| Versioned Arabic Document IR (Pydantic v2) | OCR engines |
| PyMuPDF native text/image inspection | Cloud APIs / LLMs |
| Conservative page-type heuristics | Authentication / Supabase |
| Local CLI `diagnose` | Payments / frontend UI |
| Benchmark manifest skeleton | Production deployment |
| Unit and integration tests | Automatic text correction |

## Installation

Requires **Python 3.11+**.

```powershell
cd c:\projects\arabic-document-fidelity
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## CLI usage

```powershell
python -m apps.cli diagnose --input sample.pdf --output outputs\sample
```

Produces:

```text
outputs/sample/
  diagnosis.json
  summary.txt
```

Exit codes: `0` success; non-zero for missing/invalid input or unrecoverable analysis errors.

## Test commands

```powershell
ruff check .
ruff format --check .
mypy .
pytest
```

## Privacy warning

Do **not** commit private, confidential, or sensitive PDFs. Benchmark sources
must be public, synthetic, or anonymized. See `benchmark/README.md`.

## Explicit non-goals (this package)

- No OCR (PaddleOCR, Tesseract, or proprietary engines)
- No LLM or vision-API “correction”
- No Arabic reshape / visual bidi conversion of stored logical text
- No FastAPI / web UI / auth / database
- No claim of production readiness

## Roadmap (summary)

1. **Foundation-01** (this package) — IR + native PDF analyzer + CLI
2. **OCR package** — pluggable engines behind a router; IR enrichment
3. **Document router** — choose digital vs OCR vs hybrid paths
4. **DOCX compiler** — emit editable Word from IR
5. **Round-trip validator** — fidelity checks PDF ↔ IR ↔ DOCX
6. **Visual review studio** — human review of risky pages/blocks

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/ARABIC-DOCUMENT-IR.md`](docs/ARABIC-DOCUMENT-IR.md)
- [`docs/BENCHMARK-GUIDE.md`](docs/BENCHMARK-GUIDE.md)
- [`docs/FOUNDATION-01-REPORT.md`](docs/FOUNDATION-01-REPORT.md)

## License

Proprietary — all rights reserved unless otherwise stated.

# Arabic Document Fidelity

Local-first platform for analyzing Arabic PDF documents into a stable
intermediate representation, with conservative OCR routing plans.

Current packages:

- **Foundation-01** — native PDF analysis + Arabic Document IR + `diagnose` CLI
- **OCR-ROUTER-01A** — OCR engine contract, registry, router plans, `plan-ocr` CLI

This repository does **not** run real OCR, call cloud APIs, or produce DOCX.

## Product purpose

Preserve layout and reading fidelity for Arabic (and bilingual) documents from
PDF intake through structured IR, optional OCR routing, DOCX compilation, and
round-trip validation.

## Current scope

| Included | Not included |
|----------|--------------|
| Versioned Arabic Document IR (Pydantic v2) | Real OCR engines (Paddle/Tesseract/cloud) |
| PyMuPDF native text/image inspection | OCR execution on user PDFs |
| OCR engine contract + registry | Authentication / Supabase |
| Conservative OCR routing plans | Payments / frontend UI |
| Mock OCR for tests only | Production deployment |
| CLI `diagnose` and `plan-ocr` | Automatic text correction |

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

### Diagnose (native analysis only)

```powershell
python -m apps.cli diagnose --input sample.pdf --output outputs\sample
```

```text
outputs/sample/
  diagnosis.json
  summary.txt
```

### Plan OCR routing (no OCR execution)

```powershell
python -m apps.cli plan-ocr --input sample.pdf --output outputs\sample-routing
```

```text
outputs/sample-routing/
  diagnosis.json
  routing-plan.json
  routing-summary.txt
```

Exit codes: `0` success; non-zero for missing/invalid input or unrecoverable errors.

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

## Explicit non-goals (current packages)

- No real OCR (PaddleOCR, Tesseract, proprietary, or cloud)
- No LLM or vision-API “correction”
- No Arabic reshape / visual bidi conversion of stored logical text
- No FastAPI / web UI / auth / database
- No claim of production readiness
- Mock OCR is test-only and excluded from default routing

## Roadmap (summary)

1. **Foundation-01** — IR + native PDF analyzer + diagnose CLI
2. **OCR-ROUTER-01A** (this package) — contract, registry, routing plans
3. **OCR-ROUTER-01B** — real local OCR engine behind the contract (future)
4. **DOCX compiler** — emit editable Word from IR
5. **Round-trip validator** — fidelity checks PDF ↔ IR ↔ DOCX
6. **Visual review studio** — human review of risky pages/blocks

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/ARABIC-DOCUMENT-IR.md`](docs/ARABIC-DOCUMENT-IR.md)
- [`docs/OCR-ENGINE-CONTRACT.md`](docs/OCR-ENGINE-CONTRACT.md)
- [`docs/OCR-ROUTER-01A.md`](docs/OCR-ROUTER-01A.md)
- [`docs/BENCHMARK-GUIDE.md`](docs/BENCHMARK-GUIDE.md)
- [`docs/FOUNDATION-01-REPORT.md`](docs/FOUNDATION-01-REPORT.md)

## License

Proprietary — all rights reserved unless otherwise stated.

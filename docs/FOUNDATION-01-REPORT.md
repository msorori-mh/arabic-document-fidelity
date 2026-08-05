# Foundation-01 Report

**Package ID:** ARABIC-DOCUMENT-FIDELITY-FOUNDATION-01
**Decision:** PASS
**Date:** 2026-08-06

## Verdict

Foundation-01 delivers a coherent, locally runnable Python package for native PDF
analysis into a versioned Arabic Document IR, with CLI diagnosis, tests, and
documentation. Quality gates (ruff, mypy, pytest) and a CLI smoke test passed.
This is **not** production-ready and does **not** include OCR or cloud services.

## Repository and branch

| Item | Value |
|------|-------|
| Repository | `c:\projects\arabic-document-fidelity` |
| Branch | `main` |
| Commits | None yet (fresh repo; changes uncommitted) |

## Architecture implemented

```text
PDF input
  → packages/pdf_analyzer (PyMuPDF, read-only)
  → packages/document_model (Arabic Document IR v1.0.0)
  → apps/cli diagnose → diagnosis.json + summary.txt
```

Supporting packages:

- `packages/evaluation` — summary aggregation helpers
- `benchmark/` — manifest skeleton + privacy rules

## Changed files

Created (uncommitted):

```text
.gitignore
README.md
pyproject.toml
apps/__init__.py
apps/cli/__init__.py
apps/cli/__main__.py
apps/cli/diagnose.py
packages/__init__.py
packages/document_model/__init__.py
packages/document_model/enums.py
packages/document_model/models.py
packages/pdf_analyzer/__init__.py
packages/pdf_analyzer/analyzer.py
packages/pdf_analyzer/hashing.py
packages/pdf_analyzer/heuristics.py
packages/evaluation/__init__.py
packages/evaluation/summary.py
benchmark/manifest.csv
benchmark/README.md
benchmark/source/.gitkeep
benchmark/ground_truth/.gitkeep
benchmark/results/.gitkeep
docs/ARCHITECTURE.md
docs/ARABIC-DOCUMENT-IR.md
docs/BENCHMARK-GUIDE.md
docs/FOUNDATION-01-REPORT.md
tests/__init__.py
tests/conftest.py
tests/test_cli.py
tests/test_document_model.py
tests/test_heuristics.py
tests/test_pdf_analyzer.py
tests/fixtures/.gitkeep
outputs/.gitkeep
```

Local-only (gitignored / not for commit): `.venv/`, `outputs/` smoke artifacts.

## Commands executed

```text
winget install Python.Python.3.12
python -m venv .venv
python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy .
pytest
python -m apps.cli diagnose --input outputs/_smoke_fixture.pdf --output outputs/smoke_sample
git diff --check
git status --short
```

## Exact test results

| Gate | Result |
|------|--------|
| `ruff check .` | PASS (All checks passed!) |
| `ruff format --check .` | PASS (25 files already formatted) |
| `mypy .` | PASS (Success: no issues found in 20 source files) |
| `pytest` | PASS (**23 passed**) |
| `git diff --check` | PASS |

### Pytest coverage map

- Model validation & stable JSON serialization
- SHA-256 calculation
- Arabic character detection
- RTL / LTR / mixed / unknown direction inference
- Empty / digital / scanned page classification
- Invalid PDF handling
- CLI output creation & nonzero exit codes
- Deterministic repeated analysis

## CLI smoke-test result

```text
Command: python -m apps.cli diagnose --input outputs/_smoke_fixture.pdf --output outputs/smoke_sample
Exit code: 0
Artifacts:
  outputs/smoke_sample/diagnosis.json  (present)
  outputs/smoke_sample/summary.txt     (present)
Observed summary:
  page_count: 1
  page_type: digital_text
  pages requiring OCR: none
  warning: table detection not implemented
```

## Known limitations

1. **No OCR** — scanned pages are classified and flagged `needs_ocr=true` only.
2. **Table detection not implemented** — `has_tables` remains `false` with an explicit warning.
3. **Multi-column detection is heuristic** — may mislabel complex layouts; uncertain cases stay unlabeled or warned.
4. **Coverage ratios are approximate** — bbox union vs page area, not ink-density analysis.
5. **Block type guesses are conservative** — heading/header/footer/list heuristics are simple.
6. **No Arabic reshape / bidi visual conversion** — intentional; `text_raw` stores logical extraction.
7. **`confidence` is always `null`** for native blocks — no fabricated scores.
8. **Benchmark corpus is a skeleton** — no real PDFs committed; ground truth pending.
9. **Encrypted PDFs** fail closed with an error (not decrypted).
10. **Not production-ready** — foundation package only.

## Risks

| Risk | Mitigation / note |
|------|-------------------|
| Misclassification of sparse-text or complex pages as `unknown` | Conservative by design; warnings recorded |
| Image bbox fallback approximates full-page images | High risk_level + metadata note |
| Future OCR/router packages may need IR schema bumps | `schema_version` is explicit (`1.0.0`) |
| Synthetic fixtures may not match real Arabic PDF font embedding | Real public/anonymized corpus needed next |

## External / production confirmation

| Check | Status |
|-------|--------|
| External API calls | **Zero** (local PyPI install for deps only; no OCR/LLM/cloud APIs) |
| Production writes | **Zero** |
| Supabase / Lovable / secrets | **Not used** |
| Sensitive documents committed | **None** |

## Git status (at report time)

```text
Branch: main (no commits yet)
Untracked project files as listed above
No commit or push performed (per instructions)
```

## Recommended next package

**FOUNDATION-02 / OCR-ROUTER-01:** introduce a pluggable OCR interface and document
router that consumes `needs_ocr` / `page_type` from this IR, runs local OCR on
scanned/mixed pages only, and writes OCR blocks with real `source_engine` and
non-fabricated confidence — still without cloud APIs or DOCX compilation.

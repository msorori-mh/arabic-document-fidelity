# OCR-ROUTER-01A Report

**Package ID:** OCR-ROUTER-01A
**Decision:** PASS_OCR_ROUTER_01A
**Date:** 2026-08-06

## Verdict

OCR-ROUTER-01A delivers a provider-neutral OCR contract, deterministic registry,
conservative fail-closed router, test-only Mock OCR, and a `plan-ocr` CLI that
emits routing plans **without executing OCR**. All quality gates and both CLI
smoke tests passed. Nothing was committed or pushed.

## Identity

| Item | Value |
|------|-------|
| Repository | `C:\projects\arabic-document-fidelity` |
| Branch | `feat/ocr-router-01a` |
| Base SHA | `62065321f189efa9e0030c98046e2d33d741a0ff` |
| Remote | `https://github.com/msorori-mh/arabic-document-fidelity.git` |

## Architecture implemented

```text
PDF input
  → native PDF analyzer
  → Arabic Document IR (unchanged)
  → OCR engine registry + DocumentRouter
  → DocumentRoutingPlan sidecar
  → future OCR execution (not in 01A)
```

Packages:

- `packages/ocr_contracts` — descriptor/request/result models + `OCREngine` Protocol
- `packages/ocr_registry` — deterministic in-memory registry
- `packages/document_router` — policy + routing-plan models
- `packages/mock_ocr` — fixture-only Mock engine (`test_only=true`)

## Routing action matrix

| Condition | Action | Reason examples |
|-----------|--------|-----------------|
| empty | `skip_empty` | `empty_page` |
| unknown | `review_required` | `unknown_page_type` |
| digital_text, not needs_ocr, not high risk | `use_native_text` | `sufficient_native_text` |
| scanned + eligible engine | `run_ocr` | `scanned_page` |
| scanned + no eligible engine | `review_required` | `no_eligible_engine` / `test_engine_only` |
| mixed + layout engine | `run_ocr` | `mixed_page_requires_ocr` |
| mixed + no layout engine | `review_required` | `no_eligible_engine` / `test_engine_only` |
| high risk + eligible engine | `run_ocr` | `high_risk_page` |
| high risk + no eligible engine | `review_required` | `high_risk_page` / `test_engine_only` |

## Engine contract summary

- Execution modes: `local`, `cloud`, `mock`
- Logical Arabic text preserved; no reverse/reshape/bidi for storage
- Confidence optional; never fabricated
- Typed errors: duplicate/unknown/engine failures
- Test-only engines excluded unless `allow_test_engines=True`

## Mock engine safety

- `test_only=true`, `execution_mode=mock`, `requires_network=false`
- No image analysis / OCR libraries / network
- Requires explicit fixture responses; refuses otherwise
- Labels every result as mock/test-only
- Not registered by CLI `plan-ocr`; not selected by default router

## Changed files

```text
README.md
apps/cli/diagnose.py
apps/cli/plan_ocr.py
docs/ARCHITECTURE.md
docs/OCR-ENGINE-CONTRACT.md
docs/OCR-ROUTER-01A.md
docs/OCR-ROUTER-01A-REPORT.md
packages/ocr_contracts/*
packages/ocr_registry/*
packages/document_router/*
packages/mock_ocr/*
tests/test_ocr_contracts.py
tests/test_ocr_registry.py
tests/test_document_router.py
tests/test_mock_ocr.py
tests/test_cli_plan_ocr.py
```

## Exact quality-gate results

| Gate | Result |
|------|--------|
| `ruff check .` | PASS |
| `ruff format --check .` | PASS |
| `mypy .` | PASS |
| `pytest` | **56 passed** |
| `git diff --check` | PASS |

### Diagnose smoke

```text
python -m apps.cli diagnose --input outputs/_smoke_fixture.pdf --output outputs/smoke_diagnose
Exit: 0
Files: diagnosis.json, summary.txt (gitignored under outputs/)
```

### Plan-OCR smoke

```text
python -m apps.cli plan-ocr --input outputs/_smoke_fixture.pdf --output outputs/smoke_plan_ocr
Exit: 0
Files: diagnosis.json, routing-plan.json, routing-summary.txt (gitignored)
```

## Known limitations

1. No real OCR engines registered or executed.
2. Scanned/mixed/high-risk user pages typically become `review_required` until a real engine exists.
3. Mixed pages require `supports_layout=true` for `run_ocr`.
4. Routing plan is a sidecar; IR enrichment by OCR is future work.
5. Not production-ready.

## Technical debt (carried from Foundation-01)

- `DocumentModel.to_json` docstring claims sorted-key JSON but does not sort keys.
  Left unchanged (not required for this package). CLI outputs continue to use
  `json.dumps(..., sort_keys=True)`.
- Per-page table-detection warning noise and reading-order mutation left unchanged.

## Confirmations

| Check | Status |
|-------|--------|
| Zero real OCR execution | Confirmed |
| Zero external API calls | Confirmed |
| Zero production writes | Confirmed |
| Zero commit / push | Confirmed |
| Mock excluded from default routing | Confirmed |
| Existing diagnose intact | Confirmed |

## Git status (at report time)

```text
Branch: feat/ocr-router-01a @ 6206532
Modified/untracked OCR-ROUTER-01A files present; outputs/ artifacts ignored
No commit performed
```

## Recommended next package

**OCR-ROUTER-01B** — register a real **local** OCR engine behind the contract,
optionally execute `run_ocr` decisions, and enrich IR blocks — still excluding
Mock OCR from production routing by default.

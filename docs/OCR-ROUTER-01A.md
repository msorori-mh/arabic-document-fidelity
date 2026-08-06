# OCR-ROUTER-01A

**Routing schema version:** `1.0.0`
**Policy version:** `1.0.0`

Conservative OCR routing architecture: plan only — no real OCR execution.

## Pipeline

```text
PDF input
  → native PDF analyzer
  → Arabic Document IR (unchanged)
  → engine registry + router
  → DocumentRoutingPlan (sidecar)
```

Routing never mutates `DocumentModel`.

## Routing action matrix

| Page condition | Action | Typical reason |
|----------------|--------|----------------|
| `empty` | `skip_empty` | `empty_page` |
| `unknown` | `review_required` | `unknown_page_type` |
| `digital_text`, `needs_ocr=false`, not high risk | `use_native_text` | `sufficient_native_text` |
| `scanned_image` + eligible non-test engine | `run_ocr` | `scanned_page` |
| `scanned_image` + no eligible engine | `review_required` | `no_eligible_engine` or `test_engine_only` |
| `mixed` + eligible layout engine | `run_ocr` | `mixed_page_requires_ocr` |
| `mixed` + no layout-capable engine | `review_required` | `no_eligible_engine` / `test_engine_only` |
| `risk_level=high` + eligible engine | `run_ocr` | `high_risk_page` |
| `risk_level=high` + no eligible engine | `review_required` | `high_risk_page` or `test_engine_only` |

## Safety behavior

1. **Fail closed** — unknown pages always require review; no guessing.
2. **High risk never silently native** — cannot take `use_native_text`.
3. **Mock/test engines excluded by default** — `allow_test_engines=False`.
4. **CLI `plan-ocr` uses an empty production registry** — produces plans without
   selecting Mock OCR for user PDFs.
5. **No OCR execution** in this package — plans only.

## Why unknown / high-risk fail closed

Mis-routing a page to native-only extraction can permanently drop scanned or
ambiguous content. Foundation diagnostics already mark uncertainty; the router
preserves that uncertainty as `review_required` until a real eligible engine
exists and/or a human reviews the page.

## Why Mock OCR is never production-selected

Mock OCR:

- sets `test_only=true` and `execution_mode=mock`;
- returns only explicit fixtures (no image analysis);
- is ignored by `DocumentRouter` unless `allow_test_engines=True`;
- is not registered by the CLI `plan-ocr` command.

This prevents a user document from appearing “processable” by a fake engine.

## CLI

```powershell
python -m apps.cli plan-ocr --input sample.pdf --output outputs\sample-routing
```

Writes:

```text
outputs/sample-routing/
  diagnosis.json
  routing-plan.json
  routing-summary.txt
```

## Future OCR-ROUTER-01B boundary

OCR-ROUTER-01B (not implemented here) may:

- register a real local OCR engine behind the contract;
- optionally execute `run_ocr` decisions;
- enrich IR blocks with `source_engine` tags;

It must still honor fail-closed routing and must not enable Mock OCR for
production user documents by default.

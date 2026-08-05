# Benchmark guide

## Purpose

Provide a repeatable corpus and manifest for measuring analyzer behavior on
Arabic and bilingual PDFs — without committing private documents.

## Directory contract

```text
benchmark/
  source/          # PDFs (gitignored contents)
  ground_truth/    # Reviewed labels / IR (gitignored contents)
  results/         # Run outputs (gitignored contents)
  manifest.csv     # Registry (committed)
  README.md        # Privacy rules
```

## Adding a document

1. Confirm the file is **public**, **synthetic**, or **anonymized**.
2. Place it under `benchmark/source/` locally (do not commit if sensitive).
3. Add a row to `manifest.csv` with accurate attributes.
4. Set `contains_sensitive_data` to `false` only when true.
5. Leave `ground_truth_status` as `pending` until labels exist.

## Categories

| category | Meaning |
|----------|---------|
| `synthetic` | Generated programmatically |
| `public` | Redistributable public sample |
| `anonymized` | Real origin, PII/secrets removed |

## Evaluation (future)

Foundation-01 does not score accuracy yet. A later evaluation package will:

- load manifest rows
- run the analyzer
- compare against ground truth IR / labels
- write metrics under `benchmark/results/`

## Privacy reminder

Never commit confidential customer PDFs, credentials, or documents marked
`contains_sensitive_data=true`.

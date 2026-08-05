# Benchmark corpus

This directory holds **manifest metadata** and eventual evaluation artifacts for
Arabic Document Fidelity.

## Layout

| Path | Purpose |
|------|---------|
| `source/` | Input PDFs used for benchmark runs (not committed by default) |
| `ground_truth/` | Human-reviewed IR / labels (not committed by default) |
| `results/` | Analyzer outputs from evaluation runs |
| `manifest.csv` | Registry of documents and attributes |

## Privacy and licensing rules

Real documents placed under `source/` **must** be one of:

1. **Public** — clearly licensed for redistribution and research use; or
2. **Synthetic** — generated programmatically with no personal data; or
3. **Anonymized** — all personal, confidential, and proprietary content removed.

**Do not commit private, confidential, or sensitive sample documents.**

The `.gitignore` excludes `benchmark/source/*`, `ground_truth/*`, and `results/*`
contents (keeping only `.gitkeep` placeholders). The CSV manifest may list
planned documents without storing the binary files in git.

## Manifest columns

| Column | Meaning |
|--------|---------|
| `document_id` | Stable benchmark identifier |
| `filename` | Expected source filename under `source/` |
| `category` | e.g. synthetic, public, anonymized |
| `source_type` | born_digital, scanned, mixed, unknown |
| `language_mix` | ar, en, ar+en, none, unknown |
| `scan_quality` | high, medium, low, n/a, unknown |
| `has_tables` | true/false |
| `has_multiple_columns` | true/false |
| `has_headers_footers` | true/false |
| `contains_sensitive_data` | must be false for any committed artifact |
| `ground_truth_status` | pending, not_started, ready, reviewed |
| `notes` | Free-text notes |

## Foundation-01 status

This package ships a **manifest skeleton** only. Ground-truth IR labels and
scoring live in a later evaluation package.

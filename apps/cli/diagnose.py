"""``diagnose`` command: analyze a PDF and write diagnosis artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from packages.evaluation.summary import format_summary_text, summarize_document
from packages.pdf_analyzer.analyzer import analyze_pdf


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m apps.cli",
        description="Arabic Document Fidelity foundation CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    diagnose = subparsers.add_parser(
        "diagnose",
        help="Analyze a PDF and write diagnosis.json + summary.txt",
    )
    diagnose.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the input PDF file",
    )
    diagnose.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output directory for diagnosis artifacts",
    )
    return parser


def _resolve_output_dir(output: Path) -> Path:
    """Resolve and create the output directory; refuse unsafe paths."""
    resolved = output.expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def run_diagnose(input_path: Path, output_dir: Path) -> int:
    """Run diagnosis and write artifacts. Returns a process exit code."""
    pdf_path = input_path.expanduser().resolve()
    if not pdf_path.exists():
        print(f"error: input PDF not found: {pdf_path}", file=sys.stderr)
        return 2
    if not pdf_path.is_file():
        print(f"error: input path is not a file: {pdf_path}", file=sys.stderr)
        return 2
    if pdf_path.suffix.lower() != ".pdf":
        print(f"error: input must be a .pdf file: {pdf_path}", file=sys.stderr)
        return 2

    try:
        out = _resolve_output_dir(output_dir)
    except OSError as exc:
        print(f"error: cannot create output directory: {exc}", file=sys.stderr)
        return 2

    try:
        document = analyze_pdf(pdf_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: analysis failed: {exc}", file=sys.stderr)
        return 1

    summary = summarize_document(document)

    diagnosis_path = out / "diagnosis.json"
    summary_path = out / "summary.txt"

    # Ensure we only write inside the selected output directory
    for target in (diagnosis_path, summary_path):
        if not target.resolve().is_relative_to(out):
            print(f"error: refused to write outside output directory: {target}", file=sys.stderr)
            return 1

    diagnosis_payload = {
        "document": json.loads(document.to_json()),
        "summary": summary,
    }
    diagnosis_path.write_text(
        json.dumps(diagnosis_payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary_path.write_text(format_summary_text(summary), encoding="utf-8")

    print(f"Wrote {diagnosis_path}")
    print(f"Wrote {summary_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI main entry. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "diagnose":
        return run_diagnose(args.input, args.output)

    parser.error(f"unknown command: {args.command}")
    return 2

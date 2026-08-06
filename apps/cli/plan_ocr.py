"""``plan-ocr`` command: analyze PDF and emit an OCR routing plan (no OCR execution)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from packages.document_router.models import DocumentRoutingPlan, RoutingAction
from packages.document_router.router import DocumentRouter
from packages.evaluation.summary import summarize_document
from packages.ocr_registry.registry import OCREngineRegistry
from packages.pdf_analyzer.analyzer import analyze_pdf


def _resolve_output_dir(output: Path) -> Path:
    """Resolve and create the output directory."""
    resolved = output.expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _ensure_inside(out: Path, target: Path) -> bool:
    return target.resolve().is_relative_to(out)


def format_routing_summary(plan: DocumentRoutingPlan) -> str:
    """Render a human-readable routing-plan summary."""
    summary = plan.summary
    engines = ", ".join(summary.selected_engines) if summary.selected_engines else "(none)"
    warnings = plan.warnings
    warning_lines = "\n".join(f"  - {item}" for item in warnings) if warnings else "  (none)"

    page_warnings: list[str] = []
    for decision in plan.page_decisions:
        for warning in decision.warnings:
            page_warnings.append(f"page {decision.page_number}: {warning}")
    page_warning_lines = (
        "\n".join(f"  - {item}" for item in page_warnings) if page_warnings else "  (none)"
    )

    return "\n".join(
        [
            "Arabic Document Fidelity — OCR Routing Plan Summary",
            "=" * 52,
            f"Document ID:           {plan.document_id}",
            f"SHA-256:               {plan.source_sha256}",
            f"Schema version:        {plan.schema_version}",
            f"Policy version:        {plan.policy_version}",
            f"Total pages:           {summary.total_pages}",
            f"Native pages:          {summary.native_pages}",
            f"Pages requiring OCR:   {summary.pages_requiring_ocr}",
            f"Review-required pages: {summary.review_required_pages}",
            f"Skipped empty pages:   {summary.skipped_empty_pages}",
            f"Unsupported pages:     {summary.unsupported_pages}",
            f"Selected engines:      {engines}",
            "Plan warnings:",
            warning_lines,
            "Page warnings:",
            page_warning_lines,
            "",
            "Note: plan-ocr does not execute OCR. No engines were invoked.",
            "",
        ]
    )


def build_default_registry() -> OCREngineRegistry:
    """Return an empty production registry (no mock/real OCR engines)."""
    return OCREngineRegistry()


def run_plan_ocr(input_path: Path, output_dir: Path) -> int:
    """Analyze a PDF and write routing-plan artifacts. No OCR execution."""
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

    registry = build_default_registry()
    router = DocumentRouter(registry, allow_test_engines=False)
    try:
        plan = router.plan(document)
    except Exception as exc:  # noqa: BLE001 - surface as routing failure
        print(f"error: routing failed: {exc}", file=sys.stderr)
        return 1

    diagnosis_summary = summarize_document(document)
    diagnosis_path = out / "diagnosis.json"
    plan_path = out / "routing-plan.json"
    summary_path = out / "routing-summary.txt"

    for target in (diagnosis_path, plan_path, summary_path):
        if not _ensure_inside(out, target):
            print(f"error: refused to write outside output directory: {target}", file=sys.stderr)
            return 1

    diagnosis_payload: dict[str, Any] = {
        "document": json.loads(document.to_json()),
        "summary": diagnosis_summary,
    }
    plan_payload = json.loads(plan.model_dump_json())

    diagnosis_path.write_text(
        json.dumps(diagnosis_payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    plan_path.write_text(
        json.dumps(plan_payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary_path.write_text(format_routing_summary(plan), encoding="utf-8")

    # Sanity: confirm no OCR was selected for execution in this package's CLI path.
    if any(d.action == RoutingAction.RUN_OCR for d in plan.page_decisions):
        # Possible only if a non-test engine was registered; CLI uses empty registry.
        print(
            "warning: routing plan selected run_ocr but plan-ocr does not execute OCR",
            file=sys.stderr,
        )

    print(f"Wrote {diagnosis_path}")
    print(f"Wrote {plan_path}")
    print(f"Wrote {summary_path}")
    return 0

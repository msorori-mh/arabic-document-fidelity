"""CLI tests for plan-ocr and continued diagnose operation."""

from __future__ import annotations

import json
from pathlib import Path

from apps.cli.diagnose import main
from tests.conftest import make_digital_text_pdf, make_empty_pdf, make_scanned_image_pdf


def test_plan_ocr_output_files(fixtures_dir: Path, tmp_path: Path) -> None:
    pdf = make_digital_text_pdf(fixtures_dir / "plan_digital.pdf", text="Routing plan digital text")
    out = tmp_path / "outputs" / "sample-routing"
    code = main(["plan-ocr", "--input", str(pdf), "--output", str(out)])
    assert code == 0
    assert (out / "diagnosis.json").is_file()
    assert (out / "routing-plan.json").is_file()
    assert (out / "routing-summary.txt").is_file()

    plan = json.loads((out / "routing-plan.json").read_text(encoding="utf-8"))
    assert plan["schema_version"] == "1.0.0"
    assert plan["summary"]["total_pages"] == 1
    assert plan["page_decisions"][0]["action"] == "use_native_text"
    summary = (out / "routing-summary.txt").read_text(encoding="utf-8")
    assert "Total pages" in summary
    assert "does not execute OCR" in summary


def test_plan_ocr_scanned_requires_review_without_engine(
    fixtures_dir: Path, tmp_path: Path
) -> None:
    pdf = make_scanned_image_pdf(fixtures_dir / "plan_scanned.pdf")
    out = tmp_path / "out_scanned"
    code = main(["plan-ocr", "--input", str(pdf), "--output", str(out)])
    assert code == 0
    plan = json.loads((out / "routing-plan.json").read_text(encoding="utf-8"))
    actions = {d["action"] for d in plan["page_decisions"]}
    assert "run_ocr" not in actions
    assert "review_required" in actions or "skip_empty" in actions or "unsupported" in actions


def test_plan_ocr_invalid_pdf(fixtures_dir: Path, tmp_path: Path) -> None:
    bad = fixtures_dir / "bad_plan.pdf"
    bad.write_bytes(b"not-a-pdf")
    code = main(["plan-ocr", "--input", str(bad), "--output", str(tmp_path / "bad_out")])
    assert code != 0


def test_diagnose_still_works(fixtures_dir: Path, tmp_path: Path) -> None:
    pdf = make_empty_pdf(fixtures_dir / "diag_still.pdf")
    out = tmp_path / "diag_out"
    code = main(["diagnose", "--input", str(pdf), "--output", str(out)])
    assert code == 0
    assert (out / "diagnosis.json").is_file()
    assert (out / "summary.txt").is_file()
    assert not (out / "routing-plan.json").exists()


def test_plan_ocr_no_engine_execution_marker(fixtures_dir: Path, tmp_path: Path) -> None:
    pdf = make_digital_text_pdf(fixtures_dir / "no_exec.pdf")
    out = tmp_path / "no_exec"
    code = main(["plan-ocr", "--input", str(pdf), "--output", str(out)])
    assert code == 0
    plan = json.loads((out / "routing-plan.json").read_text(encoding="utf-8"))
    assert plan["summary"]["selected_engines"] == []
    for decision in plan["page_decisions"]:
        assert decision["action"] != "run_ocr" or decision["selected_engine_id"] is not None

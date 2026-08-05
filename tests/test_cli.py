"""CLI diagnose command tests."""

from __future__ import annotations

import json
from pathlib import Path

from apps.cli.diagnose import main
from tests.conftest import make_digital_text_pdf, make_empty_pdf


def test_cli_output_creation(fixtures_dir: Path, tmp_path: Path) -> None:
    pdf = make_digital_text_pdf(fixtures_dir / "cli_sample.pdf", text="CLI diagnose test")
    out = tmp_path / "outputs" / "sample"
    code = main(["diagnose", "--input", str(pdf), "--output", str(out)])
    assert code == 0
    diagnosis = out / "diagnosis.json"
    summary = out / "summary.txt"
    assert diagnosis.is_file()
    assert summary.is_file()
    payload = json.loads(diagnosis.read_text(encoding="utf-8"))
    assert "document" in payload
    assert "summary" in payload
    assert payload["summary"]["page_count"] == 1
    text = summary.read_text(encoding="utf-8")
    assert "SHA-256" in text
    assert "Page count" in text


def test_cli_invalid_input_nonzero(tmp_path: Path) -> None:
    out = tmp_path / "out"
    code = main(["diagnose", "--input", str(tmp_path / "nope.pdf"), "--output", str(out)])
    assert code != 0


def test_cli_invalid_pdf_nonzero(fixtures_dir: Path, tmp_path: Path) -> None:
    bad = fixtures_dir / "bad.pdf"
    bad.write_bytes(b"%PDF-1.4 broken")
    out = tmp_path / "out_bad"
    code = main(["diagnose", "--input", str(bad), "--output", str(out)])
    assert code != 0


def test_cli_empty_pdf(fixtures_dir: Path, tmp_path: Path) -> None:
    pdf = make_empty_pdf(fixtures_dir / "cli_empty.pdf")
    out = tmp_path / "out_empty"
    code = main(["diagnose", "--input", str(pdf), "--output", str(out)])
    assert code == 0
    payload = json.loads((out / "diagnosis.json").read_text(encoding="utf-8"))
    assert payload["document"]["pages"][0]["page_type"] == "empty"

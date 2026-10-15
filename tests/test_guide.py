import re
import typing
from pathlib import Path

import watermark_detector.model
import watermark_detector.report

ROOT = Path(__file__).parent.parent
GUIDE = ROOT / "docs" / "43.03-guide" / "usage-guide.md"
TEXT = GUIDE.read_text(encoding="utf-8")

COVERAGE_STATUSES = (
    "checked",
    "verifier_run",
    "verifier_configured_not_run",
    "not_checkable_locally",
    "manual_check_available",
    "not_checkable",
)


def test_mentions():
    for s in (
        "wmd detect", "wmd providers", "wmd certs", "wmd validate",
        "make install", "make test", "make validate-real",
        "--json", "--anchors", "--remote", "--config", "WMD_CONFIG", "GB 45438",
    ):
        assert s in TEXT, s


def test_every_verdict_documented():
    for v in typing.get_args(watermark_detector.model.Verdict):
        assert f"`{v}`" in TEXT, v


def test_every_coverage_status_documented():
    for s in COVERAGE_STATUSES:
        assert f"`{s}`" in TEXT, s


def test_schema_id():
    assert watermark_detector.report.SCHEMA in TEXT


def test_exit_codes_section():
    assert re.search(r"^## Exit codes\s*$", TEXT, re.M)


def test_python_example_runs(monkeypatch, capsys):
    m = re.search(r"```python\n(.*?)```", TEXT, re.S)
    assert m
    monkeypatch.chdir(ROOT)
    exec(compile(m.group(1), str(GUIDE), "exec"), {})
    assert "c2pa" in capsys.readouterr().out


def test_no_removal_and_no_quota():
    assert "wmd remove" not in TEXT
    for line in TEXT.splitlines():
        if "synthid.com" in line:
            assert not re.search(r"\b\d+\s+(checks|per day|a day)", line)

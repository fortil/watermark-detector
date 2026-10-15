from pathlib import Path

import pytest

from watermark_detector.validate import run_manifest

MANIFEST = Path(__file__).parent / "fixtures" / "real" / "expected.json"


def test_real_samples():
    if not MANIFEST.exists():
        pytest.skip("no real samples: see tests/fixtures/real/README.md")
    failed = [r for r in run_manifest(MANIFEST) if not r.passed]
    assert not failed, [f"{r.id}: {r.detail}" for r in failed]

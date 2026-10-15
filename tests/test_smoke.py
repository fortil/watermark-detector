import subprocess
import sys

import c2pa

import watermark_detector


def test_version():
    assert watermark_detector.__version__ == "0.1.0"


def test_sdk_version():
    assert c2pa.sdk_version() == "0.91.0"


def test_cli_version():
    r = subprocess.run(
        [sys.executable, "-m", "watermark_detector", "--version"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert r.stdout.strip() == "wmd 0.1.0"

import re
from pathlib import Path

README = (Path(__file__).parent.parent / "README.md").read_text(encoding="utf-8")
ROOT = Path(__file__).parent.parent


def test_mentions():
    for s in ("wmd detect", "wmd providers", "wmd certs", "wmd validate", "--anchors", "--remote",
              "GB 45438", "Z.AI"):
        assert s in README, s


def test_limitations_heading():
    assert re.search(r"^#+ Limitations\s*$", README, re.M)


def test_no_removal_command():
    assert "wmd remove" not in README


def test_no_synthid_quota_number():
    # The synthid.com limit is not documented; only the Gemini app's quota may be stated.
    for line in README.splitlines():
        if "synthid.com" in line:
            assert not re.search(r"\b\d+\s+(checks|per day|a day)", line)


def test_links_guide():
    assert "](docs/43.03-guide/usage-guide.md)" in README
    assert (ROOT / "docs" / "43.03-guide" / "usage-guide.md").exists()

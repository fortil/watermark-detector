from pathlib import Path

import pytest

from watermark_detector.c2pa_reader import C2paResult, ManifestInfo, build_context, read_c2pa
from watermark_detector.providers import PROFILES, attribute, match_aigc_producer
from watermark_detector.sniff import sniff_bytes

TP = Path(__file__).parent / "fixtures" / "third_party"

# name -> (provider, verdict)
EXPECTED = {
    "claude_like.png": ("claude", "claimed"),
    "claude_like.svg": ("claude", "claimed"),
    "gpt_like.jpg": ("gpt", "claimed"),
    "gemini_like.png": ("gemini", "claimed"),
    "google_camera.jpg": (None, "present_other"),
    "spoof_name_only.png": (None, "present_other"),
    "ai_other.png": (None, "ai_unknown_provider"),
    "tampered.png": ("claude", "invalid"),
    "reencoded.png": (None, "absent"),
    "remote_only.jpg": (None, "remote_reference"),
    "plain.png": (None, "absent"),
}


def attribute_file(path, ctx):
    data = Path(path).read_bytes()
    _, mime = sniff_bytes(data)
    return attribute(read_c2pa(data, mime, ctx), "file")


@pytest.fixture(scope="module")
def ctx():
    return build_context()


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_catalogue(name, fx, ctx):
    provider, verdict = EXPECTED[name]
    f = attribute_file(fx[name], ctx)
    assert (f[0].provider, f[0].verdict) == (provider, verdict)
    assert len(f) == 1


def test_spoof_mismatch(fx, ctx):
    f = attribute_file(fx["spoof_name_only.png"], ctx)[0]
    assert f.evidence["claim_mismatch"] == "claude"


def test_pinned_confirmed(fx, pkis):
    c = build_context([pkis["claude"].root_pem.decode()])
    f = attribute_file(fx["claude_like.png"], c)[0]
    assert (f.provider, f.verdict) == ("claude", "confirmed")
    assert f.evidence["trusted_via"] == "user-anchor"


def test_third_party(ctx):
    f = attribute_file(TP / "C.jpg", ctx)[0]
    assert (f.provider, f.verdict) == (None, "present_other")
    assert f.evidence["validation_state"] == "Valid"
    assert f.evidence["failure_codes"] == ["signingCredential.untrusted"]
    assert attribute_file(TP / "A.jpg", ctx)[0].verdict == "absent"


def test_via_ingredient():
    claude = {"O": "Anthropic, PBC", "CN": "x"}
    m = ManifestInfo("urn:b", False, claude, {}, None, (), (), (), (), None)
    top = ManifestInfo("urn:a", True, {"O": "Other"}, {}, None, (), (), (), (), None)
    res = C2paResult("present", "Valid", "urn:a", (top, m))
    f = attribute(res, "file")
    assert [(x.verdict, x.provider) for x in f] == [("present_other", None), ("via_ingredient", "claude")]


def test_zai_producer():
    assert match_aigc_producer("91110108MA01KP2T5U") == "zai"
    assert match_aigc_producer("91350100M000100Y43") is None
    assert match_aigc_producer(None) is None
    assert len(PROFILES) == 4


def test_c2pa_never_zai(fx, ctx):
    for name, p in fx.items():
        kind_mime = sniff_bytes(p.read_bytes())
        if kind_mime[0] not in ("image", "svg"):
            continue
        for f in attribute_file(p, ctx):
            assert f.provider != "zai", name
            if name.startswith(("zai_", "aigc_")):
                assert f.verdict == "absent", name

import json

from watermark_detector.model import Finding, Report
from watermark_detector.report import render_json, render_text, report_to_dict

CLAIMED = Finding(
    "c2pa", "claimed", "claude", "file",
    {"signer_subject": {"O": "Anthropic, PBC", "CN": "Anthropic Claude Content Signing"},
     "note": "Signature intact, but not trusted."},
)
ZAI = Finding(
    "aigc-label", "unsigned_hint", "zai", "file",
    {"content_producer": "001191110108MA01KP2T5U00000", "label": "1"},
)
UNATTR = Finding("aigc-label", "unsigned_hint", None, "file", {"content_producer": "x", "label": "1"})


def rep(*findings):
    return Report("p", "image", "image/png", list(findings), [], [])


def test_signals():
    s = report_to_dict(rep(CLAIMED, Finding("c2pa", "via_ingredient", "claude", "file")))["summary"]
    assert s["provider_signals"] == {"claude": ["claimed", "via_ingredient"]}
    assert "absence_note" not in s


def test_absence():
    s = report_to_dict(rep(Finding("c2pa", "absent", None, "file")))["summary"]
    assert "absence_note" in s


def test_json_roundtrip():
    d = json.loads(render_json([rep(CLAIMED)]))
    assert d[0]["schema"] == "watermark-detector/report@1"


def test_text_claimed():
    t = render_text(rep(CLAIMED))
    assert "CLAIMED" in t and "claude" in t


def test_zai():
    r = rep(ZAI)
    assert report_to_dict(r)["summary"]["provider_signals"] == {"zai": ["unsigned_hint"]}
    t = render_text(r)
    assert "aigc-label zai UNSIGNED_HINT" in t
    assert "producer=001191110108MA01KP2T5U00000" in t
    assert "Unsigned metadata: anyone can add or remove it." in t


def test_unattributed():
    s = report_to_dict(rep(UNATTR))["summary"]
    assert s["ai_label_unattributed"] == 1 and "GB 45438" in s["absence_note"]

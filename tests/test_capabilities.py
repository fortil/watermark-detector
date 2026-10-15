from watermark_detector.capabilities import CAPABILITIES, coverage_for


def test_row_count_and_pairs():
    assert len(CAPABILITIES) == 18
    pairs = {(c.provider, c.modality) for c in CAPABILITIES}
    for p in ("claude", "gemini", "gpt"):
        for m in ("text", "image", "document"):
            assert (p, m) in pairs
    for m in ("text", "image", "document", "video"):
        assert ("zai", m) in pairs


def test_sources_and_text_rows():
    for c in CAPABILITIES:
        assert c.sources and any(s.startswith("https://") for s in c.sources)
        if c.modality == "text":
            assert c.local == "no"
        if c.provider == "zai":
            assert "confirmed" not in c.how_to_check


def test_coverage_image_and_text():
    img = coverage_for("image", frozenset(), False)
    assert all(c["signal"] for c in img)
    text_signals = {c.signal for c in CAPABILITIES if c.modality == "text"}
    assert not [i for i in img if i["signal"] in text_signals]
    by_signal = {i["signal"]: i["status"] for i in img}
    assert by_signal["Visible 'AI生成' badge, bottom-right"] == "manual_check_available"
    assert by_signal["Implicit digital (pixel) watermark named in BigModel docs"] == "not_checkable"
    t = coverage_for("text", frozenset({"claude"}), True)
    assert [x["status"] for x in t if x["provider"] == "claude"] == ["verifier_run"]
    t2 = coverage_for("text", frozenset({"claude"}), False)
    assert [x["status"] for x in t2 if x["provider"] == "claude"] == ["verifier_configured_not_run"]


def test_synthid_row():
    row = next(c for c in CAPABILITIES if c.signal == "SynthID pixel watermark" and c.provider == "gemini")
    assert "https://support.google.com/gemini/answer/16722517" in row.sources
    assert "not documented" in row.how_to_check and "rolling 24 h" in row.how_to_check


def test_video():
    v = coverage_for("video", frozenset(), False)
    assert len(v) == 1 and v[0]["provider"] == "zai" and v[0]["status"] == "checked"

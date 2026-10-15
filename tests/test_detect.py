from fixtures.mock_verifier import mock_verifier, write_config

from watermark_detector.detect import DetectOptions, detect_path
from watermark_detector.report import report_to_dict


def summ(r):
    return report_to_dict(r)["summary"]


def find(r, **kw):
    return [f for f in r.findings if all(getattr(f, k) == v for k, v in kw.items())]


def test_claude_png(fx, pkis):
    r = detect_path(fx["claude_like.png"])
    assert summ(r)["provider_signals"] == {"claude": ["claimed"]}
    root = pkis["claude"].root_pem.decode()
    r2 = detect_path(fx["claude_like.png"], DetectOptions(anchors_pem=(root,)))
    assert summ(r2)["provider_signals"] == {"claude": ["confirmed"]}


def test_docx_and_pdf(fx):
    r = detect_path(fx["doc_claude_image.docx"])
    assert find(r, provider="claude", verdict="claimed", location="word/media/image1.png")
    r = detect_path(fx["pdf_gpt_image.pdf"])
    assert find(r, provider="gpt", verdict="claimed", location="pdf:page1:Im0:obj4")
    assert find(r, layer="c2pa", verdict="absent", location="file")


def test_xmp_and_plain(fx):
    assert summ(detect_path(fx["xmp_google.jpg"]))["provider_signals"] == {"gemini": ["unsigned_hint"]}
    assert "absence_note" in summ(detect_path(fx["plain.png"]))


def test_text_verifier(fx, tmp_path, monkeypatch):
    monkeypatch.setenv("WMD_TEST_KEY", "k")
    with mock_verifier() as m:
        cfg = write_config(tmp_path / "v.toml", m.url)
        r = detect_path(fx["text_long.txt"], DetectOptions(config_path=cfg))
        assert find(r, layer="text-watermark", verdict="not_run", provider="claude")
        assert not m.requests
        r = detect_path(fx["text_long.txt"], DetectOptions(config_path=cfg, remote=True))
        f = find(r, layer="text-watermark", verdict="score")[0]
        assert f.evidence["score"] == 0.87 and f.evidence["word_count"] == 450


def test_flate_skipped(fx):
    r = detect_path(fx["pdf_flate_image.pdf"])
    assert find(r, verdict="skipped")[0].evidence["count"] == 1


def test_zai_files(fx):
    r = detect_path(fx["zai_like.jpg"])
    assert summ(r)["provider_signals"] == {"zai": ["unsigned_hint"]}
    assert find(r, layer="c2pa")[0].verdict == "absent"
    r = detect_path(fx["zai_like.mp4"])
    assert (r.kind, r.mime, r.errors) == ("video", "video/mp4", [])
    assert summ(r)["provider_signals"] == {"zai": ["unsigned_hint"]}
    r = detect_path(fx["plain.mp4"])
    assert r.errors == [] and "absence_note" in summ(r)
    assert any(c["provider"] == "zai" and c["status"] == "checked" for c in r.coverage)


def test_zai_documents(fx):
    r = detect_path(fx["pdf_zai_image.pdf"])
    assert find(r, provider="zai", verdict="unsigned_hint", location="pdf:page1:Im0:obj4")
    assert not find(r, provider="zai", location="file")
    for name in ("doc_zai_label.docx", "pdf_zai_label.pdf"):
        assert find(detect_path(fx[name]), provider="zai", verdict="unsigned_hint", location="file")


def test_other_producer(fx):
    s = summ(detect_path(fx["aigc_other.jpg"]))
    assert s["provider_signals"] == {} and s["ai_label_unattributed"] == 1


def test_unknown_and_missing(tmp_path):
    p = tmp_path / "x.bin"
    p.write_bytes(b"\x00\x01\x02\xff")
    assert detect_path(p).errors == ["unsupported file type"]
    assert detect_path(tmp_path / "nope").errors


def test_container_error_is_a_finding(fx):
    from watermark_detector import containers

    # Lower the member limit so the docx scan stops early with a note.
    orig = containers.MAX_MEMBERS
    containers.MAX_MEMBERS = 1
    try:
        r = detect_path(fx["doc_claude_image.docx"])
    finally:
        containers.MAX_MEMBERS = orig
    f = find(r, layer="container", verdict="error")
    assert f and "too many members" in f[0].evidence["reason"]

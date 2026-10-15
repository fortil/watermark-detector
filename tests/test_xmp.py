from watermark_detector.xmp import parse_ai_fields, xmp_findings


def _f(fx, name):
    return [(f.layer, f.provider, f.verdict) for f in xmp_findings(fx[name].read_bytes(), "file")]


def test_google(fx):
    for n in ("xmp_google.jpg", "xmp_google.png", "xmp_google_z.png"):
        assert _f(fx, n) == [("xmp", "gemini", "unsigned_hint")], n


def test_dst_only(fx):
    assert _f(fx, "xmp_dst_only.jpg") == [("xmp", None, "unsigned_hint")]


def test_none(fx):
    assert _f(fx, "xmp_capture.jpg") == []
    assert _f(fx, "plain.jpg") == []


def test_attribute_credit():
    p = '<x:xmpmeta><rdf:Description photoshop:Credit="Made with Google AI"/></x:xmpmeta>'
    assert parse_ai_fields(p).credits == ("Made with Google AI",)
    q = "<photoshop:Credit>A</photoshop:Credit>"
    assert parse_ai_fields(q).credits == ("A",)

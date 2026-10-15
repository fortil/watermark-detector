from watermark_detector.c2pa_reader import build_context, read_c2pa
from watermark_detector.certs import extract_certs


def _active_serial(path, mime):
    r = read_c2pa(path.read_bytes(), mime, build_context())
    return next(m for m in r.manifests if m.is_active).signer_serial


def test_png(fx, pkis):
    p = fx["claude_like.png"]
    certs = extract_certs(p.read_bytes(), "image/png", _active_serial(p, "image/png"))
    assert len(certs) == 2
    assert certs[0].is_active_signer and not certs[1].is_active_signer
    assert tuple(c.der for c in certs) == pkis["claude"].chain_der


def test_svg(fx, pkis):
    p = fx["claude_like.svg"]
    certs = extract_certs(p.read_bytes(), "image/svg+xml", None)
    assert tuple(c.der for c in certs) == pkis["claude"].chain_der


def test_plain(fx):
    assert extract_certs(fx["plain.png"].read_bytes(), "image/png", None) == []


def test_pin_intermediate(fx):
    p = fx["claude_like.png"]
    certs = extract_certs(p.read_bytes(), "image/png", None)
    r = read_c2pa(p.read_bytes(), "image/png", build_context([certs[1].pem]))
    assert r.validation_state == "Trusted"

from pathlib import Path

import pytest

from watermark_detector.c2pa_reader import build_context, read_c2pa

TP = Path(__file__).parent / "fixtures" / "third_party"


@pytest.fixture(scope="module")
def ctx():
    return build_context()


def rd(path, mime, ctx):
    return read_c2pa(Path(path).read_bytes(), mime, ctx)


def test_absent(fx, ctx):
    assert rd(fx["plain.png"], "image/png", ctx).status == "absent"
    assert rd(fx["plain.jpg"], "image/jpeg", ctx).status == "absent"
    assert rd(TP / "A.jpg", "image/jpeg", ctx).status == "absent"


def test_claude_like(fx, ctx):
    r = rd(fx["claude_like.png"], "image/png", ctx)
    assert r.status == "present"
    assert r.validation_state == "Valid"
    m = next(x for x in r.manifests if x.is_active)
    assert m.failure_codes == ("signingCredential.untrusted",)
    assert m.signer_subject["O"] == "Anthropic, PBC"
    assert m.claim_generators == ("Anthropic Files",)
    assert any(a["action"] == "com.anthropic.claude.provided" for a in m.actions)
    assert "assertion.dataHash.match" in m.success_codes
    assert "signingCredential.ocsp.skipped" not in m.success_codes + m.failure_codes


def test_claude_pinned(fx, pkis):
    c = build_context([pkis["claude"].root_pem.decode()])
    r = rd(fx["claude_like.png"], "image/png", c)
    assert r.validation_state == "Trusted"
    m = next(x for x in r.manifests if x.is_active)
    assert m.trusted_via == "user-anchor"
    assert "signingCredential.trusted" in m.success_codes
    assert m.failure_codes == ()


def test_tampered(fx, ctx):
    r = rd(fx["tampered.png"], "image/png", ctx)
    assert r.validation_state == "Invalid"
    m = next(x for x in r.manifests if x.is_active)
    assert "assertion.dataHash.mismatch" in m.failure_codes


def test_reencoded(fx, ctx):
    assert rd(fx["reencoded.png"], "image/png", ctx).status == "absent"


def test_remote(fx, ctx):
    r = rd(fx["remote_only.jpg"], "image/jpeg", ctx)
    assert r.status == "remote"
    assert r.remote_url == "https://example.invalid/manifest.c2pa"


def test_garbage(ctx):
    assert read_c2pa(b"not a png", "image/png", ctx).status == "error"


def test_svg(fx, ctx):
    assert rd(fx["claude_like.svg"], "image/svg+xml", ctx).status == "present"


def test_third_party_c(ctx):
    r = rd(TP / "C.jpg", "image/jpeg", ctx)
    assert r.status == "present"
    assert r.validation_state == "Valid"
    m = next(x for x in r.manifests if x.is_active)
    assert m.failure_codes == ("signingCredential.untrusted",)
    assert m.claim_generators == ("make_test_images/0.26.0 c2pa-rs/0.26.0",)
    assert any(a["digital_source_type"] == "algorithmicMedia" for a in m.actions)

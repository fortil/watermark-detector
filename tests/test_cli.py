import json
import subprocess
import sys

from fixtures.mock_verifier import mock_verifier, write_config


def wmd(*args, env=None):
    import os

    e = {**os.environ, **(env or {})}
    return subprocess.run([sys.executable, "-m", "watermark_detector", *args],
                          capture_output=True, text=True, env=e)


def findings(p, **kw):
    return [f for f in p["findings"] if all(f[k] == v for k, v in kw.items())]


def test_no_args_prints_help_and_exits_2():
    r = wmd()
    assert r.returncode == 2 and "usage: wmd" in r.stdout


def test_usage_error_exits_2():
    assert wmd("bogus").returncode == 2
    assert wmd("detect").returncode == 2


def test_detect_claude(fx, pkis, tmp_path):
    r = wmd("detect", "--json", str(fx["claude_like.png"]))
    assert r.returncode == 0, r.stderr
    rep = json.loads(r.stdout)[0]
    assert rep["summary"]["provider_signals"] == {"claude": ["claimed"]}
    root = tmp_path / "root.pem"
    root.write_bytes(pkis["claude"].root_pem)
    r = wmd("detect", "--json", "--anchors", str(root), str(fx["claude_like.png"]))
    rep = json.loads(r.stdout)[0]
    assert rep["summary"]["provider_signals"] == {"claude": ["confirmed"]}
    assert findings(rep, verdict="confirmed")[0]["evidence"]["trusted_via"] == "user-anchor"


def test_detect_text_output(fx):
    r = wmd("detect", str(fx["claude_like.png"]))
    assert r.returncode == 0 and "CLAIMED" in r.stdout


def test_missing_path_exits_1(tmp_path):
    assert wmd("detect", str(tmp_path / "nope.png")).returncode == 1


def test_bad_anchor_file_exits_1(fx, tmp_path):
    assert wmd("detect", "--anchors", str(tmp_path / "nope.pem"), str(fx["plain.png"])).returncode == 1


def test_providers_json():
    r = wmd("providers", "--json")
    rows = json.loads(r.stdout)
    assert r.returncode == 0 and len(rows) == 18
    assert all(any(s.startswith("https://") for s in row["sources"]) for row in rows)
    assert all(row["local"] == "no" for row in rows if row["modality"] == "text")
    assert wmd("providers").returncode == 0


def test_detect_zai(fx):
    rep = json.loads(wmd("detect", "--json", str(fx["zai_like.jpg"])).stdout)[0]
    assert findings(rep, layer="aigc-label", provider="zai", verdict="unsigned_hint")
    assert rep["summary"]["provider_signals"] == {"zai": ["unsigned_hint"]}
    r = wmd("detect", "--json", str(fx["zai_like.mp4"]))
    assert r.returncode == 0 and json.loads(r.stdout)[0]["kind"] == "video"
    r = wmd("detect", "--json", str(fx["plain.mp4"]))
    assert r.returncode == 0 and "absence_note" in json.loads(r.stdout)[0]["summary"]


def test_detect_remote(fx, tmp_path):
    with mock_verifier() as m:
        cfg = write_config(tmp_path / "v.toml", m.url)
        r = wmd("detect", "--json", "--remote", "--config", str(cfg), str(fx["text_long.txt"]),
                env={"WMD_TEST_KEY": "secret-key-value"})
    rep = json.loads(r.stdout)[0]
    assert findings(rep, verdict="score")[0]["evidence"]["score"] == 0.87
    assert "secret-key-value" not in r.stdout + r.stderr


def test_certs(fx, tmp_path):
    out = tmp_path / "chain.pem"
    r = wmd("certs", str(fx["claude_like.png"]), "-o", str(out))
    lines = r.stdout.strip().splitlines()
    assert r.returncode == 0 and len(lines) == 2
    assert "active_signer=yes" in lines[0] and "active_signer=no" in lines[1]
    assert out.read_text().count("BEGIN CERTIFICATE") == 2
    assert wmd("certs", str(fx["plain.png"])).returncode == 1
    assert wmd("certs", str(tmp_path / "nope")).returncode == 1


def test_validate(fx, tmp_path):
    def manifest(name, expect):
        p = tmp_path / name
        p.write_text(json.dumps({"version": 1, "samples": [
            {"id": "s1", "path": str(fx["claude_like.png"]), "expect": expect}]}))
        return p

    ok = wmd("validate", str(manifest("ok.json", {"provider": "claude", "verdict_in": ["claimed"]})))
    assert ok.returncode == 0 and "PASS s1" in ok.stdout
    bad = wmd("validate", str(manifest("bad.json", {"provider": "gpt"})))
    assert bad.returncode == 3 and "FAIL s1" in bad.stdout
    assert wmd("validate", str(tmp_path / "missing.json")).returncode == 1


def test_help_has_no_removal_words():
    texts = [wmd("--help").stdout] + [wmd(c, "--help").stdout for c in ("detect", "providers", "certs", "validate")]
    blob = "\n".join(texts).lower()
    for word in ("remove", "strip", "erase", "perturb", "rewrite"):
        assert word not in blob

import json

import pytest
from fixtures.mock_verifier import mock_verifier, write_config

from watermark_detector.detect import DetectOptions
from watermark_detector.validate import SampleResult, load_manifest, run_manifest


def _manifest(tmp_path, fx, samples):
    for s in samples:
        s["path"] = str(fx[s.pop("fixture")])
    p = tmp_path / "expected.json"
    p.write_text(json.dumps({"version": 1, "samples": samples}))
    return p


def test_passing_manifest(tmp_path, fx, monkeypatch):
    monkeypatch.setenv("WMD_TEST_KEY", "k")
    with mock_verifier() as m:
        cfg = write_config(tmp_path / "v.toml", m.url)
        p = _manifest(tmp_path, fx, [
            {"id": "c", "fixture": "claude_like.png",
             "expect": {"layer": "c2pa", "provider": "claude", "verdict_in": ["claimed"]}},
            {"id": "p", "fixture": "plain.png", "expect": {"no_provider_signal": True}},
            {"id": "t", "fixture": "text_long.txt",
             "expect": {"layer": "text-watermark", "provider": "claude", "verdict_in": ["score"], "score_min": 0.5}},
            {"id": "z1", "fixture": "zai_like.jpg",
             "expect": {"layer": "aigc-label", "provider": "zai", "verdict_in": ["unsigned_hint"]}},
            {"id": "z2", "fixture": "zai_like.mp4",
             "expect": {"layer": "aigc-label", "provider": "zai", "verdict_in": ["unsigned_hint"]}},
        ])
        res = run_manifest(p, DetectOptions(remote=True, config_path=cfg))
    assert all(isinstance(r, SampleResult) for r in res)
    assert [(r.id, r.passed) for r in res] == [(i, True) for i in ("c", "p", "t", "z1", "z2")], res


def test_failing_expectations(tmp_path, fx):
    p = _manifest(tmp_path, fx, [
        {"id": "bad", "fixture": "plain.png", "expect": {"provider": "claude", "verdict_in": ["claimed"]}},
        {"id": "zno", "fixture": "zai_like.jpg", "expect": {"no_provider_signal": True}},
    ])
    res = run_manifest(p)
    assert [r.passed for r in res] == [False, False]
    assert res[0].detail and "claude" in res[0].detail


def test_anchor_from_manifest(tmp_path, fx, pkis):
    root = tmp_path / "root.pem"
    root.write_bytes(pkis["claude"].root_pem)
    p = tmp_path / "expected.json"
    p.write_text(json.dumps({"version": 1, "samples": [{
        "id": "pinned", "path": str(fx["claude_like.png"]), "anchors": ["root.pem"],
        "expect": {"provider": "claude", "verdict_in": ["confirmed"]},
    }]}))
    assert run_manifest(p)[0].passed


def test_schema_errors(tmp_path):
    def write(doc):
        p = tmp_path / "m.json"
        p.write_text(doc if isinstance(doc, str) else json.dumps(doc))
        return p

    bad = [
        "not json",
        {"version": 2, "samples": []},
        {"version": 1, "samples": {}},
        {"version": 1, "samples": [{"id": "a", "path": "x"}]},
        {"version": 1, "samples": [{"id": "a", "path": "x", "expect": {"colour": "red"}}]},
        {"version": 1, "samples": [{"id": "a", "path": "x", "expect": {"verdict_in": "claimed"}}]},
        {"version": 1, "samples": [{"id": "a", "path": "x", "expect": {"score_min": "high"}}]},
        {"version": 1, "samples": [{"id": "a", "path": "x", "expect": {"no_provider_signal": True, "layer": "c2pa"}}]},
    ]
    for doc in bad:
        with pytest.raises(ValueError):
            load_manifest(write(doc))
    with pytest.raises(ValueError):
        load_manifest(tmp_path / "missing.json")

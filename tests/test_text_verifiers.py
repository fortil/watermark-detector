import pytest
from fixtures.mock_verifier import mock_verifier, write_config

from watermark_detector.text_verifiers import load_configs, run_verifier


def _cfg(tmp_path, url, **ov):
    return load_configs(write_config(tmp_path / "v.toml", url, **ov))["claude"]


def test_score_and_request(tmp_path, monkeypatch):
    monkeypatch.setenv("WMD_TEST_KEY", "test-key")
    with mock_verifier() as m:
        cfg = _cfg(tmp_path, m.url, extra_body={"mode": "x"})
        f = run_verifier(cfg, "hello text")
    assert f.verdict == "score"
    assert f.evidence["score"] == 0.87 and f.evidence["label"] == "likely"
    body = m.requests[0]["body"]
    assert body["text"] == "hello text" and body["mode"] == "x"
    assert "test-key" not in repr(f)


def test_custom_header(tmp_path, monkeypatch):
    monkeypatch.setenv("WMD_TEST_KEY", "test-key")
    with mock_verifier() as m:
        cfg = _cfg(tmp_path, m.url, auth_header="x-api-key", auth_scheme="")
        run_verifier(cfg, "t")
    h = {k.lower(): v for k, v in m.requests[0]["headers"].items()}
    assert h["x-api-key"] == "test-key"


def test_http_500(tmp_path, monkeypatch):
    monkeypatch.setenv("WMD_TEST_KEY", "test-key")
    with mock_verifier(status=500) as m:
        f = run_verifier(_cfg(tmp_path, m.url), "t")
    assert f.verdict == "error" and f.evidence["http_status"] == 500
    assert "test-key" not in repr(f)


def test_missing_env(tmp_path, monkeypatch):
    monkeypatch.delenv("WMD_TEST_KEY", raising=False)
    f = run_verifier(_cfg(tmp_path, "http://127.0.0.1:1/x"), "t")
    assert f.verdict == "not_configured"


def test_missing_path_is_error(tmp_path, monkeypatch):
    monkeypatch.setenv("WMD_TEST_KEY", "test-key")
    with mock_verifier(response={"other": 1}) as m:
        f = run_verifier(_cfg(tmp_path, m.url), "t")
    assert f.verdict == "error"


def test_bad_configs(tmp_path):
    with pytest.raises(ValueError):
        load_configs(write_config(tmp_path / "a.toml", "http://example.com"))
    with pytest.raises(ValueError):
        load_configs(write_config(tmp_path / "b.toml", "https://example.com", name="other"))
    assert load_configs(tmp_path / "missing.toml") == {}
    p = tmp_path / "c.toml"
    p.write_text('[verifiers.claude]\nscore_path = "a"\napi_key_env = "K"\n')
    with pytest.raises(ValueError, match="endpoint"):
        load_configs(p)


def test_repeated_name_key_is_value_error(tmp_path):
    p = tmp_path / "d.toml"
    p.write_text(
        '[verifiers.claude]\nname = "claude"\nendpoint = "https://example.com"\n'
        'score_path = "a"\napi_key_env = "K"\n'
    )
    with pytest.raises(ValueError, match="unknown field name"):
        load_configs(p)

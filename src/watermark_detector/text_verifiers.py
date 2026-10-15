"""Opt-in remote text verifiers. Endpoints come from the user's TOML file."""
from __future__ import annotations

import json
import os
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from watermark_detector.model import Finding

NAMES = ("claude", "gemini", "gpt")


@dataclass(frozen=True, kw_only=True)
class VerifierConfig:
    name: Literal["claude", "gemini", "gpt"]
    endpoint: str
    api_key_env: str
    auth_header: str = "Authorization"
    auth_scheme: str = "Bearer"
    text_field: str = "text"
    extra_body: dict = field(default_factory=dict)
    score_path: str
    label_path: str = ""
    timeout_s: float = 30.0
    max_chars: int = 100_000


def default_config_path() -> Path:
    env = os.environ.get("WMD_CONFIG")
    if env:
        return Path(env)
    return Path.home() / ".config" / "watermark-detector" / "verifiers.toml"


def _check_endpoint(name: str, endpoint: str) -> None:
    u = urlparse(endpoint)
    if u.scheme == "https" and u.hostname:
        return
    if u.scheme == "http" and u.hostname in ("127.0.0.1", "localhost"):
        return
    raise ValueError(f"verifier {name}: endpoint must be https (http only for localhost)")


def load_configs(path: Path | None) -> dict[str, VerifierConfig]:
    if path is None or not Path(path).exists():
        return {}
    with open(path, "rb") as fh:
        doc = tomllib.load(fh)
    out: dict[str, VerifierConfig] = {}
    for name, table in (doc.get("verifiers") or {}).items():
        if name not in NAMES:
            raise ValueError(f"unknown verifier name: {name}")
        if not isinstance(table, dict):
            raise ValueError(f"verifier {name}: expected a table")
        for req in ("endpoint", "score_path", "api_key_env"):
            if not table.get(req):
                raise ValueError(f"verifier {name}: missing field {req}")
        _check_endpoint(name, table["endpoint"])
        allowed = set(VerifierConfig.__dataclass_fields__) - {"name"}
        unknown = set(table) - allowed
        if unknown:
            raise ValueError(f"verifier {name}: unknown field {sorted(unknown)[0]}")
        out[name] = VerifierConfig(name=name, **table)
    return out


def _dig(obj: Any, dotted: str) -> Any:
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            raise KeyError(dotted)
    return cur


def run_verifier(cfg: VerifierConfig, text: str) -> Finding:
    key = os.environ.get(cfg.api_key_env)
    if not key:
        return Finding("text-watermark", "not_configured", cfg.name, "text", {"missing_env": cfg.api_key_env})
    sent = text[: cfg.max_chars]
    host = urlparse(cfg.endpoint).hostname
    body = json.dumps({**cfg.extra_body, cfg.text_field: sent}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    headers[cfg.auth_header] = f"{cfg.auth_scheme} {key}".strip()
    req = urllib.request.Request(cfg.endpoint, data=body, headers=headers, method="POST")

    def err(reason: str, **extra: Any) -> Finding:
        return Finding("text-watermark", "error", cfg.name, "text", {"reason": reason, "endpoint_host": host, **extra})

    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
            status = resp.status
            payload = resp.read(4 * 2**20)
    except urllib.error.HTTPError as e:
        return err(f"HTTP {e.code}", http_status=e.code)
    except urllib.error.URLError as e:
        return err(f"request failed: {type(e.reason).__name__}")
    except (TimeoutError, OSError) as e:
        return err(f"request failed: {type(e).__name__}")
    try:
        doc = json.loads(payload)
        score = _dig(doc, cfg.score_path)
        label = _dig(doc, cfg.label_path) if cfg.label_path else None
    except (ValueError, KeyError):
        return err("response missing score_path or not JSON", http_status=status)
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return err("score is not a number", http_status=status)
    return Finding(
        "text-watermark", "score", cfg.name, "text",
        {
            "score": score, "label": label, "http_status": status, "endpoint_host": host,
            "chars_sent": len(sent), "truncated": len(text) > len(sent),
        },
    )

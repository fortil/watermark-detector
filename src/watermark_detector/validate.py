"""Check real provider samples against a user-written manifest of expectations."""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path

from watermark_detector.detect import DetectOptions, detect_path
from watermark_detector.model import PROVIDER_SIGNAL_VERDICTS, Finding

EXPECT_KEYS = ("layer", "provider", "verdict_in", "location", "score_min", "score_max")
SIGNAL_LAYERS = ("c2pa", "xmp", "aigc-label")


@dataclass(frozen=True)
class SampleResult:
    id: str
    passed: bool
    detail: str


def load_manifest(path: str | Path) -> dict:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"cannot read manifest: {type(e).__name__}") from e
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise ValueError("manifest: version must be 1")
    samples = doc.get("samples")
    if not isinstance(samples, list):
        raise ValueError("manifest: samples must be a list")
    for i, s in enumerate(samples):
        if not isinstance(s, dict):
            raise ValueError(f"sample {i}: expected an object")
        if not isinstance(s.get("id"), str) or not s["id"]:
            raise ValueError(f"sample {i}: id must be a non-empty string")
        if not isinstance(s.get("path"), str) or not s["path"]:
            raise ValueError(f"sample {s['id']}: path must be a non-empty string")
        anchors = s.get("anchors", [])
        if not isinstance(anchors, list) or not all(isinstance(a, str) for a in anchors):
            raise ValueError(f"sample {s['id']}: anchors must be a list of paths")
        expect = s.get("expect")
        if not isinstance(expect, dict) or not expect:
            raise ValueError(f"sample {s['id']}: expect must be a non-empty object")
        if "no_provider_signal" in expect:
            if expect != {"no_provider_signal": True}:
                raise ValueError(f"sample {s['id']}: no_provider_signal must be the only key, set to true")
            continue
        unknown = set(expect) - set(EXPECT_KEYS)
        if unknown:
            raise ValueError(f"sample {s['id']}: unknown expect key {sorted(unknown)[0]}")
        if "verdict_in" in expect and not (
            isinstance(expect["verdict_in"], list) and all(isinstance(v, str) for v in expect["verdict_in"])
        ):
            raise ValueError(f"sample {s['id']}: verdict_in must be a list of strings")
        for k in ("score_min", "score_max"):
            if k in expect and (isinstance(expect[k], bool) or not isinstance(expect[k], (int, float))):
                raise ValueError(f"sample {s['id']}: {k} must be a number")
    return doc


def _matches(f: Finding, expect: dict) -> bool:
    if "layer" in expect and f.layer != expect["layer"]:
        return False
    if "provider" in expect and f.provider != expect["provider"]:
        return False
    if "verdict_in" in expect and f.verdict not in expect["verdict_in"]:
        return False
    if "location" in expect and f.location != expect["location"]:
        return False
    if "score_min" in expect or "score_max" in expect:
        score = f.evidence.get("score")
        if not isinstance(score, (int, float)):
            return False
        if "score_min" in expect and score < expect["score_min"]:
            return False
        if "score_max" in expect and score > expect["score_max"]:
            return False
    return True


def _check(findings: list[Finding], expect: dict) -> tuple[bool, str]:
    if expect.get("no_provider_signal"):
        bad = [
            f for f in findings
            if f.layer in SIGNAL_LAYERS and f.provider is not None and f.verdict in PROVIDER_SIGNAL_VERDICTS
        ]
        if bad:
            return False, "expected no provider signal, found " + ", ".join(
                f"{f.layer}/{f.provider}/{f.verdict}@{f.location}" for f in bad
            )
        return True, "no provider signal"
    for f in findings:
        if _matches(f, expect):
            return True, f"{f.layer}/{f.provider}/{f.verdict}@{f.location}"
    seen = ", ".join(f"{f.layer}/{f.provider}/{f.verdict}@{f.location}" for f in findings) or "no findings"
    return False, f"no finding matches {json.dumps(expect, sort_keys=True)}; got: {seen}"


def run_manifest(path: str | Path, opts: DetectOptions = DetectOptions()) -> list[SampleResult]:
    doc = load_manifest(path)
    base = Path(path).resolve().parent
    results: list[SampleResult] = []
    for s in doc["samples"]:
        try:
            pems = tuple((base / a).read_text(encoding="utf-8") for a in s.get("anchors", []))
        except (OSError, UnicodeDecodeError) as e:
            results.append(SampleResult(s["id"], False, f"cannot read anchor: {type(e).__name__}"))
            continue
        sample_opts = dataclasses.replace(opts, anchors_pem=opts.anchors_pem + pems)
        report = detect_path(base / s["path"], sample_opts)
        if report.errors:
            results.append(SampleResult(s["id"], False, "; ".join(report.errors)))
            continue
        ok, detail = _check(report.findings, s["expect"])
        results.append(SampleResult(s["id"], ok, detail))
    return results

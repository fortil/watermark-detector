"""Turn reports into JSON and text."""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

import c2pa

from watermark_detector import __version__
from watermark_detector.model import PROVIDER_SIGNAL_VERDICTS, Finding, Report

SCHEMA = "watermark-detector/report@1"
UNSIGNED_LINE = "Unsigned metadata: anyone can add or remove it."
ABSENCE_NOTE = (
    "No provider provenance signal found. This does not show the content is human-made: "
    "C2PA, XMP and EXIF/MP4 metadata labels (such as China's GB 45438 AIGC label) are removed by "
    "screenshots, re-saving and format conversion, and text watermarks can only be checked with "
    "the provider's detector."
)


def _summary(r: Report) -> dict[str, Any]:
    signals: dict[str, set[str]] = {}
    for f in r.findings:
        if f.provider and (f.verdict in PROVIDER_SIGNAL_VERDICTS or f.verdict == "score"):
            signals.setdefault(f.provider, set()).add(f.verdict)
    out: dict[str, Any] = {
        "provider_signals": {p: sorted(v) for p, v in sorted(signals.items())},
        "ai_unknown_provider": sum(1 for f in r.findings if f.verdict == "ai_unknown_provider"),
        "ai_label_unattributed": sum(
            1 for f in r.findings
            if f.layer == "aigc-label" and f.provider is None and f.verdict == "unsigned_hint"
        ),
    }
    if not signals:
        out["absence_note"] = ABSENCE_NOTE
    return out


def report_to_dict(r: Report) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "tool_version": __version__,
        "c2pa_sdk": c2pa.sdk_version(),
        "path": r.path,
        "kind": r.kind,
        "mime": r.mime,
        "findings": [asdict(f) for f in r.findings],
        "coverage": r.coverage,
        "errors": r.errors,
        "summary": _summary(r),
    }


def render_json(reports: list[Report]) -> str:
    return json.dumps([report_to_dict(r) for r in reports], indent=2, sort_keys=True, ensure_ascii=False)


def _finding_line(f: Finding) -> str:
    line = f"  {f.layer} {f.provider or '-'} {f.verdict.upper()} @{f.location}"
    ev = f.evidence
    if f.layer == "aigc-label" and f.verdict == "unsigned_hint":
        line += f" producer={ev.get('content_producer')} label={ev.get('label')}"
    elif f.verdict == "score":
        line += f" score={ev.get('score')}"
    elif isinstance(ev.get("signer_subject"), dict) and ev["signer_subject"]:
        s = ev["signer_subject"]
        line += f" {s.get('O', '?')}/{s.get('CN', '?')}"
    elif f.verdict == "error":
        line += f" {ev.get('reason') or ev.get('error') or ''}".rstrip()
    return line


def render_text(r: Report) -> str:
    lines = [f"{r.path} [{r.kind}, {r.mime}]"]
    notes: list[str] = []
    for f in r.findings:
        lines.append(_finding_line(f))
        n = f.evidence.get("note")
        if f.verdict == "claimed" and n and n not in notes:
            notes.append(n)
    lines += [f"  note: {n}" for n in notes]
    if any(f.layer == "aigc-label" for f in r.findings):
        lines.append(f"  {UNSIGNED_LINE}")
    lines += [f"  error: {e}" for e in r.errors]
    if r.coverage:
        lines.append("  coverage:")
        for c in r.coverage:
            lines.append(f"    {c['provider']}: {c['signal']} [{c['status']}]")
    summ = _summary(r)
    if "absence_note" in summ:
        lines.append(f"  {summ['absence_note']}")
    return "\n".join(lines)

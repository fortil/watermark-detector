"""Run every check that applies to one file and collect a Report."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from watermark_detector.aigc_label import aigc_label_findings
from watermark_detector.c2pa_reader import build_context, read_c2pa
from watermark_detector.capabilities import coverage_for
from watermark_detector.containers import ScanResult, scan_ooxml, scan_pdf
from watermark_detector.model import Finding, Kind, Report
from watermark_detector.providers import attribute
from watermark_detector.sniff import sniff_bytes
from watermark_detector.text_verifiers import default_config_path, load_configs, run_verifier
from watermark_detector.textio import WORD_MIME, extract_text, word_count
from watermark_detector.xmp import xmp_findings

MAX_INPUT_BYTES = 512 * 2**20


@dataclass(frozen=True)
class DetectOptions:
    anchors_pem: tuple[str, ...] = ()
    remote: bool = False
    config_path: Path | None = None


def _media_findings(scan: ScanResult, ctx) -> list[Finding]:
    out: list[Finding] = []
    for m in scan.media:
        kind: Kind = "svg" if m.mime == "image/svg+xml" else "image"
        out += attribute(read_c2pa(m.data, m.mime, ctx), m.location)
        out += xmp_findings(m.data, m.location)
        out += aigc_label_findings(m.data, kind, m.mime, m.location)
    if scan.skipped > 0:
        out.append(
            Finding("container", "skipped", None, "file", {"count": scan.skipped, "notes": list(scan.notes)})
        )
    elif scan.notes:
        # The container could not be scanned fully (bad zip, bad PDF, too many members).
        out.append(
            Finding("container", "error", None, "file", {"reason": scan.notes[0], "notes": list(scan.notes)})
        )
    return out


def detect_path(path: str | Path, opts: DetectOptions = DetectOptions()) -> Report:
    path = Path(path)
    report = Report(str(path), "unknown", None, [], [], [])
    try:
        if os.stat(path).st_size > MAX_INPUT_BYTES:
            report.errors.append("file too large")
            return report
        data = path.read_bytes()
    except OSError as e:
        report.errors.append(f"cannot read file: {type(e).__name__}")
        return report
    kind, mime = sniff_bytes(data)
    report.kind, report.mime = kind, mime
    findings = report.findings
    ctx = build_context(opts.anchors_pem)

    if kind in ("image", "svg"):
        assert mime is not None
        findings += attribute(read_c2pa(data, mime, ctx), "file")
        findings += xmp_findings(data, "file")
        findings += aigc_label_findings(data, kind, mime, "file")
    elif kind == "pdf":
        findings += attribute(read_c2pa(data, "application/pdf", ctx), "file")
        findings += aigc_label_findings(data, "pdf", mime, "file")
        findings += _media_findings(scan_pdf(data), ctx)
    elif kind == "ooxml":
        assert mime is not None
        findings += attribute(read_c2pa(data, mime, ctx), "file")
        findings += aigc_label_findings(data, "ooxml", mime, "file")
        findings += _media_findings(scan_ooxml(data), ctx)
    elif kind == "video":
        findings += aigc_label_findings(data, "video", mime, "file")
    elif kind == "unknown":
        report.errors.append("unsupported file type")
        return report

    configs = {}
    if kind in ("text", "pdf") or (kind == "ooxml" and mime == WORD_MIME):
        try:
            configs = load_configs(opts.config_path or default_config_path())
        except ValueError as e:
            report.errors.append(f"verifier config error: {e}")
        text = extract_text(data, kind, mime)
        if text is not None:
            wc = word_count(text)
            for name, cfg in configs.items():
                if opts.remote:
                    f = run_verifier(cfg, text)
                    findings.append(Finding(f.layer, f.verdict, f.provider, f.location, {**f.evidence, "word_count": wc}))
                else:
                    findings.append(
                        Finding(
                            "text-watermark", "not_run", name, "text",
                            {"reason": "remote verification disabled; pass --remote", "word_count": wc},
                        )
                    )
    report.coverage = coverage_for(kind, frozenset(configs), opts.remote)
    return report

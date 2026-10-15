"""Command line entry point."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from watermark_detector import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wmd",
        description="Detect AI provenance signals in files (detection only).",
    )
    parser.add_argument("--version", action="version", version=f"wmd {__version__}")
    sub = parser.add_subparsers(dest="command")

    d = sub.add_parser("detect", help="check files for provenance signals")
    d.add_argument("paths", nargs="+", metavar="PATH")
    d.add_argument("--json", action="store_true", help="print JSON instead of text")
    d.add_argument("--anchors", action="append", default=[], metavar="PEM_FILE",
                   help="trust anchor to pin (repeatable)")
    d.add_argument("--remote", action="store_true", help="run configured remote text verifiers")
    d.add_argument("--config", metavar="TOML", help="verifier config file")

    p = sub.add_parser("providers", help="show what can and cannot be checked")
    p.add_argument("--json", action="store_true")

    c = sub.add_parser("certs", help="list certificates in a signed file")
    c.add_argument("path", metavar="PATH")
    c.add_argument("-o", "--out", metavar="OUT_PEM", help="write the certificates to this file")

    v = sub.add_parser("validate", help="check real samples against a manifest")
    v.add_argument("manifest", metavar="MANIFEST")
    v.add_argument("--remote", action="store_true")
    v.add_argument("--config", metavar="TOML")
    return parser


def _read_anchors(paths: list[str]) -> tuple[str, ...]:
    return tuple(Path(p).read_text(encoding="utf-8") for p in paths)


def _cmd_detect(args) -> int:
    from watermark_detector.detect import DetectOptions, detect_path
    from watermark_detector.report import render_json, render_text

    try:
        anchors = _read_anchors(args.anchors)
    except (OSError, UnicodeDecodeError) as e:
        print(f"cannot read anchors: {type(e).__name__}", file=sys.stderr)
        return 1
    opts = DetectOptions(
        anchors_pem=anchors, remote=args.remote,
        config_path=Path(args.config) if args.config else None,
    )
    reports = [detect_path(p, opts) for p in args.paths]
    if args.json:
        print(render_json(reports))
    else:
        print("\n\n".join(render_text(r) for r in reports))
    return 1 if any(r.errors for r in reports) else 0


def _cmd_providers(args) -> int:
    from watermark_detector.capabilities import CAPABILITIES

    if args.json:
        print(json.dumps([dataclasses.asdict(c) for c in CAPABILITIES], indent=2, ensure_ascii=False))
    else:
        for c in CAPABILITIES:
            print(f"{c.provider:7} {c.modality:9} local={c.local:7} {c.signal}")
            print(f"        check: {c.how_to_check}")
            print(f"        note: {c.notes}")
    return 0


def _cmd_certs(args) -> int:
    from watermark_detector.c2pa_reader import build_context, read_c2pa
    from watermark_detector.certs import extract_certs
    from watermark_detector.sniff import sniff_bytes

    try:
        data = Path(args.path).read_bytes()
    except OSError as e:
        print(f"cannot read file: {type(e).__name__}", file=sys.stderr)
        return 1
    kind, mime = sniff_bytes(data)
    if kind not in ("image", "svg", "pdf", "ooxml") or mime is None:
        print("no certificates found", file=sys.stderr)
        return 1
    result = read_c2pa(data, mime, build_context())
    active = None
    for m in result.manifests:
        if m.is_active:
            active = m.signer_serial
    certs = extract_certs(data, mime, active)
    if not certs:
        print("no certificates found", file=sys.stderr)
        return 1
    for c in certs:
        print(f"#{c.index} sha256={c.sha256} serial={c.serial:x} active_signer={'yes' if c.is_active_signer else 'no'}")
    if args.out:
        try:
            Path(args.out).write_text("".join(c.pem for c in certs), encoding="utf-8")
        except OSError as e:
            print(f"cannot write output: {type(e).__name__}", file=sys.stderr)
            return 1
    return 0


def _cmd_validate(args) -> int:
    from watermark_detector.detect import DetectOptions
    from watermark_detector.validate import run_manifest

    opts = DetectOptions(remote=args.remote, config_path=Path(args.config) if args.config else None)
    try:
        results = run_manifest(args.manifest, opts)
    except ValueError as e:
        print(f"manifest error: {e}", file=sys.stderr)
        return 1
    for r in results:
        print(f"PASS {r.id}" if r.passed else f"FAIL {r.id}: {r.detail}")
    return 0 if all(r.passed for r in results) else 3


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args_list = sys.argv[1:] if argv is None else argv
    if not args_list:
        parser.print_help()
        return 2
    args = parser.parse_args(args_list)
    if args.command is None:
        parser.print_help()
        return 2
    return {
        "detect": _cmd_detect,
        "providers": _cmd_providers,
        "certs": _cmd_certs,
        "validate": _cmd_validate,
    }[args.command](args)

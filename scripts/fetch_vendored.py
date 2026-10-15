"""Download and check the pinned third-party files (stdlib only)."""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = "https://raw.githubusercontent.com/contentauth/c2pa-python/v0.38.0"

LIC_TRUST = "CC-BY-4.0 (c2pa-org/conformance-public)"
LIC_ITL = "public trust anchors, contentcredentials.org legacy Interim Trust List"
LIC_C2PA = "MIT OR Apache-2.0 (contentauth/c2pa-python v0.38.0)"

ITEMS = [
    {
        "key": "c2pa-trust-list",
        "url": "https://raw.githubusercontent.com/c2pa-org/conformance-public/main/trust-list/C2PA-TRUST-LIST.pem",
        "dest": "src/watermark_detector/trust/C2PA-TRUST-LIST.pem",
        "sha256": "75cacc98b79ecac33713c7ecfb58d4a0ef383f3c1f886e7409f9e37e8664aea5",
        "immutable": False,
        "must_contain": b"Google C2PA Root CA G3",
        "license": LIC_TRUST,
    },
    {
        "key": "itl-anchors",
        "url": "https://contentcredentials.org/trust/anchors.pem",
        "dest": "src/watermark_detector/trust/ITL-ANCHORS.pem",
        "sha256": "db57e50b9bd4e4c786cbb91f38fd85e2af6a9d5412438a8cddcc42688df07ae5",
        "immutable": False,
        "must_contain": b"Truepic",
        "license": LIC_ITL,
    },
    {
        "key": "c2pa-python-C",
        "url": f"{RAW}/tests/fixtures/C.jpg",
        "dest": "tests/fixtures/third_party/C.jpg",
        "sha256": "4cbac1af485155f878d12a610da851c2938f2ce886189c61d9da7a0a43bd00b5",
        "immutable": True,
        "must_contain": None,
        "license": LIC_C2PA,
    },
    {
        "key": "c2pa-python-A",
        "url": f"{RAW}/tests/fixtures/A.jpg",
        "dest": "tests/fixtures/third_party/A.jpg",
        "sha256": "f999fd78bfe8a83c96e468a078830ba94485bc1bc6fd086fb94a43bd29dd0f23",
        "immutable": True,
        "must_contain": None,
        "license": LIC_C2PA,
    },
    {
        "key": "c2pa-python-license",
        "url": f"{RAW}/LICENSE-MIT",
        "dest": "tests/fixtures/third_party/LICENSE-c2pa-python-MIT.txt",
        "sha256": "89375a50de90d2dcaa04406086da832ad452ebcaf6ab402ef3d51b8401a67c71",
        "immutable": True,
        "must_contain": None,
        "license": LIC_C2PA,
    },
]

PEM_RE = re.compile(
    rb"-----BEGIN CERTIFICATE-----(.+?)-----END CERTIFICATE-----", re.S
)


def pem_blocks(data: bytes) -> list[bytes]:
    out = []
    for m in PEM_RE.finditer(data):
        try:
            out.append(base64.b64decode(b"".join(m.group(1).split())))
        except ValueError:
            continue
    return out


def sources_path(dest: Path) -> Path:
    return dest.parent / "SOURCES.json"


def load_sources(dest: Path) -> dict:
    p = sources_path(dest)
    if p.exists():
        return json.loads(p.read_text())
    return {"files": {}}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": "watermark-detector-vendor/0.1"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def download() -> int:
    rc = 0
    today = datetime.date.today().isoformat()
    for it in ITEMS:
        dest = ROOT / it["dest"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = fetch(it["url"])
        digest = hashlib.sha256(data).hexdigest()
        notes = ""
        if digest != it["sha256"]:
            if it["immutable"]:
                print(f"MISMATCH {it['key']}")
                rc = 1
                continue
            print(f"CHANGED {it['key']} {digest}")
            notes = f"upstream changed after 2026-10-10; expected {it['sha256']}"
        dest.write_bytes(data)
        certs = len(pem_blocks(data)) if dest.suffix == ".pem" else None
        src = load_sources(dest)
        src["files"][dest.name] = {
            "url": it["url"],
            "sha256": digest,
            "fetched_at": today,
            "certificates": certs,
            "license": it["license"],
            "notes": notes,
        }
        sources_path(dest).write_text(json.dumps(src, indent=2) + "\n")
    return rc


def verify_only() -> int:
    ok_all = True
    for it in ITEMS:
        dest = ROOT / it["dest"]
        problem = None
        if not dest.exists():
            problem = "missing file"
        else:
            data = dest.read_bytes()
            rec = load_sources(dest)["files"].get(dest.name)
            if rec is None:
                problem = "not in SOURCES.json"
            elif hashlib.sha256(data).hexdigest() != rec["sha256"]:
                problem = "sha256 differs from SOURCES.json"
            elif dest.suffix == ".pem":
                blocks = pem_blocks(data)
                if not blocks:
                    problem = "no certificate blocks"
                elif it["must_contain"] and not any(
                    it["must_contain"] in b for b in blocks
                ):
                    problem = f"no block contains {it['must_contain']!r}"
        if problem:
            ok_all = False
            print(f"FAIL {it['key']}: {problem}")
        else:
            print(f"OK {it['key']}")
    return 0 if ok_all else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()
    return verify_only() if args.verify_only else download()


if __name__ == "__main__":
    sys.exit(main())

"""Read China's GB 45438 implicit AI-content label (unsigned metadata)."""
from __future__ import annotations

import html
import io
import json
import re
import struct
import zipfile
import zlib
from dataclasses import dataclass
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from watermark_detector import bmff
from watermark_detector.model import Finding, Kind
from watermark_detector.providers import match_aigc_producer
from watermark_detector.xmp import extract_xmp_packets

LABEL_MEANINGS = {"1": "AI-generated", "2": "possibly AI-generated", "3": "suspected AI-generated"}
MAX_LABEL_BYTES = 64 * 1024
MAX_IFD_ENTRIES = 512
MAX_INFLATE_BYTES = 256 * 1024
MAX_CUSTOM_XML_BYTES = 1 << 20
NOTE = "Unsigned metadata: anyone can add or remove it."
STANDARD = "GB 45438-2025 Annex E"

_USCC_RE = re.compile(r"^[0-9A-HJ-NPQRTUWXY]{2}[0-9]{6}[0-9A-HJ-NPQRTUWXY]{10}$")
PNG_SIG = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class LabelHit:
    container: str
    raw: str


def parse_label_json(text: str) -> dict[str, str] | None:
    try:
        obj = json.loads(text.strip())
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    inner = obj.get("AIGC")
    if isinstance(inner, dict):
        obj = inner
    if "Label" not in obj and "ContentProducer" not in obj:
        return None
    return {str(k): str(v) for k, v in obj.items()}


def producer_uscc(code: str | None) -> str | None:
    if not code:
        return None
    if len(code) == 27 and code[:2] == "00" and code[2] == "1" and code[3] == "1":
        return code[4:22]
    if len(code) == 18 and _USCC_RE.match(code):
        return code
    return None


def redact_code(code: str | None) -> str | None:
    if code is not None and len(code) == 27 and code[2] == "2":
        return code[:4] + "<redacted>" + code[22:]
    return code


# ---- JPEG EXIF ------------------------------------------------------------

def _ifd_entries(tiff: bytes, off: int, e: str) -> list[tuple[int, int, int, bytes]]:
    """Return (tag, type, count, value_field) for the entries of one IFD."""
    if off < 0 or off + 2 > len(tiff):
        return []
    n = struct.unpack(e + "H", tiff[off:off + 2])[0]
    n = min(n, MAX_IFD_ENTRIES)
    out = []
    for i in range(n):
        p = off + 2 + 12 * i
        if p + 12 > len(tiff):
            break
        tag, typ, cnt = struct.unpack(e + "HHI", tiff[p:p + 8])
        out.append((tag, typ, cnt, tiff[p + 8:p + 12]))
    return out


def _user_comment(tiff: bytes) -> str | None:
    if len(tiff) < 8:
        return None
    if tiff[:2] == b"II":
        e = "<"
    elif tiff[:2] == b"MM":
        e = ">"
    else:
        return None
    if struct.unpack(e + "H", tiff[2:4])[0] != 42:
        return None
    ifd0 = struct.unpack(e + "I", tiff[4:8])[0]
    exif_off = None
    for tag, _typ, _cnt, val in _ifd_entries(tiff, ifd0, e):
        if tag == 0x8769:
            exif_off = struct.unpack(e + "I", val)[0]
            break
    if exif_off is None:
        return None
    for tag, typ, cnt, val in _ifd_entries(tiff, exif_off, e):
        if tag != 0x9286 or typ != 7:
            continue
        if cnt > 4:
            off = struct.unpack(e + "I", val)[0]
            if off + cnt > len(tiff):
                return None
            raw = tiff[off:off + cnt]
        else:
            raw = val[:cnt]
        if len(raw) < 8:
            return None
        prefix, body = raw[:8], raw[8:]
        if prefix == b"UNICODE\x00":
            text = body.decode("utf-16-le" if e == "<" else "utf-16-be", errors="replace")
        else:
            text = body.decode("utf-8", errors="replace")
        return text.rstrip("\x00 ")
    return None


def exif_user_comments(jpeg: bytes) -> list[LabelHit]:
    hits: list[LabelHit] = []
    pos = 2
    n = len(jpeg)
    while pos + 1 < n and jpeg[pos] == 0xFF:
        marker = jpeg[pos + 1]
        if marker == 0xFF:
            pos += 1
            continue
        if marker in (0xDA, 0xD9):
            break
        if 0xD0 <= marker <= 0xD7 or marker == 0x01:
            pos += 2
            continue
        if pos + 4 > n:
            break
        length = struct.unpack(">H", jpeg[pos + 2:pos + 4])[0]
        if length < 2:
            break
        payload = jpeg[pos + 4:pos + 2 + length]
        pos += 2 + length
        if marker == 0xE1 and payload.startswith(b"Exif\x00\x00"):
            try:
                text = _user_comment(payload[6:])
            except struct.error:
                text = None
            if text and ("AIGC" in text or "ContentProducer" in text):
                hits.append(LabelHit("exif:UserComment", text))
    return hits


# ---- PNG text chunks ----------------------------------------------------------

def _inflate(buf: bytes) -> str:
    return zlib.decompressobj().decompress(buf, MAX_INFLATE_BYTES).decode("utf-8", errors="replace")


def png_text_labels(png: bytes) -> list[LabelHit]:
    hits: list[LabelHit] = []
    pos = 8
    while pos + 8 <= len(png):
        length, ctype = struct.unpack(">I4s", png[pos:pos + 8])
        body = png[pos + 8:pos + 8 + length]
        if len(body) < length:
            break
        pos += 12 + length
        if ctype == b"IEND":
            break
        if ctype not in (b"tEXt", b"zTXt", b"iTXt"):
            continue
        kw_end = body.find(b"\x00")
        if kw_end < 0:
            continue
        keyword = body[:kw_end].decode("latin-1")
        if "aigc" not in keyword.lower():
            continue
        rest = body[kw_end + 1:]
        try:
            if ctype == b"tEXt":
                text = rest.decode("latin-1")
            elif ctype == b"zTXt":
                text = _inflate(rest[1:])
            else:
                compressed = rest[0] == 1
                rest = rest[2:]
                i = rest.find(b"\x00")
                rest = rest[i + 1:]
                i = rest.find(b"\x00")
                raw = rest[i + 1:]
                text = _inflate(raw) if compressed else raw.decode("utf-8", errors="replace")
        except (zlib.error, IndexError):
            continue
        hits.append(LabelHit(f"png:{ctype.decode()}:{keyword}", text))
    return hits


# ---- XMP ------------------------------------------------------------------------

_ATTR_RE = [
    re.compile(r'\b([A-Za-z_][\w.-]*):AIGC\s*=\s*"([^"]*)"'),
    re.compile(r"\b([A-Za-z_][\w.-]*):AIGC\s*=\s*'([^']*)'"),
]
_ELEM_RE = re.compile(r"<([A-Za-z_][\w.-]*):AIGC\b[^>]*>([\s\S]*?)</\1:AIGC>")
_TAG_RE = re.compile(r"<[^>]*>")


def _xmp_hits(data: bytes) -> list[tuple[LabelHit, str | None]]:
    out: list[tuple[LabelHit, str | None]] = []
    for packet in extract_xmp_packets(data):
        found: list[tuple[str, str]] = []
        for rx in _ATTR_RE:
            found += [(m.group(1), html.unescape(m.group(2))) for m in rx.finditer(packet)]
        for m in _ELEM_RE.finditer(packet):
            found.append((m.group(1), html.unescape(_TAG_RE.sub("", m.group(2)))))
        for prefix, value in found:
            ns = re.search(r'xmlns:' + re.escape(prefix) + r'\s*=\s*["\']([^"\']*)["\']', packet)
            out.append((LabelHit(f"xmp:{prefix}:AIGC", value), ns.group(1) if ns else None))
    return out


def xmp_labels(data: bytes) -> list[LabelHit]:
    return [h for h, _ in _xmp_hits(data)]


def _xmp_namespaces(data: bytes) -> dict[tuple[str, str], str | None]:
    return {(h.container, h.raw): ns for h, ns in _xmp_hits(data)}


# ---- OOXML custom properties and PDF Info ---------------------------------------

_PROP_RE = re.compile(r"<(?:\w+:)?property\b([^>]*)>([\s\S]*?)</(?:\w+:)?property>")
_NAME_RE = re.compile(r'\bname\s*=\s*"([^"]*)"')
_LPWSTR_RE = re.compile(r"<(?:\w+:)?lpwstr\b[^>]*>([\s\S]*?)</(?:\w+:)?lpwstr>")


def ooxml_labels(data: bytes) -> list[LabelHit]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            try:
                info = z.getinfo("docProps/custom.xml")
            except KeyError:
                return []
            if info.file_size > MAX_CUSTOM_XML_BYTES:
                return []
            xml = z.read(info).decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, OSError, ValueError, RuntimeError):
        return []
    hits: list[LabelHit] = []
    for m in _PROP_RE.finditer(xml):
        nm = _NAME_RE.search(m.group(1))
        if not nm:
            continue
        name = html.unescape(nm.group(1))
        if "AIGC" not in name:
            continue
        val = _LPWSTR_RE.search(m.group(2))
        if val:
            hits.append(LabelHit(f"ooxml:docProps/custom.xml:{name}", html.unescape(val.group(1))))
    return hits


def pdf_info_labels(data: bytes) -> list[LabelHit]:
    try:
        meta = PdfReader(io.BytesIO(data)).metadata
        if meta is None:
            return []
        return [
            LabelHit(f"pdf:info:{key}", str(value))
            for key, value in meta.items()
            if "AIGC" in str(key)
        ]
    except (PyPdfError, ValueError):
        return []


# ---- dispatch -------------------------------------------------------------------

def extract_label_hits(data: bytes, kind: Kind, mime: str | None) -> list[LabelHit]:
    hits: list[LabelHit] = []
    if kind == "image":
        if mime == "image/jpeg":
            hits += exif_user_comments(data)
        elif mime == "image/png":
            hits += png_text_labels(data)
        hits += xmp_labels(data)
    elif kind == "svg":
        hits += xmp_labels(data)
    elif kind == "video":
        for path, key, value in bmff.mp4_metadata_items(data):
            if "AIGC" in key:
                hits.append(LabelHit(f"mp4:{path}/keys:{key}", value))
        hits += xmp_labels(data)
    elif kind == "pdf":
        hits += pdf_info_labels(data)
        hits += xmp_labels(data)
    elif kind == "ooxml":
        hits += ooxml_labels(data)
    seen: set[tuple[str, str]] = set()
    out: list[LabelHit] = []
    for h in hits:
        k = (h.container, h.raw)
        if k in seen or len(h.raw.encode("utf-8", errors="replace")) > MAX_LABEL_BYTES:
            continue
        seen.add(k)
        out.append(h)
    return out


def aigc_label_findings(data: bytes, kind: Kind, mime: str | None, location: str) -> list[Finding]:
    out: list[Finding] = []
    namespaces: dict[tuple[str, str], str | None] | None = None
    for hit in extract_label_hits(data, kind, mime):
        obj = parse_label_json(hit.raw)
        if obj is None:
            out.append(
                Finding(
                    "aigc-label", "error", None, location,
                    {"container": hit.container, "reason": "invalid AIGC JSON", "raw_prefix": hit.raw[:80]},
                )
            )
            continue
        uscc = producer_uscc(obj.get("ContentProducer"))
        provider = match_aigc_producer(uscc)
        label = obj.get("Label")
        evidence: dict[str, Any] = {
            "container": hit.container,
            "standard": STANDARD,
            "label": label,
            "label_meaning": LABEL_MEANINGS.get(label or ""),
            "content_producer": redact_code(obj.get("ContentProducer")),
            "producer_uscc": uscc,
            "produce_id": obj.get("ProduceID"),
            "content_propagator": redact_code(obj.get("ContentPropagator")),
            "propagate_id": obj.get("PropagateID"),
            "reserved_code1_present": bool(obj.get("ReservedCode1")),
            "reserved_code2_present": bool(obj.get("ReservedCode2")),
            "note": NOTE,
        }
        if hit.container.startswith("xmp:"):
            if namespaces is None:
                namespaces = _xmp_namespaces(data)
            evidence["xmp_namespace"] = namespaces.get((hit.container, hit.raw))
        out.append(Finding("aigc-label", "unsigned_hint", provider, location, evidence))
    return out

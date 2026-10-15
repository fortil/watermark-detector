"""Find unsigned IPTC AI markers in XMP packets."""
from __future__ import annotations

import re
import struct
import zlib
from dataclasses import dataclass

from watermark_detector.model import AI_SOURCE_TYPES, Finding

PNG_SIG = b"\x89PNG\r\n\x1a\n"
MAX_PACKETS = 16
MAX_INFLATE = 4 * 1024 * 1024
_PACKET_RE = re.compile(rb"<x:xmpmeta[\s\S]*?</x:xmpmeta>")
_DST_RE = re.compile(r"digitalsourcetype/([A-Za-z]+)")
_CREDIT_RE = re.compile(
    r"<photoshop:Credit>([^<]*)</photoshop:Credit>|photoshop:Credit=[\"']([^\"']*)[\"']"
)
NOTE = "Unsigned metadata: anyone can add or remove it."


def _png_xmp(data: bytes) -> list[bytes]:
    out: list[bytes] = []
    pos = 8
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if len(body) < length:
            break
        pos += 12 + length
        if ctype == b"IEND":
            break
        if ctype != b"iTXt":
            continue
        kw_end = body.find(b"\x00")
        if kw_end < 0 or body[:kw_end] != b"XML:com.adobe.xmp":
            continue
        rest = body[kw_end + 1:]
        if len(rest) < 2:
            continue
        compressed = rest[0] == 1
        rest = rest[2:]
        lang_end = rest.find(b"\x00")
        if lang_end < 0:
            continue
        rest = rest[lang_end + 1:]
        tr_end = rest.find(b"\x00")
        if tr_end < 0:
            continue
        text = rest[tr_end + 1:]
        if compressed:
            try:
                text = zlib.decompressobj().decompress(text, MAX_INFLATE)
            except zlib.error:
                continue
        out.append(text)
    return out


def extract_xmp_packets(data: bytes) -> list[str]:
    raw: list[bytes] = []
    if data.startswith(PNG_SIG):
        raw.extend(_png_xmp(data))
    raw.extend(m.group(0) for m in _PACKET_RE.finditer(data))
    seen: list[str] = []
    for b in raw:
        s = b.decode("utf-8", errors="replace")
        if s not in seen:
            seen.append(s)
        if len(seen) >= MAX_PACKETS:
            break
    return seen


@dataclass(frozen=True)
class XmpFields:
    digital_source_types: tuple[str, ...]
    credits: tuple[str, ...]


def parse_ai_fields(packet: str) -> XmpFields:
    dsts = tuple(_DST_RE.findall(packet))
    credits = tuple(a or b for a, b in _CREDIT_RE.findall(packet))
    return XmpFields(dsts, credits)


def xmp_findings(data: bytes, location: str) -> list[Finding]:
    out: list[Finding] = []
    for packet in extract_xmp_packets(data):
        f = parse_ai_fields(packet)
        if not set(f.digital_source_types) & AI_SOURCE_TYPES:
            continue
        provider = "gemini" if "Made with Google AI" in f.credits else None
        out.append(
            Finding(
                "xmp", "unsigned_hint", provider, location,
                {
                    "digital_source_types": list(f.digital_source_types),
                    "credits": list(f.credits),
                    "note": NOTE,
                },
            )
        )
    return out

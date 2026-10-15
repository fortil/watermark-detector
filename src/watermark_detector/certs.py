"""Pull certificates out of a signed file so the user can pin an anchor."""
from __future__ import annotations

import base64
import binascii
import hashlib
import re
import ssl
from dataclasses import dataclass

_CERT_RE = re.compile(rb"\x30\x82(..)\x30\x82..\xa0\x03\x02\x01\x02", re.S)
_SVG_MANIFEST_RE = re.compile(rb"<c2pa:manifest>([\s\S]*?)</c2pa:manifest>")


@dataclass(frozen=True)
class CertInfo:
    index: int
    sha256: str
    serial: int
    der: bytes
    pem: str
    is_active_signer: bool


def _buffer(data: bytes, mime: str) -> bytes:
    if mime != "image/svg+xml":
        return data
    out = b""
    for m in _SVG_MANIFEST_RE.finditer(data):
        try:
            out += base64.b64decode(m.group(1), validate=False)
        except (binascii.Error, ValueError):
            continue
    return out


def extract_certs(data: bytes, mime: str, active_serial: int | None) -> list[CertInfo]:
    buf = _buffer(data, mime)
    certs: list[CertInfo] = []
    seen: set[str] = set()
    for m in _CERT_RE.finditer(buf):
        start = m.start()
        length = int.from_bytes(m.group(1), "big")
        der = buf[start:start + 4 + length]
        if len(der) != 4 + length:
            continue
        digest = hashlib.sha256(der).hexdigest()
        if digest in seen:
            continue
        p = start + 13  # past the 8-byte header pair and the 5-byte version field
        if p + 2 > len(buf) or buf[p] != 0x02 or buf[p + 1] > 0x7F:
            continue
        slen = buf[p + 1]
        serial = int.from_bytes(buf[p + 2:p + 2 + slen], "big")
        seen.add(digest)
        certs.append(
            CertInfo(
                index=len(certs),
                sha256=digest,
                serial=serial,
                der=der,
                pem=ssl.DER_cert_to_PEM_cert(der),
                is_active_signer=active_serial is not None and serial == active_serial,
            )
        )
    return certs

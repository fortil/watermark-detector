"""Decide what kind of file a byte buffer is."""
from __future__ import annotations

import io
import zipfile

from watermark_detector.model import Kind

_OOXML_BASE = "application/vnd.openxmlformats-officedocument."
OOXML_MIMES = {
    "word/": _OOXML_BASE + "wordprocessingml.document",
    "xl/": _OOXML_BASE + "spreadsheetml.sheet",
    "ppt/": _OOXML_BASE + "presentationml.presentation",
}

VIDEO_BRANDS = frozenset(
    {
        "isom", "iso2", "iso4", "iso5", "iso6", "mp41", "mp42", "avc1",
        "M4V ", "qt  ", "3gp4", "3gp5", "3gp6", "dash",
    }
)
_AVIF_BRANDS = frozenset({"avif", "avis"})
_HEIC_BRANDS = frozenset({"heic", "heix", "mif1", "heif"})


def _sniff_zip(data: bytes) -> tuple[Kind, str | None]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = z.namelist()
    except zipfile.BadZipFile:
        return "unknown", None
    if "[Content_Types].xml" not in names:
        return "unknown", None
    for prefix, mime in OOXML_MIMES.items():
        if any(n.startswith(prefix) for n in names):
            return "ooxml", mime
    return "ooxml", None


def sniff_bytes(data: bytes) -> tuple[Kind, str | None]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image", "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image", "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image", "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image", "image/webp"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return "image", "image/tiff"
    if data[4:8] == b"ftyp":
        brand = data[8:12].decode("latin-1")
        if brand in _AVIF_BRANDS:
            return "image", "image/avif"
        if brand in _HEIC_BRANDS:
            return "image", "image/heic"
        if brand == "qt  ":
            return "video", "video/quicktime"
        if brand in VIDEO_BRANDS:
            return "video", "video/mp4"
    if data.startswith(b"%PDF-"):
        return "pdf", "application/pdf"
    if data.startswith(b"PK\x03\x04"):
        kind, mime = _sniff_zip(data)
        if kind != "unknown":
            return kind, mime
        return "unknown", None
    head = data[:4096]
    stripped = head.lstrip(b"\xef\xbb\xbf").lstrip()
    # SVG: also allow a BOM in front.
    text_head = stripped.decode("utf-8", errors="replace")
    if text_head.startswith("<svg") or (
        text_head.startswith("<?xml") and "<svg" in text_head
    ):
        return "svg", "image/svg+xml"
    if b"\x00" not in head:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            return "unknown", None
        return "text", "text/plain"
    return "unknown", None

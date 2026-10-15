"""Find embedded images inside OOXML and PDF files."""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PyPdfError
from pypdf.generic import IndirectObject

from watermark_detector.sniff import sniff_bytes

MAX_MEMBERS = 2000
MAX_MEMBER_BYTES = 64 * 2**20
MAX_TOTAL_BYTES = 512 * 2**20
MAX_FORM_DEPTH = 3
REENCODED_NOTE = "image re-encoded in PDF; C2PA cannot survive"


@dataclass(frozen=True)
class EmbeddedMedia:
    location: str
    mime: str
    data: bytes


@dataclass(frozen=True)
class ScanResult:
    media: tuple[EmbeddedMedia, ...]
    skipped: int
    notes: tuple[str, ...]


def scan_ooxml(data: bytes) -> ScanResult:
    media: list[EmbeddedMedia] = []
    notes: list[str] = []
    skipped = 0
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = z.infolist()
            if len(infos) > MAX_MEMBERS:
                return ScanResult((), 0, (f"too many members ({len(infos)}); not scanned",))
            total = 0
            for info in infos:
                if not info.filename.startswith(("word/media/", "xl/media/", "ppt/media/")):
                    continue
                if info.is_dir():
                    continue
                if info.file_size > MAX_MEMBER_BYTES or total + info.file_size > MAX_TOTAL_BYTES:
                    skipped += 1
                    notes.append(f"{info.filename}: over size limit, skipped")
                    continue
                total += info.file_size
                blob = z.read(info)
                kind, mime = sniff_bytes(blob)
                if kind in ("image", "svg") and mime:
                    media.append(EmbeddedMedia(info.filename, mime, blob))
    except (zipfile.BadZipFile, OSError, RuntimeError, ValueError) as e:
        notes.append(f"zip error: {type(e).__name__}")
    return ScanResult(tuple(media), skipped, tuple(notes))


def _filters(obj) -> list[str]:
    f = obj.get("/Filter")
    if f is None:
        return []
    if isinstance(f, IndirectObject):
        f = f.get_object()
    if isinstance(f, list):
        return [str(x.get_object() if isinstance(x, IndirectObject) else x) for x in f]
    return [str(f)]


def _walk(resources, page_no, depth, seen, media, counters):
    if resources is None:
        return
    resources = resources.get_object()
    xobjects = resources.get("/XObject")
    if xobjects is None:
        return
    xobjects = xobjects.get_object()
    for name in list(xobjects.keys()):
        ref = xobjects.raw_get(name)
        obj = ref.get_object()
        subtype = obj.get("/Subtype")
        if isinstance(ref, IndirectObject):
            if ref.idnum in seen:
                continue
            seen.add(ref.idnum)
            tag = f"obj{ref.idnum}"
        else:
            tag = f"direct{counters['direct']}"
            counters["direct"] += 1
        if subtype == "/Image":
            if _filters(obj) == ["/DCTDecode"]:
                media.append(
                    EmbeddedMedia(
                        f"pdf:page{page_no}:{str(name).lstrip('/')}:{tag}",
                        "image/jpeg",
                        obj.get_data(),
                    )
                )
            else:
                counters["skipped"] += 1
        elif subtype == "/Form" and depth < MAX_FORM_DEPTH:
            _walk(obj.get("/Resources"), page_no, depth + 1, seen, media, counters)


def scan_pdf(data: bytes) -> ScanResult:
    media: list[EmbeddedMedia] = []
    counters = {"skipped": 0, "direct": 0}
    notes: list[str] = []
    try:
        reader = PdfReader(io.BytesIO(data))
        seen: set[int] = set()
        for n, page in enumerate(reader.pages, start=1):
            counters["direct"] = 0
            _walk(page.get("/Resources"), n, 0, seen, media, counters)
    except (PyPdfError, ValueError, KeyError, AttributeError, RecursionError) as e:
        notes.append(f"pdf error: {type(e).__name__}")
    if counters["skipped"]:
        notes.append(REENCODED_NOTE)
    return ScanResult(tuple(media), counters["skipped"], tuple(notes))

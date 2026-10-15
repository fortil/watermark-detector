"""Pull plain text out of text, DOCX and PDF files."""
from __future__ import annotations

import io
import re
import zipfile
import xml.etree.ElementTree as ET

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from watermark_detector.model import Kind

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
WORD_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MAX_DOCUMENT_XML_BYTES = 64 * 2**20


def extract_text(data: bytes, kind: Kind, mime: str | None) -> str | None:
    if kind == "text":
        return data.decode("utf-8", errors="replace").removeprefix("﻿")
    if kind == "ooxml" and mime == WORD_MIME:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                info = z.getinfo("word/document.xml")
                if info.file_size > MAX_DOCUMENT_XML_BYTES:
                    return None
                root = ET.fromstring(z.read(info))
        except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError):
            return None
        paras = ["".join(t.text or "" for t in p.iter(f"{W_NS}t")) for p in root.iter(f"{W_NS}p")]
        return "\n".join(paras)
    if kind == "pdf":
        try:
            return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
        except (PyPdfError, ValueError, KeyError):
            return None
    return None


def word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))

import io
import zipfile

from watermark_detector.sniff import OOXML_MIMES, sniff_bytes


def _zip(names):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n in names:
            z.writestr(n, "x")
    return buf.getvalue()


def test_png():
    assert sniff_bytes(b"\x89PNG\r\n\x1a\n" + bytes(8)) == ("image", "image/png")


def test_jpeg():
    assert sniff_bytes(b"\xff\xd8\xff\xe0" + bytes(8)) == ("image", "image/jpeg")


def test_gif():
    assert sniff_bytes(b"GIF89a" + bytes(8)) == ("image", "image/gif")
    assert sniff_bytes(b"GIF87a" + bytes(8)) == ("image", "image/gif")


def test_webp():
    assert sniff_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == ("image", "image/webp")


def test_tiff():
    assert sniff_bytes(b"II*\x00" + bytes(8)) == ("image", "image/tiff")
    assert sniff_bytes(b"MM\x00*" + bytes(8)) == ("image", "image/tiff")


def test_avif_heic():
    assert sniff_bytes(b"\x00\x00\x00\x20ftypavif" + bytes(24)) == ("image", "image/avif")
    assert sniff_bytes(b"\x00\x00\x00\x20ftypheic" + bytes(24)) == ("image", "image/heic")
    assert sniff_bytes(b"\x00\x00\x00\x20ftypmif1" + bytes(24)) == ("image", "image/heic")


def test_video():
    assert sniff_bytes(b"\x00\x00\x00\x20ftypisom" + bytes(24)) == ("video", "video/mp4")
    assert sniff_bytes(b"\x00\x00\x00\x20ftypqt  " + bytes(24)) == ("video", "video/quicktime")
    assert sniff_bytes(b"\x00\x00\x00\x20ftypM4A " + bytes(24)) == ("unknown", None)


def test_pdf():
    assert sniff_bytes(b"%PDF-1.7\n") == ("pdf", "application/pdf")


def test_ooxml():
    kind, mime = sniff_bytes(_zip(["[Content_Types].xml", "word/document.xml"]))
    assert (kind, mime) == ("ooxml", OOXML_MIMES["word/"])
    kind, mime = sniff_bytes(_zip(["[Content_Types].xml", "xl/workbook.xml"]))
    assert mime == OOXML_MIMES["xl/"]
    kind, mime = sniff_bytes(_zip(["[Content_Types].xml", "ppt/presentation.xml"]))
    assert mime == OOXML_MIMES["ppt/"]


def test_zip_without_content_types():
    assert sniff_bytes(_zip(["a.txt"])) == ("unknown", None)


def test_svg():
    assert sniff_bytes(b"<svg xmlns='x'></svg>") == ("svg", "image/svg+xml")
    assert sniff_bytes(b"\xef\xbb\xbf  <svg></svg>") == ("svg", "image/svg+xml")
    xml = b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg"/>'
    assert sniff_bytes(xml) == ("svg", "image/svg+xml")


def test_text():
    assert sniff_bytes("hello wörld".encode()) == ("text", "text/plain")


def test_unknown_binary():
    assert sniff_bytes(b"\x00\x01\x02\x03\xff\xfe") == ("unknown", None)
    assert sniff_bytes(b"abc\xff\xfe") == ("unknown", None)

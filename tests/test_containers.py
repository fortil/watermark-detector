from pypdf import PdfReader

from watermark_detector import containers
from watermark_detector.containers import scan_ooxml, scan_pdf


def test_docx_media(fx):
    r = scan_ooxml(fx["doc_claude_image.docx"].read_bytes())
    assert len(r.media) == 1
    assert r.media[0].location == "word/media/image1.png"
    assert r.media[0].data == fx["claude_like.png"].read_bytes()
    assert len(scan_ooxml(fx["doc_plain.docx"].read_bytes()).media) == 0


def test_pdf_media(fx):
    r = scan_pdf(fx["pdf_gpt_image.pdf"].read_bytes())
    assert [m.location for m in r.media] == ["pdf:page1:Im0:obj4"]
    assert r.media[0].data == fx["gpt_like.jpg"].read_bytes()
    assert len(scan_pdf(fx["pdf_plain.pdf"].read_bytes()).media) == 1


def test_pdf_flate_skipped(fx):
    r = scan_pdf(fx["pdf_flate_image.pdf"].read_bytes())
    assert len(r.media) == 0 and r.skipped == 1
    assert "image re-encoded in PDF; C2PA cannot survive" in r.notes


def test_member_limit(fx, monkeypatch):
    monkeypatch.setattr(containers, "MAX_MEMBER_BYTES", 100)
    r = scan_ooxml(fx["doc_claude_image.docx"].read_bytes())
    assert r.media == () and r.skipped == 1 and r.notes


def test_pdf_images_property_reencodes(fx):
    """VC5: page.images re-encodes, so it must not be used."""
    jpg = fx["gpt_like.jpg"].read_bytes()
    page = PdfReader(str(fx["pdf_gpt_image.pdf"])).pages[0]
    assert page.images[0].data != jpg


def _direct_xobject_pdf(fx, filter_name):
    pdf = fx["pdf_plain.pdf"].read_bytes()
    old = b"/XObject <</Im0 4 0 R>>"
    assert old in pdf
    new = b"/XObject <</Im0 <</Subtype /Image /Filter " + filter_name + b" /Width 1 /Height 1>>>>"
    return pdf.replace(old, new)


def test_direct_xobject_not_decoded_as_stream(fx):
    # A direct (non-indirect) image dictionary has no stream; the direct<k> branch must not raise.
    r = scan_pdf(_direct_xobject_pdf(fx, b"/FlateDecode"))
    assert r.media == () and r.skipped == 1
    r = scan_pdf(_direct_xobject_pdf(fx, b"/DCTDecode"))
    assert r.media == ()
    assert any(n.startswith("pdf error") for n in r.notes)

from watermark_detector.textio import extract_text, word_count
from watermark_detector.sniff import sniff_bytes


def _text(fx, name):
    data = fx[name].read_bytes()
    kind, mime = sniff_bytes(data)
    return extract_text(data, kind, mime)


def test_docx(fx):
    assert _text(fx, "doc_claude_image.docx") == "Hello watermark docx"


def test_pdf(fx):
    assert "Hello watermark pdf" in _text(fx, "pdf_gpt_image.pdf")


def test_text_word_count(fx):
    assert word_count(_text(fx, "text_long.txt")) == 450


def test_png_none(fx):
    assert _text(fx, "plain.png") is None

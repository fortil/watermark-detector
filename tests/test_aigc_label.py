import json
import shutil
import subprocess

import pytest

from watermark_detector.aigc_label import (
    aigc_label_findings,
    parse_label_json,
    producer_uscc,
    redact_code,
)

ZHIPU_USCC = "91110108MA01KP2T5U"


def find(fx, name, kind, mime):
    return aigc_label_findings(fx[name].read_bytes(), kind, mime, "file")


def test_parse_label_json():
    assert parse_label_json('{"Label":"1"}') == {"Label": "1"}
    assert parse_label_json('{"AIGC":{"Label":"1","ContentProducer":"x"}}')["ContentProducer"] == "x"
    assert parse_label_json("{") is None
    assert parse_label_json("[]") is None
    assert parse_label_json('{"foo":"bar"}') is None


def test_uscc_and_redact():
    assert producer_uscc("001191110108MA01KP2T5U00000") == ZHIPU_USCC
    assert producer_uscc(ZHIPU_USCC) == ZHIPU_USCC
    assert producer_uscc("002111010519491231002X00000") is None
    assert producer_uscc(None) is None
    assert redact_code("002111010519491231002X00000") == "0021<redacted>00000"
    assert redact_code("001191110108MA01KP2T5U00000") == "001191110108MA01KP2T5U00000"


@pytest.mark.parametrize("name", ["zai_like.jpg", "zai_like_be.jpg"])
def test_exif(fx, name):
    f = find(fx, name, "image", "image/jpeg")
    assert len(f) == 1
    x = f[0]
    assert (x.layer, x.verdict, x.provider, x.location) == ("aigc-label", "unsigned_hint", "zai", "file")
    assert x.evidence["container"] == "exif:UserComment"
    assert x.evidence["label"] == "1"
    assert x.evidence["producer_uscc"] == ZHIPU_USCC


def test_xmp_png(fx):
    f = find(fx, "zai_xmp_tc260.png", "image", "image/png")
    assert len(f) == 1
    assert f[0].evidence["container"] == "xmp:TC260:AIGC"
    assert f[0].provider == "zai"
    assert f[0].evidence["xmp_namespace"] == "http://www.tc260.org.cn/ns/AIGC/1.0/"


def test_text_chunk(fx):
    f = find(fx, "zai_text_chunk.png", "image", "image/png")
    assert len(f) == 1 and f[0].provider == "zai"
    assert f[0].evidence["container"] == "png:tEXt:AIGC"


def test_other_and_bad(fx):
    f = find(fx, "aigc_other.jpg", "image", "image/jpeg")
    assert f[0].provider is None and f[0].evidence["producer_uscc"] == "91350100M000100Y43"
    b = find(fx, "aigc_bad.jpg", "image", "image/jpeg")
    assert len(b) == 1 and b[0].verdict == "error"
    assert b[0].evidence["reason"] == "invalid AIGC JSON"


def test_negatives(fx):
    for name, mime in [
        ("plain.jpg", "image/jpeg"), ("plain.png", "image/png"), ("claude_like.png", "image/png"),
        ("xmp_google.jpg", "image/jpeg"), ("zai_like_reencoded.jpg", "image/jpeg"),
    ]:
        assert find(fx, name, "image", mime) == [], name


def test_truncated_tiff(fx):
    data = fx["zai_like.jpg"].read_bytes()
    i = data.index(b"Exif\x00\x00") + 6
    assert aigc_label_findings(data[: i + 10], "image", "image/jpeg", "file") == []


def test_mp4(fx):
    f = find(fx, "zai_like.mp4", "video", "video/mp4")
    assert len(f) == 1
    assert (f[0].verdict, f[0].provider) == ("unsigned_hint", "zai")
    assert f[0].evidence["container"] == "mp4:moov/udta/meta/keys:AIGC"
    assert find(fx, "plain.mp4", "video", "video/mp4") == []


@pytest.mark.skipif(shutil.which("exiftool") is None, reason="exiftool not installed")
def test_exiftool_crosscheck(fx):
    out = subprocess.run(
        ["exiftool", "-s", "-s", "-s", "-UserComment", str(fx["zai_like.jpg"])],
        capture_output=True, text=True,
    ).stdout.strip()
    f = find(fx, "zai_like.jpg", "image", "image/jpeg")
    from watermark_detector.aigc_label import extract_label_hits
    hit = extract_label_hits(fx["zai_like.jpg"].read_bytes(), "image", "image/jpeg")[0]
    assert out == hit.raw
    out2 = subprocess.run(
        ["exiftool", "-s", "-s", "-s", "-XMP-TC260:AIGC", str(fx["zai_xmp_tc260.png"])],
        capture_output=True, text=True,
    ).stdout.strip()
    hit2 = extract_label_hits(fx["zai_xmp_tc260.png"].read_bytes(), "image", "image/png")[0]
    assert json.loads(out2) == json.loads(hit2.raw)


def test_ooxml_label(fx):
    f = find(fx, "doc_zai_label.docx", "ooxml", None)
    assert len(f) == 1
    assert (f[0].verdict, f[0].provider, f[0].location) == ("unsigned_hint", "zai", "file")
    assert f[0].evidence["container"] == "ooxml:docProps/custom.xml:AIGC"


def test_pdf_label(fx):
    f = find(fx, "pdf_zai_label.pdf", "pdf", "application/pdf")
    assert len(f) == 1
    assert (f[0].verdict, f[0].provider) == ("unsigned_hint", "zai")
    assert f[0].evidence["container"] == "pdf:info:/AIGC"


def test_doc_negatives(fx):
    assert find(fx, "doc_plain.docx", "ooxml", None) == []
    assert find(fx, "pdf_plain.pdf", "pdf", "application/pdf") == []
    assert aigc_label_findings(b"PK\x03\x04garbage", "ooxml", None, "file") == []


def test_ooxml_size_limit(fx, monkeypatch):
    from watermark_detector import aigc_label

    monkeypatch.setattr(aigc_label, "MAX_CUSTOM_XML_BYTES", 10)
    assert find(fx, "doc_zai_label.docx", "ooxml", None) == []


@pytest.mark.skipif(shutil.which("exiftool") is None, reason="exiftool not installed")
def test_pdf_exiftool_crosscheck(fx):
    out = subprocess.run(
        ["exiftool", "-s", "-s", "-s", "-PDF:AIGC", str(fx["pdf_zai_label.pdf"])],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    from watermark_detector.aigc_label import extract_label_hits

    hits = extract_label_hits(fx["pdf_zai_label.pdf"].read_bytes(), "pdf", "application/pdf")
    assert out == hits[0].raw

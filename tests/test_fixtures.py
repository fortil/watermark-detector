import io
import json
import zipfile

import c2pa
import pypdf
from PIL import Image

from fixtures.build import IPTC_DST


def _actions(path):
    r = c2pa.Reader.try_create(str(path))
    with r:
        m = json.loads(r.crjson())["manifests"]
        assert len(m) == 1
        return m[0]["assertions"]["c2pa.actions.v2"]["actions"]


def test_all_exist(fx):
    assert len(fx) == 35
    for name, p in fx.items():
        assert p.exists() and p.stat().st_size > 0, name


def test_claude_png(fx):
    r = c2pa.Reader.try_create(str(fx["claude_like.png"]))
    with r:
        assert r.get_validation_state() == "Valid"
    assert c2pa.Reader.try_create(str(fx["reencoded.png"])) is None
    assert fx["claude_like.png"].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    names = [a["action"] for a in _actions(fx["claude_like.png"])]
    assert names == ["c2pa.opened", "com.anthropic.claude.provided"]


def test_gpt_actions(fx):
    acts = _actions(fx["gpt_like.jpg"])
    assert len(acts) == 1
    assert acts[0]["action"] == "c2pa.created"
    assert acts[0]["digitalSourceType"] == IPTC_DST + "trainedAlgorithmicMedia"
    assert acts[0]["softwareAgent"] == {"name": "GPT-4o"}


def test_pdf_text(fx):
    reader = pypdf.PdfReader(str(fx["pdf_gpt_image.pdf"]))
    assert "Hello watermark pdf" in reader.pages[0].extract_text()


def test_docx_media(fx):
    with zipfile.ZipFile(fx["doc_claude_image.docx"]) as z:
        assert z.read("word/media/image1.png") == fx["claude_like.png"].read_bytes()


def test_zai_fixtures(fx):
    assert fx["zai_like.mp4"].read_bytes()[4:12] == b"ftypisom"
    assert b"AIGC" not in fx["zai_like_reencoded.jpg"].read_bytes()
    for n in ("zai_like.jpg", "zai_like_be.jpg"):
        assert Image.open(fx[n]).size == (32, 32)
    with zipfile.ZipFile(fx["doc_zai_label.docx"]) as z:
        assert "docProps/custom.xml" in z.namelist()

"""Deterministic fixture builder: signed, tagged and plain sample files."""
from __future__ import annotations

import html
import io
import json
import struct
import zipfile
import zlib
from pathlib import Path
from typing import Any

import c2pa
from PIL import Image

from fixtures.pki import TestPki, make_chain

IPTC_DST = "http://cv.iptc.org/newscodes/digitalsourcetype/"
CLAUDE_ACTION = {
    "action": "com.anthropic.claude.provided",
    "parameters": {"origin-confidence": "unknown"},
}
ZHIPU_CODE = "001191110108MA01KP2T5U00000"
OTHER_CODE = "001191350100M000100Y4300000"

PNG_SIG = b"\x89PNG\r\n\x1a\n"


# ---- C2PA signing -------------------------------------------------------

def manifest_dict(generators: list[dict[str, str]], actions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "claim_generator_info": generators,
        "assertions": [{"label": "c2pa.actions", "data": {"actions": actions}}],
    }


def created_action(term: str, software_agent: str | None = None) -> dict[str, Any]:
    a: dict[str, Any] = {"action": "c2pa.created", "digitalSourceType": IPTC_DST + term}
    if software_agent is not None:
        a["softwareAgent"] = {"name": software_agent}
    return a


def sign_asset(
    src: bytes,
    mime: str,
    manifest: dict,
    pki: TestPki,
    *,
    edit_intent: bool = False,
    remote_url: str | None = None,
) -> bytes:
    builder = c2pa.Builder(manifest)
    if edit_intent:
        builder.set_intent(c2pa.C2paBuilderIntent.EDIT)
    if remote_url:
        builder.set_no_embed()
        builder.set_remote_url(remote_url)
    info = c2pa.C2paSignerInfo(
        alg=b"es256", sign_cert=pki.chain_pem, private_key=pki.key_pem, ta_url=None
    )
    signer = c2pa.Signer.from_info(info)
    src_stream = io.BytesIO(src)
    dst_stream = io.BytesIO()
    builder.sign(signer, mime, src_stream, dst_stream)  # return value is manifest bytes
    return dst_stream.getvalue()


# ---- XMP ------------------------------------------------------------------

def xmp_packet(dst_term: str, credit: str | None) -> str:
    credit_xml = f"<photoshop:Credit>{credit}</photoshop:Credit>" if credit else ""
    return (
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about="" '
        'xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" '
        'xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/">'
        f"<Iptc4xmpExt:DigitalSourceType>{IPTC_DST}{dst_term}</Iptc4xmpExt:DigitalSourceType>"
        f"{credit_xml}"
        "</rdf:Description></rdf:RDF></x:xmpmeta>"
    )


def insert_after_soi(jpeg: bytes, segment: bytes) -> bytes:
    assert jpeg[:2] == b"\xff\xd8"
    return jpeg[:2] + segment + jpeg[2:]


def inject_xmp_jpeg(jpeg: bytes, packet: str) -> bytes:
    payload = b"http://ns.adobe.com/xap/1.0/\x00" + packet.encode()
    seg = b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
    return insert_after_soi(jpeg, seg)


def png_chunk(type_: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(type_ + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + type_ + data + struct.pack(">I", crc)


def insert_png_chunk(png: bytes, chunk: bytes) -> bytes:
    assert png[:8] == PNG_SIG
    ihdr_len = struct.unpack(">I", png[8:12])[0]
    pos = 8 + 12 + ihdr_len
    return png[:pos] + chunk + png[pos:]


def inject_xmp_png(png: bytes, packet: str, *, compressed: bool) -> bytes:
    text = packet.encode()
    if compressed:
        text = zlib.compress(text)
    data = b"XML:com.adobe.xmp\x00" + (b"\x01" if compressed else b"\x00") + b"\x00" + b"\x00" + b"\x00" + text
    return insert_png_chunk(png, png_chunk(b"iTXt", data))


# ---- AIGC label (GB 45438) --------------------------------------------------

def aigc_json(producer: str, produce_id: str, *, wrapped: bool, reserved: str = "e494") -> str:
    obj = {
        "Label": "1",
        "ContentProducer": producer,
        "ProduceID": produce_id,
        "ReservedCode1": reserved,
        "ContentPropagator": producer,
        "PropagateID": produce_id,
        "ReservedCode2": reserved,
    }
    if wrapped:
        obj = {"AIGC": obj}
    return json.dumps(obj, separators=(",", ":"))


def exif_usercomment_app1(comment: str, *, little_endian: bool = True) -> bytes:
    e = "<" if little_endian else ">"
    payload = b"ASCII\x00\x00\x00" + comment.encode()
    tiff = (b"II*\x00" if little_endian else b"MM\x00*") + struct.pack(e + "I", 8)
    tiff += struct.pack(e + "H", 1) + struct.pack(e + "HHII", 0x8769, 4, 1, 26) + struct.pack(e + "I", 0)
    assert len(tiff) == 26
    tiff += struct.pack(e + "H", 1) + struct.pack(e + "HHII", 0x9286, 7, len(payload), 44) + struct.pack(e + "I", 0)
    assert len(tiff) == 44
    tiff += payload
    body = b"Exif\x00\x00" + tiff
    return b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body


def xmp_tc260_packet(label_json: str) -> str:
    return (
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about="" xmlns:TC260="http://www.tc260.org.cn/ns/AIGC/1.0/" '
        f'TC260:AIGC="{html.escape(label_json, quote=True)}"/>'
        "</rdf:RDF></x:xmpmeta>"
    )


# ---- MP4 ---------------------------------------------------------------------

def _box(type_: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", 8 + len(payload)) + type_ + payload


def build_mp4_with_keys(items: list[tuple[str, str]], *, fullbox_meta: bool = True) -> bytes:
    ftyp = _box(b"ftyp", b"isom" + struct.pack(">I", 512) + b"isomiso2avc1mp41")
    hdlr = _box(b"hdlr", bytes(4) + bytes(4) + b"mdta" + bytes(12) + b"\x00")
    keys_payload = bytes(4) + struct.pack(">I", len(items))
    for k, _ in items:
        name = k.encode()
        keys_payload += struct.pack(">I", 8 + len(name)) + b"mdta" + name
    keys = _box(b"keys", keys_payload)
    ilst_payload = b""
    for i, (_, v) in enumerate(items):
        data = _box(b"data", struct.pack(">II", 1, 0) + v.encode())
        ilst_payload += _box(struct.pack(">I", i + 1), data)
    ilst = _box(b"ilst", ilst_payload)
    meta = _box(b"meta", (bytes(4) if fullbox_meta else b"") + hdlr + keys + ilst)
    moov = _box(b"moov", _box(b"udta", meta))
    return ftyp + moov


# ---- documents ---------------------------------------------------------------

def build_docx(
    text: str,
    media: dict[str, bytes],
    *,
    custom_props: dict[str, str] | None = None,
) -> bytes:
    ct = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="png" ContentType="image/png"/>'
        '<Default Extension="jpg" ContentType="image/jpeg"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    )
    if custom_props is not None:
        ct += (
            '<Override PartName="/docProps/custom.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/>'
        )
    ct += "</Types>"
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{html.escape(text)}</w:t></w:r></w:p></w:body></w:document>"
    )
    doc_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
    )
    core = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator>fixture</dc:creator></cp:coreProperties>'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        z.writestr("docProps/core.xml", core)
        if custom_props is not None:
            props = ""
            for i, (name, value) in enumerate(custom_props.items()):
                props += (
                    f'<property fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="{2 + i}" '
                    f'name="{html.escape(name, quote=True)}"><vt:lpwstr>{html.escape(value, quote=True)}</vt:lpwstr></property>'
                )
            z.writestr(
                "docProps/custom.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" '
                'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
                f"{props}</Properties>",
            )
        for name, data in media.items():
            z.writestr(f"word/media/{name}", data)
    return buf.getvalue()


def _pdf_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def minimal_pdf(
    image: bytes,
    *,
    width: int,
    height: int,
    filter_name: str,
    text: str,
    info: dict[str, str],
) -> bytes:
    content = (
        f"BT /F1 12 Tf 10 80 Td ({_pdf_escape(text)}) Tj ET q {width} 0 0 {height} 0 0 cm /Im0 Do Q"
    ).encode()
    info_body = "".join(f"/{k} ({_pdf_escape(v)}) " for k, v in info.items())
    objs: list[bytes] = [
        b"<</Type /Catalog /Pages 2 0 R>>",
        b"<</Type /Pages /Kids [3 0 R] /Count 1>>",
        b"<</Type /Page /Parent 2 0 R /MediaBox [0 0 200 100] /Contents 5 0 R "
        b"/Resources <</XObject <</Im0 4 0 R>> /Font <</F1 6 0 R>>>>>>",
        (
            f"<</Type /XObject /Subtype /Image /Width {width} /Height {height} "
            f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter {filter_name} "
            f"/Length {len(image)}>>\nstream\n"
        ).encode() + image + b"\nendstream",
        f"<</Length {len(content)}>>\nstream\n".encode() + content + b"\nendstream",
        b"<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>",
        f"<<{info_body}>>".encode(),
    ]
    out = bytearray(b"%PDF-1.7\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objs) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<</Size {len(objs) + 1} /Root 1 0 R /Info 7 0 R>>\nstartxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    return bytes(out)


# ---- images -------------------------------------------------------------------

def _plain_image(fmt: str, **kw) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (10, 20, 30)).save(buf, fmt, **kw)
    return buf.getvalue()


def _resave(data: bytes, fmt: str, **kw) -> bytes:
    buf = io.BytesIO()
    Image.open(io.BytesIO(data)).save(buf, fmt, **kw)
    return buf.getvalue()


SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">'
    '<rect width="16" height="16" fill="#123456"/></svg>'
)


def build_all(out: Path) -> tuple[dict[str, Path], dict[str, TestPki]]:
    out.mkdir(parents=True, exist_ok=True)
    files: dict[str, bytes] = {}

    pkis = {
        "claude": make_chain("Anthropic, PBC", "Anthropic Claude Content Signing"),
        "gpt": make_chain("OpenAI OpCo, LLC", "OpenAI Media Service"),
        "gemini": make_chain("Google LLC", "Google Media Processing Services"),
        "google_camera": make_chain("Google LLC", "Pixel Camera"),
        "forger": make_chain("Example Forger Ltd", "Forger"),
        "other_ai": make_chain("Example AI Co", "Example Generator"),
    }

    plain_png = _plain_image("PNG")
    plain_jpg = _plain_image("JPEG", quality=90)
    files["plain.png"] = plain_png
    files["plain.jpg"] = plain_jpg

    claude_manifest = manifest_dict([{"name": "Anthropic Files", "version": "1.0.0"}], [CLAUDE_ACTION])
    claude_png = sign_asset(plain_png, "image/png", claude_manifest, pkis["claude"], edit_intent=True)
    files["claude_like.png"] = claude_png
    files["claude_like.svg"] = sign_asset(
        SVG.encode(), "image/svg+xml", claude_manifest, pkis["claude"], edit_intent=True
    )
    gpt_jpg = sign_asset(
        plain_jpg, "image/jpeg",
        manifest_dict([{"name": "ChatGPT"}], [created_action("trainedAlgorithmicMedia", "GPT-4o")]),
        pkis["gpt"],
    )
    files["gpt_like.jpg"] = gpt_jpg
    files["gemini_like.png"] = sign_asset(
        plain_png, "image/png",
        manifest_dict([{"name": "Google C2PA Core Generator Library"}],
                      [created_action("trainedAlgorithmicMedia")]),
        pkis["gemini"],
    )
    files["google_camera.jpg"] = sign_asset(
        plain_jpg, "image/jpeg",
        manifest_dict([{"name": "Pixel Camera"}], [created_action("digitalCapture")]),
        pkis["google_camera"],
    )
    files["spoof_name_only.png"] = sign_asset(
        plain_png, "image/png", claude_manifest, pkis["forger"], edit_intent=True
    )
    other_manifest = manifest_dict(
        [{"name": "Example Generator"}], [created_action("trainedAlgorithmicMedia")]
    )
    files["ai_other.png"] = sign_asset(plain_png, "image/png", other_manifest, pkis["other_ai"])

    tampered = bytearray(claude_png)
    idx = claude_png.index(b"IDAT") + 20
    tampered[idx] ^= 0xFF
    files["tampered.png"] = bytes(tampered)
    files["reencoded.png"] = _resave(claude_png, "PNG")
    files["remote_only.jpg"] = sign_asset(
        plain_jpg, "image/jpeg", other_manifest, pkis["other_ai"],
        remote_url="https://example.invalid/manifest.c2pa",
    )

    google_xmp = xmp_packet("trainedAlgorithmicMedia", "Made with Google AI")
    files["xmp_google.jpg"] = inject_xmp_jpeg(plain_jpg, google_xmp)
    files["xmp_google.png"] = inject_xmp_png(plain_png, google_xmp, compressed=False)
    files["xmp_google_z.png"] = inject_xmp_png(plain_png, google_xmp, compressed=True)
    files["xmp_dst_only.jpg"] = inject_xmp_jpeg(plain_jpg, xmp_packet("trainedAlgorithmicMedia", None))
    files["xmp_capture.jpg"] = inject_xmp_jpeg(plain_jpg, xmp_packet("digitalCapture", None))

    files["doc_claude_image.docx"] = build_docx("Hello watermark docx", {"image1.png": claude_png})
    files["doc_plain.docx"] = build_docx("Plain docx", {})
    files["pdf_gpt_image.pdf"] = minimal_pdf(
        gpt_jpg, width=32, height=32, filter_name="/DCTDecode",
        text="Hello watermark pdf", info={"Producer": "fixture"},
    )
    files["pdf_plain.pdf"] = minimal_pdf(
        plain_jpg, width=32, height=32, filter_name="/DCTDecode",
        text="Plain pdf", info={"Producer": "fixture"},
    )
    files["pdf_flate_image.pdf"] = minimal_pdf(
        zlib.compress(bytes(32 * 32 * 3)), width=32, height=32, filter_name="/FlateDecode",
        text="Flate pdf", info={"Producer": "fixture"},
    )
    files["text_long.txt"] = " ".join(f"token{i}" for i in range(450)).encode()

    # Z.AI catalogue
    zai_comment = aigc_json(ZHIPU_CODE, "20260914202522fixture0000000001", wrapped=True)
    zai_jpg = insert_after_soi(plain_jpg, exif_usercomment_app1(zai_comment))
    files["zai_like.jpg"] = zai_jpg
    files["zai_like_be.jpg"] = insert_after_soi(
        plain_jpg, exif_usercomment_app1(zai_comment, little_endian=False)
    )
    files["zai_like_reencoded.jpg"] = _resave(zai_jpg, "JPEG", quality=90)
    files["zai_xmp_tc260.png"] = inject_xmp_png(
        plain_png, xmp_tc260_packet(aigc_json(ZHIPU_CODE, "fixture-xmp", wrapped=False)), compressed=False
    )
    files["zai_text_chunk.png"] = insert_png_chunk(
        plain_png,
        png_chunk(b"tEXt", b"AIGC\x00" + aigc_json(ZHIPU_CODE, "fixture-text", wrapped=True).encode()),
    )
    files["aigc_other.jpg"] = insert_after_soi(
        plain_jpg,
        exif_usercomment_app1(aigc_json(OTHER_CODE, "20260914202522fixture0000000001", wrapped=True)),
    )
    files["aigc_bad.jpg"] = insert_after_soi(
        plain_jpg, exif_usercomment_app1('{"AIGC":{"Label":"1",')
    )
    files["zai_like.mp4"] = build_mp4_with_keys(
        [
            ("major_brand", "isom"),
            ("minor_version", "512"),
            ("compatible_brands", "isomiso2avc1mp41"),
            ("AIGC", aigc_json(ZHIPU_CODE, "fixture-mp4", wrapped=False)),
            ("encoder", "Lavf58.76.100"),
        ]
    )
    files["plain.mp4"] = build_mp4_with_keys([("encoder", "Lavf58.76.100")])
    files["doc_zai_label.docx"] = build_docx(
        "Hello zai docx", {},
        custom_props={"AIGC": aigc_json(ZHIPU_CODE, "fixture-docx", wrapped=False)},
    )
    files["pdf_zai_label.pdf"] = minimal_pdf(
        plain_jpg, width=32, height=32, filter_name="/DCTDecode", text="Zai pdf",
        info={"Producer": "fixture", "AIGC": aigc_json(ZHIPU_CODE, "fixture-pdf", wrapped=False)},
    )
    files["pdf_zai_image.pdf"] = minimal_pdf(
        zai_jpg, width=32, height=32, filter_name="/DCTDecode", text="Zai image pdf",
        info={"Producer": "fixture"},
    )

    paths: dict[str, Path] = {}
    for name, data in files.items():
        p = out / name
        p.write_bytes(data)
        paths[name] = p
    return paths, pkis

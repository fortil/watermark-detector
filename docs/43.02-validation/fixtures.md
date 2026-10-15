---
tema: Fixture catalogue
tipo: nota
proyecto: watermark-detector
creada: 2026-10-15
actualizada: 2026-10-15
estado: activa
aliases: [Fixtures]
tags: [watermark-detector, fixtures]
---

# Fixtures

Built at test time by `tests/fixtures/build.py` with a throwaway PKI per provider identity. All rasters are 32x32 RGB (10, 20, 30). Third-party files come from c2pa-python v0.38.0 (MIT OR Apache-2.0).

## C2PA and XMP

| Name | Built from | Expected |
|---|---|---|
| plain.png / plain.jpg | Pillow | c2pa absent |
| claude_like.png / .svg | PKI "Anthropic, PBC", edit intent, action `com.anthropic.claude.provided` | claude/claimed; confirmed with the root pinned |
| gpt_like.jpg | PKI "OpenAI OpCo, LLC", `c2pa.created` trainedAlgorithmicMedia | gpt/claimed |
| gemini_like.png | PKI "Google LLC" / "Google Media Processing Services" | gemini/claimed |
| google_camera.jpg | PKI "Google LLC" / "Pixel Camera", digitalCapture | none/present_other |
| spoof_name_only.png | Forger PKI, Claude-like manifest | none/present_other, claim_mismatch claude |
| ai_other.png | PKI "Example AI Co" | none/ai_unknown_provider |
| tampered.png | claude_like.png with one IDAT byte flipped | claude/invalid |
| reencoded.png | Pillow re-save of claude_like.png | absent |
| remote_only.jpg | remote manifest URL, not embedded | remote_reference |
| xmp_google.jpg / .png / _z.png | XMP DigitalSourceType plus Credit (APP1, iTXt, compressed iTXt) | xmp gemini/unsigned_hint |
| xmp_dst_only.jpg | XMP DigitalSourceType only | xmp none/unsigned_hint |
| xmp_capture.jpg | XMP digitalCapture | no xmp finding |
| third_party/C.jpg | vendored | none/present_other, Valid, untrusted |
| third_party/A.jpg | vendored | absent |

## Documents and text

| Name | Expected |
|---|---|
| doc_claude_image.docx | claude/claimed at `word/media/image1.png`; text "Hello watermark docx" |
| doc_plain.docx | no provider signal |
| pdf_gpt_image.pdf | gpt/claimed at `pdf:page1:Im0:obj4`; top level absent |
| pdf_plain.pdf | embedded media without a manifest |
| pdf_flate_image.pdf | 0 media, skipped 1 |
| text_long.txt | text, word_count 450 |

## Z.AI and GB 45438

| Name | Expected |
|---|---|
| zai_like.jpg / zai_like_be.jpg | aigc-label zai/unsigned_hint (EXIF UserComment, little and big endian) |
| zai_like_reencoded.jpg | no aigc-label finding |
| zai_xmp_tc260.png | aigc-label zai/unsigned_hint (`xmp:TC260:AIGC`) |
| zai_text_chunk.png | aigc-label zai/unsigned_hint (`png:tEXt:AIGC`) |
| aigc_other.jpg | aigc-label none/unsigned_hint, `producer_uscc` 91350100M000100Y43 |
| aigc_bad.jpg | aigc-label none/error, "invalid AIGC JSON" |
| zai_like.mp4 | kind video; aigc-label zai/unsigned_hint |
| plain.mp4 | kind video; no finding; absence note |
| doc_zai_label.docx | zai/unsigned_hint at file (`ooxml:docProps/custom.xml:AIGC`) |
| pdf_zai_label.pdf | zai/unsigned_hint at file (`pdf:info:/AIGC`) |
| pdf_zai_image.pdf | zai/unsigned_hint at `pdf:page1:Im0:obj4` |

Back to [Validation](index.md).

---
tema: Real-samples protocol
tipo: nota
proyecto: watermark-detector
creada: 2026-10-15
actualizada: 2026-10-15
estado: activa
aliases: [Real samples]
tags: [watermark-detector, validation, protocol]
---

# Real-samples protocol

Samples are outputs from your own accounts, saved in `tests/fixtures/real/samples/` (gitignored). Check the providers' current terms before sharing any sample. The expectations are as of 2026-10-10. Write down what you actually get; a mismatch is information, not a bug by default.

Run with `make validate-real` after copying `tests/fixtures/real/expected.example.json` to `expected.json`. The manifest format is in `tests/fixtures/real/README.md`.

| # | Sample | How to produce it | Expected | Negative |
|---|---|---|---|---|
| 1 | Claude PNG | claude.ai file creation, download a PNG | c2pa claude/claimed; confirmed after pinning the intermediate from this same file | screenshot: no provider signal |
| 2 | Claude SVG | ask for an SVG logo file, download | claude/claimed | editor re-export: absent |
| 3 | Claude API | code execution, Files API download | claude/claimed | none |
| 4 | Claude DOCX | ask for a .docx report | no C2PA provider signal expected (unverified) | none |
| 5 | Claude text | 400+ words of prose | not_run without access; score with API access | public-domain text |
| 6 | GPT image (ChatGPT) | generate and download a PNG | gpt/confirmed or claimed (unverified until run) | screenshot |
| 7 | GPT image (API) | decode the b64 output | same as 6 | none |
| 8 | GPT text | API project with text watermarking on, 400+ tokens | not_run without researcher access | public-domain text |
| 9 | Gemini image | Gemini app download | gemini/confirmed expected; maybe xmp unsigned_hint; check SynthID by hand | screenshot |
| 10 | Gemini text | 400+ words | coverage only | none |
| 11 | Camera photo | your own phone photo | absent or present_other, never gemini | none |
| 12 | Z.AI image (China API) | open.bigmodel.cn images/generations, `glm-image` | aigc-label zai/unsigned_hint at file; badge likely | screenshot |
| 13 | Z.AI image (international) | api.z.ai, `glm-image` | aigc-label zai/unsigned_hint at file; no badge | screenshot |
| 14 | Z.AI video | open.bigmodel.cn videos/generations, `cogvideox-3`, download result | kind video; aigc-label zai/unsigned_hint at file | one-frame screenshot |
| 15 | Z.AI text | chat.z.ai or chat API, 400+ words | coverage only | none |

Back to [Validation](index.md).

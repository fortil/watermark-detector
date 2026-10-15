---
tema: Z.AI signals and GB 45438
tipo: nota
proyecto: watermark-detector
creada: 2026-10-15
actualizada: 2026-10-15
estado: activa
aliases: [Z.AI, GB 45438]
tags: [watermark-detector, zai, gb-45438]
---

# Z.AI (Zhipu / BigModel)

Answer: yes for images and video, no documented mark for text.

## Research rows

| Modality | Signal | Local? | Facts |
|---|---|---|---|
| Text (GLM-4.7 to GLM-5.3, GLM-4.xV) | None documented | no | No text request has a watermark parameter in either API reference; the only chat-completions `watermark_enabled` is in the GLM-4-Voice audio schema [P, E35, E37]. GB 45438 lets the explicit text label sit in the chat interface [P, E39]. A citizen submission to the EC says GLM served via a Singapore platform "performs no marking" [S, E48]. A hidden statistical mark cannot be ruled out (unverified). |
| Image (glm-image, cogview-4, cogview-3-flash) | GB 45438 label in EXIF `UserComment`, ContentProducer `001191110108MA01KP2T5U00000` | yes, `unsigned_hint` | 69 of 69 real outputs carry it, from both APIs [L15]. Re-saving drops it [L18]. Consumer apps (chatglm.cn, chat.z.ai) were not sampled (unverified). |
| Image | Visible "AI生成" badge, bottom-right | manual | `watermark_enabled` defaults to true; false needs a signed disclaimer [P, E33]. Seen on BigModel 2026-04 and 2026-09 sets; absent on the 2025-11 set and on api.z.ai sets [L15]. v1 detects no visible marks. |
| Image | "Implicit digital watermark" (pixel) | no | Named in BigModel docs and user agreement [P, E33, E36]. No scheme, key or detector is published. |
| Video (cogvideox-3/-2/-flash) | GB 45438 label in MP4 `moov/udta/meta` keys `AIGC` | yes, `unsigned_hint` | One CogVideoX-3 output (2026-07-07) on aigc-files.bigmodel.cn carries it; its ProduceID equals the API task id [L16]. |
| Document | GB 45438 label in OOXML `docProps/custom.xml` or PDF Info `/AIGC` | partial | No Z.AI document sample was found (unverified). Embedded JPEGs keep their EXIF label. |
| Audio | Explicit and implicit marks per docs | out of scope | `watermark_enabled` on TTS and GLM-4-Voice [P, E35]. |
| Open weights run locally | None | no | The zai-org repos and diffusers pipelines contain no labeling code [P, E50]. |
| C2PA | None | n/a | No Zhipu entry among the conforming products [P, E24]. |

## GB 45438 and TC260 summary

- Standard GB 45438-2025 and China's labeling Measures (Art. 5: implicit label in file metadata is mandatory), in force 2025-09-01 [P, E39, E40].
- Fields (Annex E): `Label` (1 AI-generated, 2 possibly, 3 suspected), `ContentProducer`, `ProduceID`, `ReservedCode1`, `ContentPropagator`, `PropagateID`, `ReservedCode2`. The JSON sits under a field whose name or keyword contains `AIGC`, plain or wrapped as `{"AIGC": {...}}`.
- Containers read in v1: JPEG EXIF UserComment; an XMP property `<prefix>:AIGC` (namespace `http://www.tc260.org.cn/ns/AIGC/1.0/` in the TC260 scheme) [E41]; PNG `tEXt`/`zTXt`/`iTXt` with an AIGC keyword; MP4/MOV `moov/udta/meta` keys [E42]; OOXML `docProps/custom.xml` and PDF Info key [E43].
- Code format, 27 characters [P, E44]: 1-2 version `00`; 3 subject type (1 organisation, 2 individual); 4 binding (1 = USCC for organisations); 5-22 subject code; 23-27 service extension (`00000` for Zhipu).
- Individual-type codes embed an ID, phone, passport or net number, so the tool redacts characters 5-22 for them.

## Observed samples

| Endpoint | Model | Dates | Files | Badge |
|---|---|---|---|---|
| open.bigmodel.cn | cogview-3-flash | 2025-11 | 29 | no |
| open.bigmodel.cn | cogview-4 | 2026-04 | 18 | yes |
| open.bigmodel.cn | cogview-3-flash | 2026-09 | 12 | yes |
| api.z.ai | cogView-4-250304 | 2026-01 | 4 | no |
| api.z.ai | cogview-3-flash / cogview-4 | 2026-09 to 2026-10 | 6 | no |
| aigc-files.bigmodel.cn | cogvideox-3 (MP4) | 2026-07-07 | 1 | no |

Source repos are listed under E49 in [Sources](sources.md); the files are third-party outputs and are not vendored.

## Attribution rule

The provider comes only from the USCC inside ContentProducer: characters 5-22 of the 27-character code, or a bare 18-character USCC. `91110108MA01KP2T5U` is the unified social credit code of 北京智谱华章科技有限公司 [S, E46; the official registry was not fetched]. ContentPropagator, ProduceID and the reserved codes never attribute.

## Limits

- The label is unsigned. Anyone can write or strip it, and a Pillow re-save drops it. It is only ever an `unsigned_hint`.
- Zhipu's ReservedCode1/2 are 4 to 8 hex characters with no published way to verify them [E45].
- Text is unmarked as far as any document says.
- Visible badges and pixel watermarks are not checked.

Back to [Research](index.md).

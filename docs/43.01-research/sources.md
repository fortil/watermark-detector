---
tema: Sources
tipo: nota
proyecto: watermark-detector
creada: 2026-10-15
actualizada: 2026-10-15
estado: activa
aliases: [Sources]
tags: [watermark-detector, sources]
---

# Sources

Accessed 2026-10-10 unless an entry says otherwise. [P] primary source, [S] secondary. E# ids are web sources and L# ids are local observations; the research notes cite them by id.

## Web sources

- **E1 [P]** https://www.anthropic.com/news/claude-text-watermark (2026-08-14, updated 2026-09-01). SynthID-Text version, key, code/factual/short/translation behaviour, light edit vs full rewrite, C2PA on .png/.jpg/.svg, private-preview API and form.
- **E2 [P]** https://support.claude.com/en/articles/16266773-how-claude-marks-ai-generated-content (2026-08-11). Start date 2026-08-02, model and product lists, Bedrock 10-17, Content Checker, API eligibility, limits.
- **E3 [P]** https://claude.com/check-content. Free, runs in the browser, accepted formats, text not supported.
- **E4 [S]** TechCrunch, 2026-08-11 and 2026-08-15:
  - https://techcrunch.com/2026/08/11/anthropic-says-it-will-watermark-text-generated-by-its-ai-models/
  - https://techcrunch.com/2026/08/15/anthropic-shares-more-details-about-how-claudes-new-watermarks-will-work/
- **E5 [S]** https://magazine.sebastianraschka.com/p/claude-watermarking (2026-08-22). Tournament-sampling interpretation; key required.
- **E6 [S]** https://news.ycombinator.com/item?id=49303350. Thread on E1; verified through the HN API.
- **E7 [S]** https://c2paviewer.com/articles/claude-api-c2pa-example. Claude manifest fields; validation "Valid" plus signingCredential.untrusted; manifest attached at download.
- **E8 [S]** https://github.com/DICOMPUTE/Open/issues/1414 (2026-10-07). An independent observation of "Anthropic Files" 1.0.0, com.anthropic.claude.provided and "Anthropic Content Credentials Root CA".
- **E9 [P]** https://cdn.openai.com/pdf/e9508624-d767-41b6-a26d-e34ca798ada6/textgrain-entropy-calibrated-watermarking-for-language-model-text.pdf (2026-10-05). The algorithm; detection needs the text, the key and the generation config.
- **E10 [P, not fetchable]** https://openai.com/index/eu-text-provenance/. Returns HTTP 403 to automated clients; its content comes from E11.
- **E11 [S]** Rollout, API opt-in settings, detection rates, researcher access, "no hidden characters":
  - https://www.actuia.com/en/news/openai-will-watermark-chatgpt-in-the-eu-but-leaves-the-api-opt-in/
  - https://www.therundown.ai/news/openai-textgrain-eu-chatgpt-codex-watermarks
  - https://slashdot.org/story/26/10/06/0443237/openai-is-adding-text-watermarking-in-chatgpt-and-codex
- **E12 [P, 403]** https://help.openai.com/en/articles/8912793-provenance-signals-in-openai-generated-content (content unverified).
- **E13 [S]** https://sightengine.com/python-c2pa-tutorial-verifying-images-detecting-tampering (2025-06-11). ChatGPT manifest: issuer "OpenAI", generator "ChatGPT", softwareAgent "GPT-4o", DST trainedAlgorithmicMedia.
- **E14 [P forum]** https://community.openai.com/t/c2pa-not-working-on-chatgpt-images/1379093 (OpenAI support, 2026-04-17).
- **E15 [P]** https://blog.google/innovation-and-ai/products/identifying-ai-generated-media-online/ (2026-05-19). OpenAI is among the SynthID adopters; AI Content Detection API; C2PA verification in the Gemini app. Also https://www.resultsense.com/news/2026-05-20-openai-c2pa-synthid-content-provenance/ [S]. The OpenAI side, https://openai.com/index/advancing-content-provenance/, was not fetched (403).
- **E16 [P]** https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/ai-content-detection. Private preview, JPEG/PNG/WebP, ML classifier, no C2PA.
- **E17 [P]** https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/nano-banana-2-1. "Content Credentials (C2PA): Supported".
- **E18 [P]** https://support.google.com/gemini/answer/16722517. Gemini app verification of image/video/audio. Quota, verbatim (re-fetched 2026-10-10): "approximately 10 image checks, 10 video checks (up to 5 minutes total), and 10 audio checks (up to 3 hours total) within any 24-hour rolling window".
- **E19 [P forum staff]** https://discuss.ai.google.dev/t/does-gemini-api-text-output-carry-synthid-watermarking-gemini-2-5-flash-lite-gemini-3-1-flash-lite-eu-ai-act-art-50-2/177241. Staff correction on 2026-08-19: API text IS watermarked.
- **E20 [P]** SynthID-Text sources:
  - https://deepmind.google/blog/watermarking-ai-generated-text-and-video-with-synthid/ (2024-05-14)
  - https://www.nature.com/articles/s41586-024-08025-4
  - https://github.com/google-deepmind/synthid-text (keys; Bayesian detector trained per key)
- **E21 [P]** https://ai.google.dev/responsible/docs/safeguards/synthid. Keep the config private; HF Transformers classes; limitations.
- **E22 [S]** Public SynthID Detector: formats, text excluded, ToS forbids automation. Neither source gives a quota number: ppc.land says "Daily limits apply" and "The documents do not state what the daily quota is", and ventureatlas states no limit (both re-fetched 2026-10-10):
  - https://ppc.land/googles-synthid-detector-gains-public-access-and-covers-4-companies/
  - https://www.ventureatlas.org/news/2026-10-07-google-synthid-detector-public
- **E23 [P]** https://iptc.org/?p=7667 (2024-10-28). Gemini images carry DigitalSourceType trainedAlgorithmicMedia and Credit "Made with Google AI".
- **E24 [P]** https://github.com/c2pa-org/conformance-public (CC-BY-4.0), files `trust-list/C2PA-TRUST-LIST.pem` and `conforming-products/conforming-products-list.json`, fetched 2026-10-10. Facts used: 30 anchors (Google present, no Anthropic/OpenAI names); OpenAI Media Service conformant on 2026-01-28; Google Media Processing Services entries; 0 Anthropic entries.
- **E25 [P]** https://contentcredentials.org/trust/anchors.pem. Legacy ITL, 27 anchors (Truepic, Adobe, Microsoft, …).
- **E26 [P]** https://github.com/contentauth/c2pa-python (v0.38.0, docs/context-settings.md). `trust_anchors` replaces, `user_anchors` adds, `remote_manifest_fetch` is true by default.
- **E27 [S, academic]** https://arxiv.org/abs/2609.09604 (2026-09-09). "No public tool can test the deployed systems".
- **E28 [S]** https://letsdatascience.com/news/google-makes-gemini-media-watermarks-optional-6153add7. The Gemini visible sparkle is optional since 2026-08-14.
- **E29 [S]** https://www.euronews.com/2026/08/11/eu-compliance-delivered-globally-anthropic-to-watermark-claudes-output-worldwide
- **E30 [S, snippet only]** https://aiphotocheck.com/blog/google-c2pa-core-generator-library. Nano Banana manifests: issuer Google LLC, claim generator "Google C2PA Core Generator Library", DST trainedAlgorithmicMedia. The page was not fetched, so treat this as (unverified).
- **E31 [P]** https://blog.google/innovation-and-ai/models-and-research/google-deepmind/synth-id-ai-content/ ("Google expands SynthID Detector for AI content", 2026-10-07). Access for everyone, "available globally in English starting today", to check "an image, video, or audio file". It gives no quota number.
- **E32 [S]** Reports of a synthid.com quota of about 10 checks a day across image, video and audio, attributed to Google without a primary link. Treated as (unverified):
  - https://letsdatascience.com/news/google-opens-synthid-detector-to-global-public-access-effe39eb (2026-10-08, citing Ars Technica, which was not fetchable)
  - https://borncity.com/news/google-synthid-detector-weltweiter-zugang-aber-nur-10-pruefungen-taeglich/ (2026-10-08)

## Z.AI and China sources
- **E33 [P]** BigModel API reference, image generation: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%9B%BE%E5%83%8F%E7%94%9F%E6%88%90.md (and its twin "图像生成异步").
  - `POST /paas/v4/images/generations`; models `glm-image`, `cogview-4-250304`, `cogview-4`, `cogview-3-flash`; image links are valid for 30 days.
  - `watermark_enabled`, verbatim: "`true`: 默认启用AI生成的显式水印及隐式数字水印，符合政策要求。`false`: 关闭所有水印，仅允许已签署免责声明的客户使用，签署路径：个人中心-安全管理-去水印管理".
- **E34 [P]** BigModel API reference, async video generation: https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E8%A7%86%E9%A2%91%E7%94%9F%E6%88%90%E5%BC%82%E6%AD%A5.md. Models `cogvideox-3`, `cogvideox-2`, `cogvideox-flash`, `viduq1-text`, `viduq1-image`, `vidu2-image`, `viduq1-start-end`, `vidu2-start-end`, `vidu2-reference`. Same `watermark_enabled` text.
- **E35 [P]** BigModel API reference, chat completions (`…/对话补全.md`) and text-to-speech (`…/文本转语音.md`):
  - In chat completions, `watermark_enabled` appears only in the GLM-4-Voice audio request schema; text-model requests have none.
  - TTS: "控制AI生成音频时是否添加水印 … 默认启用AI生成的显式水印及隐式数字水印".
- **E36 [P]** BigModel user agreement §四.7 "人工智能生成合成内容标识": https://docs.bigmodel.cn/cn/terms/user-agreement.
  - Content is labeled per the Interim Measures, the Labeling Measures and GB 45438—2025, "包括但不限于显式标识、隐式标识".
  - Users must not tamper with "显式标识、隐式标识（包括元数据标识和数字水印）".
  - Removing labels needs a written application, and the user then takes over the labeling duty.
- **E37 [P]** Z.AI international docs:
  - https://docs.z.ai/api-reference/image/generate-image.md: only `glm-image`; parameters `model`, `prompt`, `quality`, `size`, `user_id`; no watermark parameter.
  - https://docs.z.ai/api-reference/video/generate-video.md: `cogvideox-3`; no watermark parameter.
  - https://docs.z.ai/llms-full.txt: no "watermark" string.
  - https://docs.z.ai/release-notes/new-released: GLM-4.7 2025-12-22, GLM-Image 2026-01-14, GLM-5 2026-02-12, GLM-5.1 2026-04-07, GLM-5.2 2026-06-16, GLM-5.3 2026-08-18, GLM-5.3-Flash 2026-08-26.
- **E38 [P]** https://docs.z.ai/legal-agreement/terms-of-use: the user "shall adopt technical measures to add identifiers … AI-generated Outputs shall be prominently marked at reasonable locations". This is a duty on the user, not a statement about Z.AI's own marking.
- **E39 [P]** 《人工智能生成合成内容标识办法》 (CAC, MIIT, MPS and NRTA; signed 2025-03-07, published 2025-03-14, in force 2025-09-01): https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm.
  - Art. 4: explicit labels. For text, at the start, end or middle, "或者在交互场景界面、文字周边添加显著的提示标识". Downloaded files must keep explicit labels.
  - Art. 5: the implicit label in file metadata is mandatory, and digital watermarks are encouraged.
  - Art. 9: label-free content on request, with logs kept at least 6 months.
  - Art. 10: no malicious removal.
- **E40 [P]** GB 45438—2025 《网络安全技术 人工智能生成合成内容标识方法》 (SAMR/SAC; published 2025-02-28, in force 2025-09-01). The text was read from a law-firm-hosted copy of the official PDF: https://www.sidley.com/en/-/media/resource-pages/ai-monitor/20250314-china-standard-gb-454382025-labeling-method-for-content-generated-by-ai.pdf (sha256 `4a5224ca…2c49`).
  - §6.1: five label elements. §6.2: content implicit labels "准许采用数字水印".
  - Annex E: the field name or keyword contains "AIGC", and the value is `{"AIGC": {"Label":…,"ContentProducer":…,"ProduceID":…,"ReservedCode1":…,"ContentPropagator":…,"PropagateID":…,"ReservedCode2":…}}`. Label 1/2/3 = is / possibly / suspected AI-generated.
  - Annex F.4: an example ReservedCode1 holding a hash-based signature.
- **E41 [P]** TC260-PG-20259A, image files (2025-08): https://www.tc260.org.cn/tc260/sjzn/202508/7227bfecdf344c14abc647fbbcf69edf/files/37774d2b3149456ba7179a81bc07d3d5.pdf (sha256 `e4f7fe82…a02f`).
  - §6: XMP namespace `TC260` = `http://www.tc260.org.cn/ns/AIGC/1.0/`, property `AIGC` holding flat JSON.
  - Locations: JPEG APP1 XMP; PNG iTXt XMP; TIFF IFD0 tag 0x2BC; GIF Application Extension; WebP XMP; HEIF per ISO/IEC 23008-12.
  - Annex B: EXIF `UserComment`, and a PNG `tEXt` chunk "AIGC", both with the wrapped `{"AIGC":{…}}` form.
- **E42 [P]** TC260-PG-20257A, video files: https://www.tc260.org.cn/tc260/sjzn/202508/e1d2ed74976341cfafdc709243070d58/files/8d7cd66e0f5b464cb778143d7500d0a5.pdf (sha256 `f24b835c…beb1`).
  - §6.1.1 MP4/MOV: `moov.udta.meta`, key `AIGC` in `keys`, flat JSON in `ilst`; written with ffmpeg `-metadata AIGC=… -movflags use_metadata_tags`.
  - §6.1.2–6.1.4: FLV, MKV, AVI. §6.2: XMP fallback.
- **E43 [P]** TC260-PG-20258A, text files: https://www.tc260.org.cn/tc260/sjzn/202508/f0a84ada0c11458e9cb6da56c1cb2426/files/760387fb30e94c058c31b8c2b2230020.pdf (sha256 `6bf6c118…3b0e`).
  - OOXML: a `docProps/custom.xml` property `name="AIGC"` with JSON in `vt:lpwstr`.
  - PDF: the Document Information Dictionary entry `/AIGC (…)`.
  - Also UOF, OFD, Markdown, xmind and posm/posf.
- **E44 [P]** TC260-PG-20252A, service-provider coding rules (2025-03): https://www.tc260.org.cn/tc260/sjzn/202503/44ac104a3559429eb9260d0826212be7/files/3534b47327704191bea0eceb0f3e0f7f.pdf (sha256 `7741a161…47a1`). The code has 27 characters:
  - 1–2: format version `00`;
  - 3: subject type (1 organisation, 2 individual);
  - 4: binding (1 = USCC for organisations; 1–4 = ID card, phone, passport or net number for individuals);
  - 5–22: subject code;
  - 23–27: service extension, `00000` when unused, else 23 = 1 generation / 2 propagation.
  - The example USCC `91350100M000100Y43` "不指向特定主体".
- **E45 [P]** TC260-PG-202511A, label security protection: https://www.tc260.org.cn/tc260/sjzn/202508/63ab55a3265f45c7865e9b8be15d4a29/files/dc379ec776f94abc8f1806affa1cda35.pdf (sha256 `861126b3…466b`). A signature in ReservedCode1/2 needs a key pair whose public key is published and bound to the signer by a certificate.
- **E46 [S]** Company registry record from a BigModel competition dataset: https://raw.githubusercontent.com/Samge0/BigModelCompetitionDataV2/0ed21d0258ace105b9aa4723805875eed29a01ca/datas/智谱ai平台的公司主体-北京智谱华章科技有限公司.md.
  - 统一社会信用代码 91110108MA01KP2T5U = 北京智谱华章科技有限公司, est. 2019-06-11, Haidian, Beijing.
  - Corroborated by the detector table in https://github.com/martianzhang/aigc-cli/blob/main/internal/service/detect_result.go (`"1191110108MA01KP2T5U": "智谱AI (Zhipu) — 清言 / GLM"`).
  - The official registry (gsxt.gov.cn) was not fetched.
- **E47 [S]** https://help.aliyun.com/en/document_detail/2672918.html: Alibaba Cloud's description of the 27-character code and the Label values, matching E44.
- **E48 [S]** EC "Have your say" citizen feedback, Ref. Ares(2026)7932405, 2026-08-16: https://ec.europa.eu/info/law/better-regulation/api/download/090166e5321114c0. Quote: "GLM by Zhipu served via a Singapore-based platform, which performs no marking". This is one user's statement.
- **E49 [S]** Where the real samples come from: public GitHub repos at pinned commits. The files are third-party outputs and are not vendored.
  - https://github.com/CloudAI-X/z-ai-playground-v2 @56799677: `generate_samples.py` posts to `https://api.z.ai/api/paas/v4/images/generations` with `cogView-4-250304` and saves the bytes unchanged. Images dated 2026-01-02.
  - https://github.com/HerlockShelomes/LLMGal @4cae08bd: `open.bigmodel.cn`, `cogview-3-flash`, 2026-09-14.
  - https://github.com/eyesmoons/inkForge-studio @02c102b5: `open.bigmodel.cn`, `cogview-4`, 2026-04.
  - https://github.com/maxazure/ai-website-builder-nz: `open.bigmodel.cn`, `cogview-3-flash`, 2025-11.
  - https://github.com/spiritmalteam-star/interplanetary: `api.z.ai`, `cogview-3-flash`/`cogview-4`, 2026-09/10.
  - https://github.com/thisisniagahub/Dowgnut-Z @bed3472a: `public/videos/commercial-result.json` records cogvideox-3 task `2026070704263981822d714f6c48b6`, whose `video_result[0].url` is the L16 file.
- **E50 [P]** Open-weight repos https://github.com/zai-org/GLM-Image, https://github.com/zai-org/CogView4 and https://github.com/zai-org/CogVideo: their READMEs mention no watermark or label. A GitHub code search of huggingface/diffusers `src/diffusers/pipelines/cogview4` and `…/cogvideo` for "watermark" returns 0 hits (2026-10-10).

## Local observations

Made on 2026-10-10 with c2pa-python 0.38.0 (c2pa-rs 0.91.0), pypdf 6.20.0, Pillow, exiftool 13.55 and ffmpeg 7.1.1.

- **L2.** A self-made chain with O "Anthropic, PBC" gives "Valid" plus `signingCredential.untrusted`. Pinning the root or intermediate gives "Trusted" ("found in [user_anchors]"). Putting the intermediate in `trust_anchors` gives "Trusted" ("[system_anchors]").
- **L15.** A scan of committed media in 524 GitHub repos that reference Zhipu image or video models found 69 unique files with Zhipu's code, from 5 repos (E49), with ProduceIDs from 2025-11-01 to 2026-10-02.
  - All are JPEG bytes (some saved as `.png`), all use EXIF UserComment, and all have Label "1".
  - ReservedCode1 and ReservedCode2 are always 4 hex characters.
  - The key order is Label, ContentProducer, ProduceID, ContentPropagator, PropagateID, ReservedCode1, ReservedCode2.
  - The "AI生成" badge (bottom-right) is present in the BigModel 2026-04 (18 files) and 2026-09 (12) sets. It is absent in the BigModel 2025-11 set (29) and the api.z.ai 2026-01 (4) and 2026-09/10 (6) sets.
  - Reference file: `style_after.jpg` (BigModel, sha256 `974d7de3…acff`), which shows the badge.
- **L16.** `https://aigc-files.bigmodel.cn/api/cogvideo/fe9e2828-7978-11f1-b8dd-0e390b9f69e7_0.mp4` (live on 2026-10-10; sha256 `db8d7651…bddc`; 1920×1080, 5.19 s, encoder Lavf58.76.100):
  - `moov/udta/meta` is a FullBox (version/flags 0). It holds `hdlr` (`mdta`), `keys` [major_brand, minor_version, compatible_brands, AIGC, encoder] and `ilst`.
  - `ilst` item 4 holds a type-1 `data` box with the flat JSON `{"Label": "1", "ContentProducer": "001191110108MA01KP2T5U00000", "ProduceID": "2026070704263981822d714f6c48b6", "ReservedCode1": "8f39dc2d", …}`.
  - The ProduceID equals the API task id in E49.
  - No badge in the corners of the first and last frames.
  - The task's cover JPEG on `aigc-files.bigmodel.cn` (sha256 `cf44a882…6fcd`) has no label.
  - `c2pa.Reader.try_create` → None.
- **L18.** The synthetic fixture builders in `tests/fixtures/build.py` (EXIF `II` and `MM`, PNG `tEXt` "AIGC", PNG iTXt XMP `TC260:AIGC`, MP4 keys/ilst, DOCX custom.xml, PDF Info `/AIGC`) parse back to the same JSON.
  - Independent tools read them too: `exiftool -UserComment`, `-XMP-TC260:AIGC`, `-Keys:AIGC`, `-PDF:AIGC` and the docx custom property, and `ffprobe … format_tags=AIGC`.
  - A Pillow `Image.open(x).save(jpeg)` drops the EXIF label.

Back to [Research](index.md).

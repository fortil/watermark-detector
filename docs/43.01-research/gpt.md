---
tema: GPT signals
tipo: nota
proyecto: watermark-detector
creada: 2026-10-15
actualizada: 2026-10-15
estado: activa
aliases: [GPT]
tags: [watermark-detector, gpt]
---

# GPT

| Modality | Signal | Local? | Facts |
|---|---|---|---|
| Text | textGrain, keyed OT/Gumbel block watermark [P, E9] | no | The detector needs the text, the secret key and the tokenizer/config. EU ChatGPT/Codex rollout from 2026-10-05. API opt-in per org/project ("Text provenance", "Allow text watermarking"), off by default, no request parameter [S, E11]. About 95% detection at 400 tokens and 80% at 200 tokens (1% FPR); 10% word substitution gives 66%, 25% gives 17% [S, E11]. Detector access only for approved researchers. |
| Image | C2PA signed by "OpenAI" (2025 sample) or "OpenAI OpCo, LLC" / CN "OpenAI Media Service" | yes | 2025 ChatGPT sample: generator "ChatGPT", softwareAgent "GPT-4o", trainedAlgorithmicMedia [S, E13]. Conformant since 2026-01-28 for jpeg/png/gif/webp, mp4, audio and pdf [P, E24]. Some ChatGPT images had no credential in April 2026 [P forum, E14]. |
| Image | SynthID pixel watermark since 2026-05-19 | manual | OpenAI Verify and synthid.com [S, E15, E22]. |
| Document | C2PA in a PDF, if present | partial | The conformance entry lists `application/pdf`; which product emits it is (unverified) [E24]. |

Back to [Research](index.md).

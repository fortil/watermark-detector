---
tema: Gemini signals
tipo: nota
proyecto: watermark-detector
creada: 2026-10-15
actualizada: 2026-10-15
estado: activa
aliases: [Gemini]
tags: [watermark-detector, gemini]
---

# Gemini

| Modality | Signal | Local? | Facts |
|---|---|---|---|
| Text | SynthID-Text | no | App/web since 2024-05-14 [P, E20]. API, AI Studio and Antigravity per Google staff on 2026-08-19 [P forum, E19]. Vertex (unverified). No public detector: the portal excludes text [S, E22] and the keys are private [P, E20, E21]. |
| Image | C2PA signed by "Google LLC" / CN "Google Media Processing Services" | yes, confirmable | Nano Banana 2.1 lists Content Credentials as supported [P, E17]. Google anchors are on the C2PA Trust List [P, E24]. Claim generator "Google C2PA Core Generator Library" is from a search snippet only (unverified, E30). |
| Image | SynthID pixel watermark | manual | synthid.com opened to everyone on 2026-10-07 [P, E31]. Google documents no daily number; about 10 checks per day is secondary (unverified, E32). The Gemini app allows about 10 image checks per rolling 24 h [P, E18]. Programmatic use is against the terms [S, E22]. The Cloud AI Content Detection API is a private-preview ML classifier that does not read C2PA [P, E16]. |
| Image | IPTC XMP `DigitalSourceType=trainedAlgorithmicMedia`, `Credit="Made with Google AI"` [P, E23] | yes, `unsigned_hint` | Anyone can add or remove it. |
| Document | C2PA in a PDF, if present | partial | One Google conformant generator lists `application/pdf`; which product emits it is (unverified) [E24]. |

Back to [Research](index.md).

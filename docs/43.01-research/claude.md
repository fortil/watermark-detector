---
tema: Claude signals
tipo: nota
proyecto: watermark-detector
creada: 2026-10-15
actualizada: 2026-10-15
estado: activa
aliases: [Claude]
tags: [watermark-detector, claude]
---

# Claude

| Modality | Signal | Local? | Facts |
|---|---|---|---|
| Text | Keyed watermark, "a version of SynthID-Text" [P, E1] | no | Models launched on or after 2026-08-02, older ones being retrofitted. Covers claude.ai, API, Claude Code, Bedrock (completes 2026-10-17), Vertex, Foundry [P, E2]. Detection API is in private preview (form https://forms.gle/9tGA33hPJJwtHsMk9); the request/response spec is not public [P, E1, E2]. Weak on short, factual or code text and on heavy edits. "Tournament sampling" is Raschka's reading [S, E5]. |
| Image (.png .jpg .svg) | C2PA Content Credential [P, E1] | yes, `claimed` | Observed manifest: generator "Anthropic Files" 1.0.0, actions `c2pa.opened` then `com.anthropic.claude.provided`, no digitalSourceType. Signer O "Anthropic, PBC", CN "Anthropic Claude Content Signing", root "Anthropic Content Credentials Root CA". Result "Valid" plus `signingCredential.untrusted` [S, E7, E8]. Manual check: https://claude.com/check-content [P, E3]. |
| Document (docx/pdf) | None announced [E1] | partial | The manifest is attached at download through the Files API [S, E7]. Images inside Claude-made documents are probably unsigned (unverified). |

Anthropic is not on the official C2PA Trust List and has no conformant product [P, E24], so a Claude file is `claimed` unless the user pins an anchor. See [C2PA trust](c2pa-trust.md).

Back to [Research](index.md).

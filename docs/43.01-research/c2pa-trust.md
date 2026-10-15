---
tema: C2PA trust model
tipo: nota
proyecto: watermark-detector
creada: 2026-10-15
actualizada: 2026-10-15
estado: activa
aliases: [C2PA trust]
tags: [watermark-detector, c2pa]
---

# C2PA trust

## Valid vs Trusted

A C2PA signature proves the file was not changed after signing. It does not prove who signed, unless the certificate chain ends at an anchor you trust. c2pa-rs reports "Valid" plus `signingCredential.untrusted` for an intact signature with an unknown chain, and "Trusted" when the chain ends at an anchor [L2].

A locally made certificate with O="Anthropic, PBC" validates as "Valid", so the signer name alone never gives `confirmed`.

## Anchors

- Vendored: the official C2PA Trust List (30 anchors, LoTE seq 1, issued 2026-08-05) and the legacy Interim Trust List (27 anchors), passed as `trust.trust_anchors` [E24, E25, E26].
- Neither list names Anthropic or OpenAI. Google anchors are present.
- User pins go in `trust.user_anchors`.

## Pinning procedure

1. Generate a file yourself with the provider (so you know it is genuine).
2. `wmd certs that-file.png -o chain.pem` lists the chain and marks the active signer.
3. Pin the intermediate: `wmd detect --anchors chain.pem other-file.png`. Matching files then show `confirmed` with `trusted_via: user-anchor`.

## Spoof demonstration

`spoof_name_only.png` carries the Claude action and generator name but is signed by "Example Forger Ltd". The tool reports `present_other` with `claim_mismatch: claude`, not a Claude finding. Attribution uses only the signer certificate subject.

## Offline

`verify.remote_manifest_fetch=false` and `verify.ocsp_fetch=false`: the tool makes no network calls without `--remote`.

Back to [Research](index.md).

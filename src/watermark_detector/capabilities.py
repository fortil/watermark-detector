"""What can and cannot be checked per provider and modality (research as data)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

VERIFIED_ON = "2026-10-10"

_E1 = "https://www.anthropic.com/news/claude-text-watermark"
_E2 = "https://support.claude.com/en/articles/16266773-how-claude-marks-ai-generated-content"
_E3 = "https://claude.com/check-content"
_E7 = "https://c2paviewer.com/articles/claude-api-c2pa-example"
_E9 = "https://cdn.openai.com/pdf/e9508624-d767-41b6-a26d-e34ca798ada6/textgrain-entropy-calibrated-watermarking-for-language-model-text.pdf"
_E11 = "https://www.actuia.com/en/news/openai-will-watermark-chatgpt-in-the-eu-but-leaves-the-api-opt-in/"
_E13 = "https://sightengine.com/python-c2pa-tutorial-verifying-images-detecting-tampering"
_E15 = "https://blog.google/innovation-and-ai/products/identifying-ai-generated-media-online/"
_E16 = "https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/ai-content-detection"
_E17 = "https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/nano-banana-2-1"
_E18 = "https://support.google.com/gemini/answer/16722517"
_E19 = "https://discuss.ai.google.dev/t/does-gemini-api-text-output-carry-synthid-watermarking-gemini-2-5-flash-lite-gemini-3-1-flash-lite-eu-ai-act-art-50-2/177241"
_E20 = "https://deepmind.google/blog/watermarking-ai-generated-text-and-video-with-synthid/"
_E22 = "https://ppc.land/googles-synthid-detector-gains-public-access-and-covers-4-companies/"
_E23 = "https://iptc.org/?p=7667"
_E24 = "https://github.com/c2pa-org/conformance-public"
_E31 = "https://blog.google/innovation-and-ai/models-and-research/google-deepmind/synth-id-ai-content/"
_E33 = "https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%9B%BE%E5%83%8F%E7%94%9F%E6%88%90.md"
_E34 = "https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E8%A7%86%E9%A2%91%E7%94%9F%E6%88%90%E5%BC%82%E6%AD%A5.md"
_E35 = "https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8.md"
_E36 = "https://docs.bigmodel.cn/cn/terms/user-agreement"
_E37 = "https://docs.z.ai/api-reference/image/generate-image.md"
_E39 = "https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm"
_E41 = "https://www.tc260.org.cn/tc260/sjzn/202508/7227bfecdf344c14abc647fbbcf69edf/files/37774d2b3149456ba7179a81bc07d3d5.pdf"
_E42 = "https://www.tc260.org.cn/tc260/sjzn/202508/e1d2ed74976341cfafdc709243070d58/files/8d7cd66e0f5b464cb778143d7500d0a5.pdf"
_E43 = "https://www.tc260.org.cn/tc260/sjzn/202508/f0a84ada0c11458e9cb6da56c1cb2426/files/760387fb30e94c058c31b8c2b2230020.pdf"
_E44 = "https://www.tc260.org.cn/tc260/sjzn/202503/44ac104a3559429eb9260d0826212be7/files/3534b47327704191bea0eceb0f3e0f7f.pdf"

Modality = Literal["text", "image", "document", "video"]


@dataclass(frozen=True)
class Capability:
    provider: str
    modality: Modality
    signal: str
    local: Literal["yes", "no", "partial"]
    how_to_check: str
    notes: str
    sources: tuple[str, ...]


CAPABILITIES: tuple[Capability, ...] = (
    Capability(
        "claude", "text", "SynthID-Text-derived keyed watermark", "no",
        "Anthropic Watermark Detection API (private preview, eligible orgs, form https://forms.gle/9tGA33hPJJwtHsMk9); verifier 'claude' + --remote",
        "Models launched on or after 2026-08-02. Weak on short, factual or code text and on heavy edits. The request/response spec is not public.",
        (_E1, _E2),
    ),
    Capability(
        "claude", "image", "C2PA Content Credential (.png .jpg .svg)", "yes",
        "wmd detect (claimed unless the anchor is pinned); manual https://claude.com/check-content",
        "Signer O 'Anthropic, PBC'. The CA is not on the official C2PA Trust List, so a valid signature is 'claimed' until you pin the anchor.",
        (_E1, _E3, _E7),
    ),
    Capability(
        "claude", "document", "No document-level marking; embedded images + text only", "partial",
        "wmd detect; verifier 'claude'",
        "The manifest is attached at download through the Files API. Images inside Claude-made documents are probably unsigned (unverified).",
        (_E1, _E7),
    ),
    Capability(
        "gemini", "text", "SynthID-Text", "no",
        "No public detector (SynthID Detector excludes text; keys private)",
        "In the Gemini app/web since 2024-05; Gemini API per staff on 2026-08-19. Vertex AI unverified.",
        (_E19, _E20, _E22),
    ),
    Capability(
        "gemini", "image", "C2PA (Google LLC, Google Media Processing Services)", "yes",
        "wmd detect",
        "Google anchors are on the official C2PA Trust List, so a valid file can be 'confirmed'.",
        (_E17, _E24),
    ),
    Capability(
        "gemini", "image", "SynthID pixel watermark", "no",
        "Manual: https://synthid.com (daily limit; number not documented; automation prohibited) or the Gemini app (about 10 image checks per rolling 24 h)",
        "Google documents no number for the synthid.com quota. The Cloud AI Content Detection API is a private-preview ML classifier.",
        (_E16, _E18, _E22, _E31),
    ),
    Capability(
        "gemini", "image", "IPTC XMP DigitalSourceType + Credit 'Made with Google AI'", "yes",
        "wmd detect (unsigned hint)",
        "Unsigned metadata: anyone can add or remove it.",
        (_E23,),
    ),
    Capability(
        "gemini", "document", "C2PA in PDF if present; text not detectable", "partial",
        "wmd detect",
        "One Google conformant generator lists application/pdf; which product emits it is unverified.",
        (_E24,),
    ),
    Capability(
        "gpt", "text", "textGrain keyed watermark", "no",
        "OpenAI detector for approved researchers (application since 2026-10-05); verifier 'gpt' + --remote",
        "The detector needs the text, the secret key and the tokenizer/config. Rollout started 2026-10-05 in the EU.",
        (_E9, _E11),
    ),
    Capability(
        "gpt", "image", "C2PA (OpenAI / OpenAI OpCo, LLC, OpenAI Media Service)", "yes",
        "wmd detect",
        "Some ChatGPT images carried no credential (April 2026).",
        (_E13, _E24),
    ),
    Capability(
        "gpt", "image", "SynthID pixel watermark (since 2026-05-19)", "no",
        "Manual: https://openai.com/research/verify/ or https://synthid.com",
        "Secondary reports only for the OpenAI side.",
        (_E15, _E22),
    ),
    Capability(
        "gpt", "document", "C2PA in PDF if present; text via researcher detector", "partial",
        "wmd detect; verifier 'gpt'",
        "OpenAI Media Service conformance lists application/pdf; which product emits it is unverified.",
        (_E24, _E9),
    ),
    Capability(
        "zai", "text", "No documented text watermark", "no",
        "Nothing to check: Z.AI documents no text mark; GB 45438 text labels may sit in the chat interface",
        "No text-model request has a watermark parameter in either API reference. A hidden statistical mark cannot be ruled out (unverified).",
        (_E35, _E37, _E39),
    ),
    Capability(
        "zai", "image", "GB 45438 AIGC label (EXIF UserComment; also XMP or PNG text) with Zhipu's producer code", "yes",
        "wmd detect (unsigned hint)",
        "69 of 69 real outputs carried it (BigModel and api.z.ai, 2025-11 to 2026-10). The label is unsigned: re-saving drops it and anyone can write it.",
        (_E33, _E41, _E44),
    ),
    Capability(
        "zai", "image", "Visible 'AI生成' badge, bottom-right", "no",
        "Manual: look at the bottom-right corner (BigModel default; not seen on api.z.ai outputs)",
        "Seen on 30 BigModel files (2026-04, 2026-09); absent on 29 BigModel files (2025-11) and 10 api.z.ai files.",
        (_E33, _E36),
    ),
    Capability(
        "zai", "image", "Implicit digital (pixel) watermark named in BigModel docs", "no",
        "No public detector (Zhipu publishes no scheme or key)",
        "Named in the API docs and the user agreement; no scheme, key or detector is published.",
        (_E33, _E36),
    ),
    Capability(
        "zai", "document", "GB 45438 label in docx custom.xml or PDF Info if present; embedded images", "partial",
        "wmd detect",
        "No Z.AI document sample was found (unverified). Embedded Z.AI JPEGs keep their EXIF label. Unsigned.",
        (_E43,),
    ),
    Capability(
        "zai", "video", "GB 45438 AIGC label in MP4/MOV moov/udta/meta keys", "yes",
        "wmd detect (unsigned hint)",
        "Seen on a CogVideoX-3 output (2026-07-07). Video is checked only for this label; C2PA in video is not read. Unsigned.",
        (_E34, _E42),
    ),
)

_KIND_MODALITIES: dict[str, tuple[str, ...]] = {
    "image": ("image",),
    "svg": ("image",),
    "pdf": ("document", "image", "text"),
    "ooxml": ("document", "image", "text"),
    "text": ("text",),
    "video": ("video",),
}


def coverage_for(kind: str, configured: frozenset[str], remote: bool) -> list[dict[str, str]]:
    modalities = _KIND_MODALITIES.get(kind, ())
    out: list[dict[str, str]] = []
    for c in CAPABILITIES:
        if c.modality not in modalities:
            continue
        if c.local in ("yes", "partial"):
            status = "checked"
        elif c.modality == "text":
            if c.provider in configured and remote:
                status = "verifier_run"
            elif c.provider in configured:
                status = "verifier_configured_not_run"
            else:
                status = "not_checkable_locally"
        elif c.how_to_check.startswith("Manual:"):
            status = "manual_check_available"
        else:
            status = "not_checkable"
        out.append({"provider": c.provider, "signal": c.signal, "local": c.local, "status": status})
    return out

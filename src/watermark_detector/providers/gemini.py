"""Gemini / Google generative AI profile."""
from watermark_detector.providers import ProviderProfile

PROFILE = ProviderProfile(
    key="gemini",
    display="Gemini / Google generative AI",
    signer_orgs=frozenset({"Google LLC"}),
    signer_cn_prefixes=("Google Media Processing Services",),
    claim_generator_prefixes=("Google C2PA Core Generator Library",),
    action_labels=frozenset(),
    requires_ai_source_type=True,
    sources=(
        "https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/nano-banana-2-1",
        "https://github.com/c2pa-org/conformance-public",
    ),
)

"""Claude (Anthropic) profile."""
from watermark_detector.providers import ProviderProfile

PROFILE = ProviderProfile(
    key="claude",
    display="Claude (Anthropic)",
    signer_orgs=frozenset({"Anthropic, PBC"}),
    signer_cn_prefixes=(),
    claim_generator_prefixes=("Anthropic Files",),
    action_labels=frozenset({"com.anthropic.claude.provided"}),
    requires_ai_source_type=False,
    sources=(
        "https://www.anthropic.com/news/claude-text-watermark",
        "https://support.claude.com/en/articles/16266773-how-claude-marks-ai-generated-content",
        "https://c2paviewer.com/articles/claude-api-c2pa-example",
        "https://github.com/DICOMPUTE/Open/issues/1414",
    ),
)

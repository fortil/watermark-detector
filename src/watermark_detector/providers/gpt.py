"""GPT (OpenAI) profile."""
from watermark_detector.providers import ProviderProfile

PROFILE = ProviderProfile(
    key="gpt",
    display="GPT (OpenAI)",
    signer_orgs=frozenset({"OpenAI OpCo, LLC", "OpenAI"}),
    signer_cn_prefixes=(),
    claim_generator_prefixes=("ChatGPT", "OpenAI"),
    action_labels=frozenset(),
    requires_ai_source_type=False,
    sources=(
        "https://sightengine.com/python-c2pa-tutorial-verifying-images-detecting-tampering",
        "https://github.com/c2pa-org/conformance-public",
        "https://help.openai.com/en/articles/8912793-provenance-signals-in-openai-generated-content",
    ),
)

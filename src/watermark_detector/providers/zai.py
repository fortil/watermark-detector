"""Z.AI / Zhipu profile. Attributed only through the GB 45438 label, never C2PA."""
from watermark_detector.providers import ProviderProfile

PROFILE = ProviderProfile(
    key="zai",
    display="Z.AI / Zhipu (GLM, CogView, CogVideoX)",
    signer_orgs=frozenset(),
    signer_cn_prefixes=(),
    claim_generator_prefixes=(),
    action_labels=frozenset(),
    requires_ai_source_type=False,
    sources=(
        "https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%9B%BE%E5%83%8F%E7%94%9F%E6%88%90.md",
        "https://docs.z.ai/api-reference/image/generate-image.md",
        "https://docs.z.ai/api-reference/video/generate-video.md",
        "https://docs.z.ai/llms-full.txt",
        "https://www.sidley.com/en/-/media/resource-pages/ai-monitor/20250314-china-standard-gb-454382025-labeling-method-for-content-generated-by-ai.pdf",
        "https://www.tc260.org.cn/tc260/sjzn/202508/7227bfecdf344c14abc647fbbcf69edf/files/37774d2b3149456ba7179a81bc07d3d5.pdf",
        "https://www.tc260.org.cn/tc260/sjzn/202508/e1d2ed74976341cfafdc709243070d58/files/8d7cd66e0f5b464cb778143d7500d0a5.pdf",
        "https://www.tc260.org.cn/tc260/sjzn/202503/44ac104a3559429eb9260d0826212be7/files/3534b47327704191bea0eceb0f3e0f7f.pdf",
        "https://raw.githubusercontent.com/Samge0/BigModelCompetitionDataV2/0ed21d0258ace105b9aa4723805875eed29a01ca/datas/智谱ai平台的公司主体-北京智谱华章科技有限公司.md",
    ),
    aigc_producer_usccs=frozenset({"91110108MA01KP2T5U"}),
)

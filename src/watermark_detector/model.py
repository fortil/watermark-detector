"""Report data model shared by all modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Kind = Literal["image", "svg", "pdf", "ooxml", "text", "video", "unknown"]
Layer = Literal["c2pa", "xmp", "text-watermark", "container", "aigc-label"]
Verdict = Literal[
    "confirmed",
    "claimed",
    "via_ingredient",
    "invalid",
    "ai_unknown_provider",
    "present_other",
    "unsigned_hint",
    "remote_reference",
    "absent",
    "skipped",
    "score",
    "not_configured",
    "not_run",
    "error",
]

PROVIDERS = ("claude", "gemini", "gpt", "zai")

AI_SOURCE_TYPES = frozenset(
    {"trainedAlgorithmicMedia", "compositeWithTrainedAlgorithmicMedia"}
)

PROVIDER_SIGNAL_VERDICTS = frozenset(
    {"confirmed", "claimed", "via_ingredient", "invalid", "unsigned_hint"}
)


@dataclass(frozen=True)
class Finding:
    layer: Layer
    verdict: Verdict
    provider: str | None
    location: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    path: str
    kind: Kind
    mime: str | None
    findings: list[Finding]
    coverage: list[dict[str, str]]
    errors: list[str]

"""Provider profiles and C2PA attribution rules."""
from __future__ import annotations

from dataclasses import dataclass, field

from watermark_detector.c2pa_reader import C2paResult, ManifestInfo
from watermark_detector.model import AI_SOURCE_TYPES, Finding


@dataclass(frozen=True)
class ProviderProfile:
    key: str
    display: str
    signer_orgs: frozenset[str]
    signer_cn_prefixes: tuple[str, ...]
    claim_generator_prefixes: tuple[str, ...]
    action_labels: frozenset[str]
    requires_ai_source_type: bool
    sources: tuple[str, ...]
    aigc_producer_usccs: frozenset[str] = field(default_factory=frozenset)


from watermark_detector.providers import claude as _claude  # noqa: E402
from watermark_detector.providers import gemini as _gemini  # noqa: E402
from watermark_detector.providers import gpt as _gpt  # noqa: E402
from watermark_detector.providers import zai as _zai  # noqa: E402

PROFILES: dict[str, ProviderProfile] = {
    p.key: p for p in (_claude.PROFILE, _gemini.PROFILE, _gpt.PROFILE, _zai.PROFILE)
}

NOTE_CLAIMED = (
    "Signature intact, but the signing certificate does not chain to a trusted anchor; "
    "certificate names can be forged. Pin the provider anchor with --anchors to confirm."
)


def _has_ai_dst(m: ManifestInfo) -> bool:
    return any(a.get("digital_source_type") in AI_SOURCE_TYPES for a in m.actions)


def match_profile(m: ManifestInfo) -> ProviderProfile | None:
    org = m.signer_subject.get("O")
    cn = m.signer_subject.get("CN", "")
    for p in PROFILES.values():
        if org not in p.signer_orgs:
            continue
        if p.signer_cn_prefixes and not any(cn.startswith(x) for x in p.signer_cn_prefixes):
            continue
        if p.requires_ai_source_type and not _has_ai_dst(m):
            continue
        return p
    return None


def claimed_by_content(m: ManifestInfo) -> str | None:
    for p in PROFILES.values():
        if any(g.startswith(x) for g in m.claim_generators for x in p.claim_generator_prefixes):
            return p.key
        if any(a.get("action") in p.action_labels for a in m.actions):
            return p.key
    return None


def match_aigc_producer(uscc: str | None) -> str | None:
    if not uscc:
        return None
    for p in PROFILES.values():
        if uscc in p.aigc_producer_usccs:
            return p.key
    return None


def attribute(result: C2paResult, location: str) -> list[Finding]:
    if result.status == "absent":
        return [Finding("c2pa", "absent", None, location)]
    if result.status == "remote":
        return [Finding("c2pa", "remote_reference", None, location, {"remote_url": result.remote_url})]
    if result.status == "error":
        return [Finding("c2pa", "error", None, location, {"error": result.error})]

    findings: list[Finding] = []
    state = result.validation_state
    active = next((m for m in result.manifests if m.is_active), None)
    if active is None and result.manifests:
        active = result.manifests[0]
    if active is not None:
        p = match_profile(active)
        if p is not None:
            verdict = {"Trusted": "confirmed", "Invalid": "invalid"}.get(state or "", "claimed")
            evidence = {
                "signer_subject": active.signer_subject,
                "signer_issuer": active.signer_issuer,
                "validation_state": state,
                "failure_codes": list(active.failure_codes),
                "trusted_via": active.trusted_via,
                "claim_generators": list(active.claim_generators),
                "actions": [dict(a) for a in active.actions],
                "corroboration": {
                    "claim_generator": any(
                        g.startswith(x) for g in active.claim_generators for x in p.claim_generator_prefixes
                    ),
                    "action_label": any(a.get("action") in p.action_labels for a in active.actions),
                    "ai_source_type": _has_ai_dst(active),
                },
            }
            if verdict == "claimed":
                evidence["note"] = NOTE_CLAIMED
            findings.append(Finding("c2pa", verdict, p.key, location, evidence))
        else:
            if state == "Invalid":
                verdict = "invalid"
            elif _has_ai_dst(active):
                verdict = "ai_unknown_provider"
            else:
                verdict = "present_other"
            evidence = {
                "signer_subject": active.signer_subject,
                "signer_issuer": active.signer_issuer,
                "validation_state": state,
                "failure_codes": list(active.failure_codes),
                "claim_generators": list(active.claim_generators),
                "actions": [dict(a) for a in active.actions],
            }
            mismatch = claimed_by_content(active)
            if mismatch is not None:
                evidence["claim_mismatch"] = mismatch
            findings.append(Finding("c2pa", verdict, None, location, evidence))
    for m in result.manifests:
        if m is active or m.is_active:
            continue
        q = match_profile(m)
        if q is not None:
            findings.append(
                Finding(
                    "c2pa", "via_ingredient", q.key, location,
                    {"manifest_label": m.label, "trusted_via": m.trusted_via,
                     "signer_subject": m.signer_subject},
                )
            )
    return findings

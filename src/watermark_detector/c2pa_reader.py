"""Read C2PA manifests with an explicit trust context."""
from __future__ import annotations

import io
import json
from collections.abc import Sequence
from dataclasses import dataclass
from importlib import resources
from typing import Any, Literal

import c2pa


@dataclass(frozen=True)
class ManifestInfo:
    label: str
    is_active: bool
    signer_subject: dict[str, str]
    signer_issuer: dict[str, str]
    signer_serial: int | None
    claim_generators: tuple[str, ...]
    actions: tuple[dict[str, str | None], ...]
    success_codes: tuple[str, ...]
    failure_codes: tuple[str, ...]
    trusted_via: Literal["trust-list", "user-anchor"] | None


@dataclass(frozen=True)
class C2paResult:
    status: Literal["absent", "present", "remote", "error"]
    validation_state: str | None = None
    active_label: str | None = None
    manifests: tuple[ManifestInfo, ...] = ()
    remote_url: str | None = None
    error: str | None = None


def bundled_anchor_pem() -> str:
    pkg = resources.files("watermark_detector.trust")
    parts = [
        (pkg / "C2PA-TRUST-LIST.pem").read_text(),
        (pkg / "ITL-ANCHORS.pem").read_text(),
    ]
    return "\n".join(parts)


def build_context(extra_anchor_pems: Sequence[str] = ()) -> c2pa.Context:
    extra = [p for p in extra_anchor_pems if p]
    trust: dict[str, str] = {"trust_anchors": bundled_anchor_pem()}
    if extra:
        trust["user_anchors"] = "\n".join(extra)
    return c2pa.Context.from_dict(
        {
            "verify": {
                "remote_manifest_fetch": False,
                "ocsp_fetch": False,
                "verify_trust": True,
            },
            "trust": trust,
        }
    )


_DST_MARK = "digitalsourcetype/"


def _generators(claim: dict[str, Any]) -> tuple[str, ...]:
    info = claim.get("claim_generator_info")
    names: list[str] = []
    if isinstance(info, dict):
        info = [info]
    if isinstance(info, list):
        for g in info:
            if isinstance(g, dict) and g.get("name"):
                names.append(str(g["name"]))
    if not names and isinstance(claim.get("claim_generator"), str):
        names.append(claim["claim_generator"])
    return tuple(names)


def _agent(value: Any) -> str | None:
    if isinstance(value, dict):
        v = value.get("name")
        return str(v) if v is not None else None
    if isinstance(value, str):
        return value
    return None


def _actions(assertions: Any) -> tuple[dict[str, str | None], ...]:
    out: list[dict[str, str | None]] = []
    if not isinstance(assertions, dict):
        return ()
    for key, data in assertions.items():
        if not key.startswith("c2pa.actions") or not isinstance(data, dict):
            continue
        for a in data.get("actions", []) or []:
            if not isinstance(a, dict):
                continue
            dst = a.get("digitalSourceType")
            term = None
            if isinstance(dst, str):
                low = dst.lower()
                i = low.find(_DST_MARK)
                term = dst[i + len(_DST_MARK):] if i >= 0 else dst
            desc = a.get("description")
            out.append(
                {
                    "action": a.get("action"),
                    "digital_source_type": term,
                    "software_agent": _agent(a.get("softwareAgent")),
                    "description": str(desc) if desc is not None else None,
                }
            )
    return tuple(out)


def _parse_manifest(m: dict[str, Any], active: str | None) -> ManifestInfo:
    claim = m.get("claim.v2") or m.get("claim") or {}
    cert = (m.get("signature") or {}).get("certificateInfo") or {}
    serial = None
    if cert.get("serialNumber"):
        try:
            serial = int(str(cert["serialNumber"]), 16)
        except ValueError:
            serial = None
    vr = m.get("validationResults") or {}
    success = vr.get("success", []) or []
    failure = vr.get("failure", []) or []
    trusted_via = None
    for e in success:
        if e.get("code") == "signingCredential.trusted":
            trusted_via = (
                "user-anchor" if "[user_anchors]" in e.get("explanation", "") else "trust-list"
            )
            break
    label = str(m.get("label", ""))
    return ManifestInfo(
        label=label,
        is_active=(label == active),
        signer_subject={str(k): str(v) for k, v in (cert.get("subject") or {}).items()},
        signer_issuer={str(k): str(v) for k, v in (cert.get("issuer") or {}).items()},
        signer_serial=serial,
        claim_generators=_generators(claim),
        actions=_actions(m.get("assertions")),
        success_codes=tuple(e["code"] for e in success if "code" in e),
        failure_codes=tuple(e["code"] for e in failure if "code" in e),
        trusted_via=trusted_via,
    )


def read_c2pa(data: bytes, mime: str, ctx: c2pa.Context) -> C2paResult:
    try:
        reader = c2pa.Reader.try_create(mime, io.BytesIO(data), context=ctx)
        if reader is None:
            return C2paResult(status="absent")
        with reader:
            state = reader.get_validation_state()
            active = json.loads(reader.json()).get("active_manifest")
            manifests = tuple(
                _parse_manifest(m, active)
                for m in json.loads(reader.crjson()).get("manifests", [])
            )
        return C2paResult(
            status="present",
            validation_state=state,
            active_label=active,
            manifests=manifests,
        )
    except c2pa.C2paError as e:
        text = str(e)
        if text.startswith("Remote"):
            marker = "from url "
            i = text.find(marker)
            url = text[i + len(marker):].strip() if i >= 0 else None
            return C2paResult(status="remote", remote_url=url)
        return C2paResult(status="error", error=f"{type(e).__name__}: {e}"[:300])

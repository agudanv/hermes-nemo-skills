#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES.
# SPDX-FileCopyrightText: Modifications Copyright (c) 2026 Patrick Moorhead.
# SPDX-License-Identifier: Apache-2.0
# Modified from the identity-policy patterns in NVIDIA/nemoclaw-community.
"""Pure, deterministic contract for a restricted Slack A2A handshake.

This module is transport-independent. Integrate it at the Slack gateway before
LLM dispatch so peer messages cannot acquire owner context or private tools.
"""

from __future__ import annotations

import os
import re
import secrets
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Mapping, Optional


OWNER_IDS_ENV = "NEMOCLAW_OWNER_SLACK_IDS"
PEER_IDS_ENV = "NEMOCLAW_PEER_AGENT_SLACK_IDS"
CHANNEL_IDS_ENV = "NEMOCLAW_A2A_CHANNEL_IDS"
LOCAL_BOT_ID_ENV = "NEMOCLAW_LOCAL_BOT_SLACK_ID"
POLICY_ENABLED_ENV = "NEMOCLAW_ACTOR_POLICY_ENABLED"
PUBLIC_AGENT_NAME_ENV = "NEMOCLAW_PUBLIC_AGENT_NAME"
PUBLIC_MODEL_ENV = "NEMOCLAW_PUBLIC_MODEL"
PUBLIC_CONTEXT_WINDOW_ENV = "NEMOCLAW_PUBLIC_CONTEXT_WINDOW"

_HEADER_RE = re.compile(r"^\[A2A:v1 (request|response)\]$")
_MENTION_RE = re.compile(r"<@[A-Z0-9]+>")
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,79}$")
_ACTION_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_USER_ID_RE = re.compile(r"^[UW][A-Z0-9]{8,}$")
_CHANNEL_ID_RE = re.compile(r"^[CG][A-Z0-9]{8,}$")
_DM_ID_RE = re.compile(r"^D[A-Z0-9]{8,}$")
_SAFE_VALUE_RE = re.compile(r"[^A-Za-z0-9 ._:/,+-]")
_SLACK_MODEL_INFO_LINKS = frozenset(
    {
        "<http://model.info|model.info>",
        "<https://model.info|model.info>",
    }
)

_SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "credential",
        re.compile(
            r"(?i)\b(?:"
            r"xox[baprs]-[A-Za-z0-9-]{8,}|"
            r"xapp-[A-Za-z0-9-]{8,}|"
            r"github_pat_[A-Za-z0-9_]{12,}|"
            r"gh[pousr]_[A-Za-z0-9]{20,}|"
            r"nvapi-[A-Za-z0-9_-]{12,}|"
            r"sk-[A-Za-z0-9_-]{12,}"
            r")\b"
        ),
    ),
    (
        "email",
        re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    ),
    ("url", re.compile(r"(?i)\bhttps?://\S+")),
    (
        "private_ip",
        re.compile(
            r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
            r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
        ),
    ),
    (
        "absolute_path",
        re.compile(r"(?m)(?:^|[\s`'\"])/(?:home|Users|sandbox|root|var)/\S+"),
    ),
    ("slack_id", re.compile(r"\b[UWBCGD][A-Z0-9]{8,}\b")),
)


class ContractError(ValueError):
    """Raised when configuration or an outbound request is invalid."""


class DisclosureDenied(ContractError):
    """Raised when a public response contains a deterministic private marker."""


@dataclass(frozen=True)
class A2AMessage:
    kind: str
    request_id: str
    action: str
    ttl: int
    fields: Mapping[str, str]


@dataclass(frozen=True)
class PublicAgentInfo:
    agent: str
    model: str
    context_window: Optional[int] = None
    capabilities: tuple[str, ...] = ("model.info",)


@dataclass(frozen=True)
class PeerPolicy:
    enabled: bool
    owner_ids: frozenset[str]
    peer_ids: frozenset[str]
    channel_ids: frozenset[str]
    local_bot_id: str

    @classmethod
    def from_env(
        cls,
        environ: Optional[Mapping[str, str]] = None,
    ) -> "PeerPolicy":
        env = os.environ if environ is None else environ
        return cls(
            enabled=_truthy(env.get(POLICY_ENABLED_ENV, "")),
            owner_ids=_csv_set(env.get(OWNER_IDS_ENV, "")),
            peer_ids=_csv_set(env.get(PEER_IDS_ENV, "")),
            channel_ids=_csv_set(env.get(CHANNEL_IDS_ENV, "")),
            local_bot_id=str(env.get(LOCAL_BOT_ID_ENV, "") or "").strip(),
        )

    def validate(self) -> None:
        if not self.enabled:
            raise ContractError(f"{POLICY_ENABLED_ENV} must be true")
        _validate_ids("owner", self.owner_ids, _USER_ID_RE)
        _validate_ids("peer", self.peer_ids, _USER_ID_RE)
        _validate_ids("channel", self.channel_ids, _CHANNEL_ID_RE)
        if not _USER_ID_RE.fullmatch(self.local_bot_id):
            raise ContractError("invalid local bot ID format")
        if self.owner_ids & self.peer_ids:
            raise ContractError("owner and peer registries must be disjoint")
        if self.local_bot_id in self.owner_ids or self.local_bot_id in self.peer_ids:
            raise ContractError("local bot ID must not be an owner or peer ID")


@dataclass(frozen=True)
class PendingRequest:
    request_id: str
    peer_id: str
    channel_id: str
    action: str
    owner_id: str
    owner_dm_id: str


@dataclass(frozen=True)
class PeerDecision:
    kind: str
    reason: str
    channel_id: Optional[str] = None
    owner_dm_id: Optional[str] = None
    text: Optional[str] = None


class ExpiringReplayCache:
    """Bounded process-local request replay cache."""

    def __init__(self, max_entries: int = 512, ttl_seconds: float = 3600.0):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._entries: "OrderedDict[str, float]" = OrderedDict()
        self._lock = threading.Lock()

    def claim(self, key: str, now: Optional[float] = None) -> bool:
        current = time.monotonic() if now is None else now
        with self._lock:
            self._purge(current)
            if key in self._entries:
                return False
            self._entries[key] = current + self.ttl_seconds
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
            return True

    def _purge(self, now: float) -> None:
        for key in [key for key, expiry in self._entries.items() if expiry <= now]:
            self._entries.pop(key, None)


class PendingRequestStore:
    """Correlate one owner request with exactly one peer response."""

    def __init__(self, max_entries: int = 256, ttl_seconds: float = 900.0):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._entries: "OrderedDict[str, tuple[float, PendingRequest]]" = (
            OrderedDict()
        )
        self._lock = threading.Lock()

    def put(self, pending: PendingRequest) -> None:
        now = time.monotonic()
        with self._lock:
            self._purge(now)
            self._entries[pending.request_id] = (
                now + self.ttl_seconds,
                pending,
            )
            self._entries.move_to_end(pending.request_id)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

    def consume(
        self,
        request_id: str,
        peer_id: str,
        channel_id: str,
        action: str,
    ) -> Optional[PendingRequest]:
        now = time.monotonic()
        with self._lock:
            self._purge(now)
            entry = self._entries.get(request_id)
            if entry is None:
                return None
            pending = entry[1]
            if (
                pending.peer_id != peer_id
                or pending.channel_id != channel_id
                or pending.action != action
            ):
                return None
            self._entries.pop(request_id, None)
            return pending

    def take(self, request_id: str) -> Optional[PendingRequest]:
        now = time.monotonic()
        with self._lock:
            self._purge(now)
            entry = self._entries.pop(request_id, None)
            return entry[1] if entry else None

    def _purge(self, now: float) -> None:
        expired = [
            key for key, (expiry, _) in self._entries.items() if expiry <= now
        ]
        for key in expired:
            self._entries.pop(key, None)


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _csv_set(value: object) -> frozenset[str]:
    return frozenset(
        part.strip() for part in str(value or "").split(",") if part.strip()
    )


def _validate_ids(
    label: str,
    values: frozenset[str],
    pattern: re.Pattern[str],
) -> None:
    if not values:
        raise ContractError(f"at least one {label} ID is required")
    invalid = sorted(value for value in values if not pattern.fullmatch(value))
    if invalid:
        raise ContractError(f"invalid {label} ID format")


def sensitive_reasons(text: str) -> tuple[str, ...]:
    """Return deterministic disclosure categories without echoing content."""

    return tuple(name for name, pattern in _SENSITIVE_PATTERNS if pattern.search(text))


def _safe_value(value: object, *, fallback: str) -> str:
    text = str(value or "").replace("\n", " ").replace("\r", " ").strip()
    text = _SAFE_VALUE_RE.sub("", text)[:160].strip()
    return text or fallback


def _normalize_transport_value(key: str, value: str) -> str:
    """Normalize only Slack's exact auto-linking of the fixed v1 capability."""

    if key in {"action", "capabilities"} and value in _SLACK_MODEL_INFO_LINKS:
        return "model.info"
    return value


def parse_message(text: str) -> Optional[A2AMessage]:
    """Parse the strict A2A v1 envelope or fail closed."""

    if not isinstance(text, str) or len(text) > 2048:
        return None
    cleaned = _MENTION_RE.sub("", text).strip()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if not lines:
        return None
    header_indexes = [
        index for index, line in enumerate(lines) if _HEADER_RE.fullmatch(line)
    ]
    if len(header_indexes) != 1 or header_indexes[0] > 1:
        return None
    header_index = header_indexes[0]
    if header_index == 1 and sensitive_reasons(lines[0]):
        return None
    lines = lines[header_index:]
    header = _HEADER_RE.fullmatch(lines[0])
    if header is None:
        return None

    kind = header.group(1)
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if ":" not in line:
            return None
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if not key or not value or key in fields or len(value) > 256:
            return None
        fields[key] = _normalize_transport_value(key, value)

    request_fields = {"id", "action", "ttl"}
    response_fields = {
        "id",
        "status",
        "action",
        "agent",
        "model",
        "context_window",
        "capabilities",
        "error",
        "ttl",
    }
    allowed = request_fields if kind == "request" else response_fields
    if set(fields) - allowed:
        return None

    request_id = fields.get("id", "")
    action = fields.get("action", "")
    if not _REQUEST_ID_RE.fullmatch(request_id) or not _ACTION_RE.fullmatch(action):
        return None
    try:
        ttl = int(fields.get("ttl", ""))
    except ValueError:
        return None

    if kind == "request":
        if set(fields) != request_fields:
            return None
    else:
        status = fields.get("status")
        if status not in {"ok", "error"} or ttl != 0:
            return None
        required = {"id", "status", "action", "ttl"}
        if status == "ok":
            success_required = required | {
                "agent",
                "model",
                "capabilities",
            }
            if not success_required.issubset(fields) or "error" in fields:
                return None
            if set(fields) - (
                required
                | {"agent", "model", "context_window", "capabilities"}
            ):
                return None
            raw_context = fields.get("context_window")
            if raw_context is not None:
                try:
                    if int(raw_context) <= 0:
                        return None
                except ValueError:
                    return None
            if fields.get("capabilities") != "model.info":
                return None
        else:
            if set(fields) != required | {"error"}:
                return None
        if sensitive_reasons("\n".join(fields.values())):
            return None

    return A2AMessage(
        kind=kind,
        request_id=request_id,
        action=action,
        ttl=ttl,
        fields=fields,
    )


def public_info_from_env(
    environ: Optional[Mapping[str, str]] = None,
) -> PublicAgentInfo:
    env = os.environ if environ is None else environ
    raw_context = str(env.get(PUBLIC_CONTEXT_WINDOW_ENV, "") or "").strip()
    context_window: Optional[int] = None
    if raw_context:
        try:
            parsed = int(raw_context)
        except ValueError as exc:
            raise ContractError("public context window must be an integer") from exc
        if parsed <= 0:
            raise ContractError("public context window must be positive")
        context_window = parsed
    info = PublicAgentInfo(
        agent=str(env.get(PUBLIC_AGENT_NAME_ENV, "") or "NemoClaw agent"),
        model=str(env.get(PUBLIC_MODEL_ENV, "") or env.get("NEMOCLAW_MODEL", "") or "unknown"),
        context_window=context_window,
    )
    if sensitive_reasons(
        "\n".join([info.agent, info.model, *info.capabilities])
    ):
        raise DisclosureDenied("public agent configuration failed deterministic DLP")
    return info


def build_request(
    peer_id: str,
    *,
    action: str = "model.info",
    request_id: Optional[str] = None,
    requester_name: str = "NemoClaw peer",
) -> tuple[str, str]:
    if not _USER_ID_RE.fullmatch(peer_id):
        raise ContractError("invalid peer bot ID")
    if action != "model.info":
        raise ContractError("unsupported A2A action")
    effective_id = request_id or f"req-{secrets.token_hex(8)}"
    if not _REQUEST_ID_RE.fullmatch(effective_id):
        raise ContractError("invalid request ID")
    if sensitive_reasons(str(requester_name or "")):
        raise DisclosureDenied("public requester name failed deterministic DLP")
    safe_requester = _safe_value(requester_name, fallback="NemoClaw peer")
    return effective_id, "\n".join(
        [
            f"<@{peer_id}>",
            (
                f"Hey there - {safe_requester} here. Could you share your "
                "public model and context window?"
            ),
            "[A2A:v1 request]",
            f"id: {effective_id}",
            f"action: {action}",
            "ttl: 1",
        ]
    )


def build_response(
    request: A2AMessage,
    *,
    info: Optional[PublicAgentInfo] = None,
    error: Optional[str] = None,
) -> str:
    if request.kind != "request":
        raise ContractError("response requires a request envelope")
    if error:
        return "\n".join(
            [
                "Hi there - I could not share public model information safely.",
                "[A2A:v1 response]",
                f"id: {request.request_id}",
                "status: error",
                f"action: {request.action}",
                f"error: {_safe_value(error, fallback='request_denied')}",
                "ttl: 0",
            ]
        )

    public_info = info or public_info_from_env()
    if public_info.capabilities != ("model.info",):
        raise ContractError("v1 public capability must be exactly model.info")
    raw_public_values = "\n".join(
        [
            public_info.agent,
            public_info.model,
            *public_info.capabilities,
        ]
    )
    if sensitive_reasons(raw_public_values):
        raise DisclosureDenied("public response failed deterministic DLP")
    safe_agent = _safe_value(public_info.agent, fallback="NemoClaw agent")
    safe_model = _safe_value(public_info.model, fallback="unknown")
    lines = [
        (
            f"Hi there - I'm {safe_agent}. I'm running {safe_model}; "
            "here is my public runtime card."
        ),
        "[A2A:v1 response]",
        f"id: {request.request_id}",
        "status: ok",
        f"action: {request.action}",
        f"agent: {safe_agent}",
        f"model: {safe_model}",
    ]
    if public_info.context_window is not None:
        if public_info.context_window <= 0:
            raise ContractError("public context window must be positive")
        lines.append(f"context_window: {public_info.context_window}")
    capabilities = ",".join(
        _safe_value(item, fallback="") for item in public_info.capabilities
    ).strip(",")
    lines.extend([f"capabilities: {capabilities or 'model.info'}", "ttl: 0"])
    rendered = "\n".join(lines)
    if sensitive_reasons(rendered):
        raise DisclosureDenied("public response failed deterministic DLP")
    return rendered


def create_outbound_request(
    *,
    policy: PeerPolicy,
    pending_store: PendingRequestStore,
    owner_id: str,
    owner_dm_id: str,
    peer_id: str,
    channel_id: str,
    request_id: Optional[str] = None,
    requester_name: Optional[str] = None,
) -> tuple[str, str]:
    policy.validate()
    if owner_id not in policy.owner_ids or not _DM_ID_RE.fullmatch(owner_dm_id):
        raise ContractError("outbound A2A must originate from a registered owner DM")
    if peer_id not in policy.peer_ids or channel_id not in policy.channel_ids:
        raise ContractError("peer or channel is not registered")
    effective_requester = requester_name
    if effective_requester is None:
        effective_requester = public_info_from_env().agent
    effective_id, text = build_request(
        peer_id,
        request_id=request_id,
        requester_name=effective_requester,
    )
    pending_store.put(
        PendingRequest(
            request_id=effective_id,
            peer_id=peer_id,
            channel_id=channel_id,
            action="model.info",
            owner_id=owner_id,
            owner_dm_id=owner_dm_id,
        )
    )
    return effective_id, text


def build_owner_result(message: A2AMessage) -> str:
    if message.fields.get("status") == "error":
        error = _safe_value(
            message.fields.get("error"),
            fallback="request_failed",
        )
        return f"The peer agent could not complete model.info: {error}."

    lines = ["Agent-to-agent result:"]
    if message.fields.get("agent"):
        lines.append(
            "Agent: "
            + _safe_value(message.fields.get("agent"), fallback="peer agent")
        )
    lines.append(
        "Model: " + _safe_value(message.fields.get("model"), fallback="unknown")
    )
    if message.fields.get("context_window"):
        lines.append(
            "Context window: "
            + _safe_value(
                message.fields.get("context_window"),
                fallback="unknown",
            )
        )
    if message.fields.get("capabilities"):
        lines.append(
            "Public capabilities: "
            + _safe_value(
                message.fields.get("capabilities"),
                fallback="model.info",
            )
        )
    return "\n".join(lines)


def handle_peer_message(
    *,
    policy: PeerPolicy,
    replay_cache: ExpiringReplayCache,
    pending_store: PendingRequestStore,
    sender_id: str,
    channel_id: str,
    is_bot: bool,
    text: str,
    public_info: Optional[PublicAgentInfo] = None,
) -> PeerDecision:
    """Evaluate one bot-authored event without invoking an LLM."""

    try:
        policy.validate()
    except ContractError:
        return PeerDecision("drop", "invalid_policy")
    if (
        not is_bot
        or sender_id not in policy.peer_ids
        or channel_id not in policy.channel_ids
    ):
        return PeerDecision("drop", "unregistered_actor_or_channel")
    mentions = _MENTION_RE.findall(text)
    if mentions != [f"<@{policy.local_bot_id}>"]:
        return PeerDecision("drop", "invalid_local_bot_mention")

    message = parse_message(text)
    if message is None:
        return PeerDecision("drop", "invalid_envelope")

    if message.kind == "response":
        pending = pending_store.consume(
            message.request_id,
            sender_id,
            channel_id,
            message.action,
        )
        if pending is None:
            return PeerDecision("drop", "unsolicited_or_mismatched_response")
        if (
            pending.owner_id not in policy.owner_ids
            or not _DM_ID_RE.fullmatch(pending.owner_dm_id)
            or pending.owner_dm_id in policy.channel_ids
        ):
            return PeerDecision("drop", "invalid_owner_return_route")
        return PeerDecision(
            "owner_result",
            "accepted_response",
            owner_dm_id=pending.owner_dm_id,
            text=build_owner_result(message),
        )

    if message.ttl != 1:
        return PeerDecision("drop", "invalid_request_ttl")
    replay_key = f"{sender_id}:{channel_id}:{message.request_id}"
    if not replay_cache.claim(replay_key):
        return PeerDecision("drop", "duplicate_request")
    if message.action != "model.info":
        response = build_response(message, error="unsupported_action")
    else:
        try:
            response = build_response(message, info=public_info)
        except (ContractError, DisclosureDenied):
            response = build_response(message, error="disclosure_denied")
    return PeerDecision(
        "reply",
        "handled_request",
        channel_id=channel_id,
        text=f"<@{sender_id}>\n{response}",
    )


def expire_request(
    request_id: str,
    *,
    policy: PeerPolicy,
    pending_store: PendingRequestStore,
) -> PeerDecision:
    pending = pending_store.take(request_id)
    if pending is None:
        return PeerDecision("drop", "already_completed_or_unknown")
    if (
        pending.owner_id not in policy.owner_ids
        or not _DM_ID_RE.fullmatch(pending.owner_dm_id)
    ):
        return PeerDecision("drop", "invalid_owner_return_route")
    return PeerDecision(
        "owner_result",
        "request_timeout",
        owner_dm_id=pending.owner_dm_id,
        text=(
            "The registered peer agent did not respond to the model.info "
            "request before the timeout. No retry was sent."
        ),
    )

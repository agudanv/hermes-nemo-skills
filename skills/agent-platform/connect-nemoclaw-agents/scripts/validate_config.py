#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 Patrick Moorhead.
# SPDX-License-Identifier: Apache-2.0
"""Validate A2A environment configuration without reading or printing secrets."""

from __future__ import annotations

import os
import sys

from a2a_contract import (
    ContractError,
    PeerPolicy,
    PUBLIC_AGENT_NAME_ENV,
    PUBLIC_CONTEXT_WINDOW_ENV,
    PUBLIC_MODEL_ENV,
    public_info_from_env,
)


def _masked(values: frozenset[str]) -> str:
    return ",".join(f"...{value[-4:]}" for value in sorted(values))


def main() -> int:
    try:
        policy = PeerPolicy.from_env()
        policy.validate()
        info = public_info_from_env()
    except ContractError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    allow_bots = os.environ.get("SLACK_ALLOW_BOTS", "").strip().lower()
    if allow_bots != "mentions":
        print("FAIL: SLACK_ALLOW_BOTS must be mentions", file=sys.stderr)
        return 1
    if not info.agent.strip():
        print(f"FAIL: {PUBLIC_AGENT_NAME_ENV} is required", file=sys.stderr)
        return 1
    if not info.model.strip() or info.model == "unknown":
        print(f"FAIL: {PUBLIC_MODEL_ENV} is required", file=sys.stderr)
        return 1

    print("PASS: restricted A2A configuration is structurally valid")
    print(f"  owners: {_masked(policy.owner_ids)}")
    print(f"  local bot: ...{policy.local_bot_id[-4:]}")
    print(f"  peers: {_masked(policy.peer_ids)}")
    print(f"  channels: {_masked(policy.channel_ids)}")
    print(f"  public agent name: {info.agent}")
    print(f"  public model configured: yes")
    print(
        "  public context window configured: "
        + ("yes" if info.context_window is not None else "no")
    )
    print("  bot traffic: mentions only")
    print("  secrets inspected: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

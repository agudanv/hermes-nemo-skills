---
name: agent-collaboration
description: Use when the authenticated owner asks this NemoClaw agent to query a registered peer agent for public model information or asks how the restricted Slack agent-room handshake works.
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 PicoNVIDIA -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Agent Collaboration

Use the typed `nemoclaw_a2a_request` tool. Never construct Slack API calls,
inspect Slack credentials, or improvise an agent protocol in the terminal.

Start only from the authenticated owner's direct message. The registered
agent-room channel is visible transport; a validated result returns
asynchronously to the originating owner DM.

Version 1 supports only:

- action `model.info`
- peer bot IDs in `$NEMOCLAW_PEER_AGENT_SLACK_IDS`
- channel IDs in `$NEMOCLAW_A2A_CHANNEL_IDS`
- request TTL `1`
- response TTL `0`

The gateway, not this skill, must enforce sender identity, exact channel
registration, replay protection, request correlation, owner-only return
routing, deterministic DLP, and response-loop prevention.

The channel request and response include a short conversational sentence for
humans, but that sentence is deterministic and limited to configured public
agent/model fields. Peer prose never enters the LLM.

Never claim a peer is configured when either registry is empty. Never send a
live request during setup or testing without explicit owner approval.

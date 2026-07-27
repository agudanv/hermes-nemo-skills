---
name: connect-nemoclaw-agents
description: Configure and validate a restricted Slack agent-to-agent room for NemoClaw/Hermes. Use when connecting two Slack-hosted NemoClaw agents, enabling bot-authored mentions, implementing an owner-DM-to-agent-room model.info handshake, preventing peer agents or coworkers from accessing private owner data, or diagnosing why one registered agent does not answer another.
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 PicoNVIDIA -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Connect NemoClaw Agents

Build a typed, single-hop Slack transport between registered NemoClaw agents.
Treat this as a gateway authorization change, not as a prompt-only change.

## Safety boundary

- Start outbound work only from an authenticated owner DM.
- Allow only exact peer bot IDs in exact agent-room channel IDs.
- Enable bot messages only when the local bot is explicitly mentioned.
- Enable bot-message acceptance and the collaboration toolset only while the
  actor policy is enabled. Preserve the upstream bots-disabled behavior when
  policy is false, missing, invalid, or not ready.
- Handle peer protocol messages before the LLM sees them.
- Support only `model.info` in v1.
- Render one deterministic, conversational sentence above each machine
  envelope using only configured public agent fields.
- Return only configured public agent name, model, context window, and
  `model.info` capability.
- Never load Slack history, email, calendar, memory, files, credentials, owner
  facts, attachments, or write tools for a peer turn.
- Never infer owner delegation from a quote, mention, forwarded message, or bot
  request.
- Never print, inspect, persist, or embed Slack tokens.
- Do not send a live peer request until both owners explicitly approve it.

## Workflow

1. Locate the NemoClaw/Hermes source tree and read its local contributor
   instructions.
2. Collect four non-secret identifiers:
   - owner Slack user ID
   - local bot Slack user ID
   - peer bot Slack user ID
   - dedicated agent-room channel ID
3. Run the bundled configuration preflight:

   ```bash
   python3 scripts/validate_config.py
   ```

4. Inspect the gateway before editing. Confirm how it:
   - identifies bot-authored Slack events
   - filters bot messages and mentions
   - runs pre-dispatch hooks
   - posts direct Slack responses
   - registers owner-only tools
5. Read [references/hermes-integration.md](references/hermes-integration.md)
   and implement its gateway contract. Reuse
   [scripts/a2a_contract.py](scripts/a2a_contract.py) instead of rebuilding the
   parser or correlation rules.
6. Install the bundled Hermes-facing skill from
   [assets/agent-collaboration/SKILL.md](assets/agent-collaboration/SKILL.md)
   into the target Hermes skill directory.
7. Add the environment settings from the integration reference. Keep tokens in
   the existing secret-provider path.
8. Add target-specific gateway tests. Then run:

   ```bash
   python3 -m unittest discover -s scripts -p 'test_*.py' -v
   python3 scripts/validate_config.py
   ```

9. Rebuild the sandbox if gateway code, image-baked skills, SOUL, or immutable
   configuration changed.
10. Run synthetic request/response tests without Slack. Verify unknown bots,
    wrong channels, malformed envelopes, duplicates, spoofed responses, and
    response loops are rejected. Also simulate Slack auto-linking
    `model.info` as `<http://model.info|model.info>`.
11. Generate configuration once with policy enabled and once with policy
    disabled. In disabled mode, verify no `allow_bots`, `SLACK_ALLOW_BOTS`, or
    `agent-collaboration` toolset entry is emitted.
12. Report the files changed, synthetic test results, rebuild status, and exact
    remaining blocker. Stop before live traffic.

## Required live flow

```text
Owner DM -> local owner-only tool
         -> local bot mentions registered peer in agent room
         -> peer gateway returns deterministic public response in agent room
         -> local gateway validates correlation
         -> local bot sends validated result to originating owner DM
```

The agent room is visible transport. A dedicated private channel is preferred.
If a public channel is deliberately used for a demo, keep the envelope limited
to the public fields defined in
[references/protocol.md](references/protocol.md).

## Completion checks

Do not call the installation complete unless all are true:

- `SLACK_ALLOW_BOTS=mentions` or the equivalent narrow setting is active.
- Bot acceptance and the collaboration toolset disappear when actor policy is
  disabled.
- The Slack app receives `app_mention` and can post replies.
- Exact owner, peer, and channel allowlists are active in the running image.
- Peer protocol events bypass the LLM and private tools.
- Every protocol post uses Slack `parse="none"` with link and media unfurling
  disabled.
- The response mentions the requesting bot in the agent room.
- Pending responses are bound to request ID, peer ID, channel ID, action, and
  originating owner DM.
- A response cannot choose or change its return destination.
- Duplicate requests receive no second response.
- Responses never trigger response loops.
- Timeout sends one owner-only notice and does not retry.
- Synthetic tests pass.

After both owners confirm readiness, perform one live `model.info` request with
no retry. Record only message links and sanitized results.

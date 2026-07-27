<!-- SPDX-FileCopyrightText: Copyright (c) 2026 PicoNVIDIA -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Hermes Gateway Integration

## Architecture

Enforce the peer boundary in the gateway before LLM dispatch:

```text
Slack event
  -> identify sender and bot marker
  -> require explicit mention
  -> exact peer/channel allowlist
  -> isolate one optional deterministic conversation line
  -> strict A2A parser and replay/correlation checks
  -> direct deterministic Slack response
  -> skip LLM dispatch
```

A `SKILL.md` alone cannot establish this boundary because a skill loads after
the gateway has accepted a turn. Keep the prompt layer for owner routing and
the gateway layer for authorization.

For the `personal-community-sentiment-triage` example in current
`NVIDIA/nemoclaw-community`, expect to update:

- `agents/hermes/patches/sitecustomize.py`
- a new actor-policy/A2A module under `agents/hermes/patches/`
- `agents/hermes/plugins/nemoclaw/__init__.py` and its manifest
- `agents/hermes/Dockerfile`
- `agents/hermes/generate-config.ts`
- `agents/hermes/SOUL.md`
- `agents/hermes/skills/agent-platform/agent-collaboration/SKILL.md`
- `scripts/03-sandbox.sh`
- `.env.example` and `.env.example.s3`
- focused policy and integration tests

## Environment

Bake or inject these non-secret values through the existing immutable
configuration path:

```env
NEMOCLAW_ACTOR_POLICY_ENABLED=true
NEMOCLAW_OWNER_SLACK_IDS=<OWNER_USER_ID>
NEMOCLAW_LOCAL_BOT_SLACK_ID=<LOCAL_BOT_USER_ID>
NEMOCLAW_PEER_AGENT_SLACK_IDS=<PEER_BOT_USER_ID>
NEMOCLAW_A2A_CHANNEL_IDS=<AGENT_ROOM_CHANNEL_ID>
NEMOCLAW_PUBLIC_AGENT_NAME=<PUBLIC_AGENT_NAME>
NEMOCLAW_MODEL=<PUBLIC_MODEL_NAME>
NEMOCLAW_PUBLIC_CONTEXT_WINDOW=<OPTIONAL_POSITIVE_INTEGER>
NEMOCLAW_A2A_RESPONSE_TIMEOUT_SECONDS=45
SLACK_ALLOW_BOTS=mentions
```

Do not add Slack tokens to these values. Keep bot and app tokens in the
existing secret provider.

Treat `NEMOCLAW_ACTOR_POLICY_ENABLED` as an explicit opt-in. Require real
owner, local-bot, peer, and channel IDs when it is true; do not silently fall
back to sample or synthetic IDs. When it is false or missing:

- do not emit `allow_bots` in Hermes Slack platform configuration
- do not emit `SLACK_ALLOW_BOTS`
- do not add the `agent-collaboration` toolset
- do not register the outbound A2A tool or hooks
- preserve Hermes's default rejection of bot-authored messages

## Slack app

Require:

- the app is installed in the workspace
- both bots are members of the agent-room channel
- Socket Mode or the existing Events API transport is connected
- `app_mention` event subscription
- `app_mentions:read` bot scope
- `chat:write` bot scope
- app-level `connections:write` for Socket Mode

Use a dedicated private channel when possible. A public channel is acceptable
only for intentionally public protocol fields.

## Bot identity

Do not trust only `event["user"]`. Mark a source as a bot when the Slack event
contains an authenticated bot marker such as `bot_id` or the platform adapter
has resolved the sender as a bot user. Carry `is_bot` into the pre-dispatch
policy.

Drop bot-authored messages unless all are true:

- the local bot is explicitly mentioned
- `is_bot` is true
- sender ID is registered
- channel ID is registered
- the strict A2A envelope parses

Never turn on bot-message acceptance independently from this policy. The
configuration generator must gate `allow_bots: "mentions"`,
`SLACK_ALLOW_BOTS=mentions`, and the `agent-collaboration` toolset on the same
validated policy-enabled condition.

Post every protocol request and response through `chat.postMessage` with
`parse="none"`, `unfurl_links=false`, and `unfurl_media=false`. Slack otherwise
auto-links the fixed `model.info` token and changes the event text. For
backward compatibility, normalize only the exact
`<http://model.info|model.info>` or `<https://model.info|model.info>` spelling
back to `model.info`; reject every other link.

Hermes v2026.7.1 removes the local app mention before assigning normalized
`MessageEvent.text`. Pass the original Slack payload text from
`MessageEvent.raw_message["text"]`, or intercept the event in
`SlackAdapter._handle_slack_message` before normalization. Never use the
mention-stripped text for the protocol check.

Require exactly one mention and require it to be the configured local bot ID.
Reject zero mentions, extra mentions, and a mention of a different bot.

Patch the Slack adapter at interpreter startup so `SessionSource.is_bot`
survives normalization. Resolve the actor once at the adapter edge and again
in pre-dispatch. When actor policy is enabled, drop every peer, collaborator,
shared-channel, or unknown event at the adapter edge if the policy runtime is
not ready. This prevents Hermes from continuing after plugin import or hook
registration failures.

## Adapter sketch

Adapt names to the installed Hermes version:

```python
decision = handle_peer_message(
    policy=peer_policy,
    replay_cache=replay_cache,
    pending_store=pending_store,
    sender_id=source.user_id,
    channel_id=source.chat_id,
    is_bot=source.is_bot,
    text=event.raw_message["text"],
    public_info=public_info,
)

if decision.kind == "reply":
    await slack_client.chat_postMessage(
        channel=decision.channel_id,
        text=decision.text,
        parse="none",
        unfurl_links=False,
        unfurl_media=False,
    )
    return SKIP_LLM

if decision.kind == "owner_result":
    await slack_client.chat_postMessage(
        channel=decision.owner_dm_id,
        text=decision.text,
        parse="none",
        unfurl_links=False,
        unfurl_media=False,
    )
    return SKIP_LLM

return SKIP_LLM
```

Register this hook before permissive pre-dispatch hooks. Fail closed if the
policy hook or bot-identity patch does not load.

In Hermes v2026.7.1, `pre_gateway_dispatch` is synchronous and hook exceptions
may be logged without stopping dispatch. The policy hook must catch every
exception and return `{"action": "skip", "reason": "actor_policy_error"}` while
policy is enabled.

For a deterministic response, schedule work on the running event loop and
retain the task in the gateway background-task set. Protocol replies must use
the direct Slack post path so the transport flags above are guaranteed. For an
owner-DM relay, use the same secret-backed client. If scheduling fails, still
return `skip`; never fall through to LLM dispatch. Log only exception types,
not event content or token values.

## Owner-only outbound tool

Expose a typed tool such as `nemoclaw_a2a_request` only in an authenticated
owner DM. It accepts:

- registered `peer_id`
- registered `channel_id`
- fixed action `model.info`

The handler must call `create_outbound_request`, post its returned text to the
registered channel, and schedule one timeout. If Slack posting fails, remove
the pending request and report the error privately. Never retry automatically.

Hermes registers tools globally, so tool visibility alone is not an
authorization boundary. Enforce owner-only use three ways:

1. Bind the authenticated actor to a request-local `ContextVar` at the Slack
   adapter/gateway edge and reset it in `finally`.
2. Have the tool handler require the `OWNER_PRIVATE` role before any Slack
   call or pending-request write.
3. Have `pre_tool_call` block the tool for every non-owner role, while
   restricted agents receive only a deliberately public toolset.

Do not use mutable global sender state or a cached per-tool `check_fn`; either
can leak authority across concurrent Slack turns.

## Public responder

Build the response from immutable public configuration. Do not ask the LLM to
answer `model.info`; deterministic handling prevents tool calls, empty model
responses, prompt injection, and private-context disclosure.

Make the exchange readable by placing one short deterministic sentence before
the envelope. The request sentence may contain only the configured public agent
name. The response sentence may contain only the configured public agent name
and model. The parser may ignore at most one such line before the envelope, and
must reject it when deterministic disclosure checks find a private marker.

## Target tests

Add gateway tests that prove:

- owner has full capabilities only in the owner's DM
- owner in a shared channel is restricted
- collaborator DMs and shared-channel turns cannot access private tools
- unknown bots and humans using a peer ID are dropped
- registered peer in the wrong channel is dropped
- malformed and duplicate requests are dropped
- zero, wrong, or additional mentions are dropped
- normalized mention-stripped text is never used for protocol validation
- exact Slack auto-linking of `model.info` is normalized and arbitrary links
  are rejected
- protocol posts disable Slack URL parsing and unfurling
- conversational text is deterministic, public-only, and never sent to the LLM
- one valid request returns one public response
- response correlation includes peer, channel, request, and action
- mismatch cannot consume a valid pending request
- response returns only to the stored owner DM
- response cannot trigger another channel response
- timeout sends one private notice and no retry
- missing policy integration fails closed
- policy-disabled generated config contains no bot allowance or collaboration
  toolset
- policy-enabled startup with missing or placeholder IDs fails before sandbox
  creation
- concurrent owner and collaborator turns cannot exchange actor authority
- hook exceptions return `skip` and never reach the LLM

Run the bundled pure tests first, then the target repository's full test suite.
Rebuild when the running sandbox bakes gateway code or configuration into its
image.

## Live test

Do not send a live message during installation. After both owners confirm the
two agents are ready, send exactly one `model.info` request with no retry.
Confirm:

1. request is visible in the agent room
2. peer response is visible in the agent room
3. validated result reaches the originating owner DM
4. no private data or tool output appears in the agent room

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 PicoNVIDIA -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Restricted Slack A2A v1

Use a dedicated Slack channel as visible transport between explicitly
registered bots. The protocol is line-oriented and single-hop.

## Request

```text
<@PEER_BOT_ID>
Hey there - Pico NemoClaw here. Could you share your public model and context window?
[A2A:v1 request]
id: req-0123456789abcdef
action: model.info
ttl: 1
```

Requirements:

- Generate a new unpredictable request ID.
- Mention exactly the registered peer bot.
- Permit at most one deterministic conversation line immediately before the
  envelope. It never enters the LLM.
- Allow only `model.info`.
- Require `ttl: 1`.
- Cache the sender, channel, and request ID to reject replays.
- Do not include owner data, return routes, or free-form payloads.
- Post with Slack `parse="none"` and link/media unfurling disabled.
- Normalize only Slack's exact auto-linked representation of `model.info`;
  reject arbitrary links.

## Success response

```text
<@REQUESTING_BOT_ID>
Hi there - I'm Peer NemoClaw. I'm running vendor/model-name; here is my public runtime card.
[A2A:v1 response]
id: req-0123456789abcdef
status: ok
action: model.info
agent: Example NemoClaw
model: vendor/model-name
context_window: 131072
capabilities: model.info
ttl: 0
```

`context_window` is optional. All other fields shown are required.

## Error response

```text
<@REQUESTING_BOT_ID>
Hi there - I could not share public model information safely.
[A2A:v1 response]
id: req-0123456789abcdef
status: error
action: model.info
error: request_denied
ttl: 0
```

## Correlation

Bind each pending request to:

- request ID
- exact peer bot ID
- exact agent-room channel ID
- action
- authenticated owner ID
- originating owner DM channel ID

The response cannot provide or alter the owner return route. Consume a pending
request only after every peer-controlled correlation field matches. A
mismatched response must not invalidate the legitimate pending request.

## Loop prevention

- A request may produce one channel response.
- A response may produce only an owner-DM result.
- A response never produces another channel response.
- A duplicate request produces no response.
- A timeout produces one owner-DM notice and no retry.

## Public payload

The v1 payload may disclose only:

- configured public agent name
- configured model name
- configured context window
- `model.info` capability

Do not generate these fields from conversation history, memory, files, email,
calendar, Slack history, credentials, endpoints, paths, or owner context.

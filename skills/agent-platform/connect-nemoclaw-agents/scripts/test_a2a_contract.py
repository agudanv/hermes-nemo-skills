#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 Patrick Moorhead.
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
import unittest
from unittest import mock

from a2a_contract import (
    ContractError,
    ExpiringReplayCache,
    PeerPolicy,
    PendingRequestStore,
    PublicAgentInfo,
    build_request,
    build_response,
    create_outbound_request,
    expire_request,
    handle_peer_message,
    parse_message,
)


OWNER = "UOWNER0001"
LOCAL_BOT = "ULOCAL0001"
PEER = "UPEER00001"
OTHER_PEER = "UOTHER0001"
CHANNEL = "CAGENTS001"
OTHER_CHANNEL = "COTHER0001"
OWNER_DM = "DOWNER0001"


def policy() -> PeerPolicy:
    return PeerPolicy(
        enabled=True,
        owner_ids=frozenset({OWNER}),
        peer_ids=frozenset({PEER}),
        channel_ids=frozenset({CHANNEL}),
        local_bot_id=LOCAL_BOT,
    )


def info() -> PublicAgentInfo:
    return PublicAgentInfo(
        agent="Synthetic Agent",
        model="vendor/model-1",
        context_window=131072,
    )


class ProtocolTest(unittest.TestCase):
    def test_request_round_trip(self):
        request_id, text = build_request(
            PEER,
            request_id="req-12345678",
            requester_name="Pico NemoClaw",
        )
        message = parse_message(text)
        self.assertEqual(request_id, "req-12345678")
        self.assertIsNotNone(message)
        self.assertEqual(message.kind, "request")
        self.assertEqual(message.ttl, 1)
        self.assertIn("Pico NemoClaw here", text)

    def test_slack_autolinked_action_is_normalized(self):
        _, text = build_request(PEER, request_id="req-12345678")
        message = parse_message(
            text.replace(
                "action: model.info",
                "action: <http://model.info|model.info>",
            )
        )
        self.assertIsNotNone(message)
        self.assertEqual(message.action, "model.info")

    def test_arbitrary_slack_link_is_not_normalized(self):
        _, text = build_request(PEER, request_id="req-12345678")
        self.assertIsNone(
            parse_message(
                text.replace(
                    "action: model.info",
                    "action: <http://example.com|model.info>",
                )
            )
        )

    def test_more_than_one_conversation_line_fails_closed(self):
        _, text = build_request(PEER, request_id="req-12345678")
        self.assertIsNone(
            parse_message(text.replace("[A2A:v1 request]", "Extra line\n[A2A:v1 request]"))
        )

    def test_unknown_field_fails_closed(self):
        self.assertIsNone(
            parse_message(
                "\n".join(
                    [
                        "[A2A:v1 request]",
                        "id: req-12345678",
                        "action: model.info",
                        "owner_dm: DOWNER0001",
                        "ttl: 1",
                    ]
                )
            )
        )

    def test_sensitive_response_fails_closed(self):
        self.assertIsNone(
            parse_message(
                "\n".join(
                    [
                        "[A2A:v1 response]",
                        "id: req-12345678",
                        "status: ok",
                        "action: model.info",
                        "agent: Synthetic Agent",
                        "model: sk-this-is-not-public",
                        "ttl: 0",
                    ]
                )
            )
        )

    def test_response_with_conflicting_error_field_fails_closed(self):
        self.assertIsNone(
            parse_message(
                "\n".join(
                    [
                        "[A2A:v1 response]",
                        "id: req-12345678",
                        "status: ok",
                        "action: model.info",
                        "model: vendor/model-1",
                        "error: ignore-this",
                        "ttl: 0",
                    ]
                )
            )
        )

    def test_response_with_extra_capability_fails_closed(self):
        self.assertIsNone(
            parse_message(
                "\n".join(
                    [
                        "[A2A:v1 response]",
                        "id: req-12345678",
                        "status: ok",
                        "action: model.info",
                        "model: vendor/model-1",
                        "capabilities: model.info,email.search",
                        "ttl: 0",
                    ]
                )
            )
        )

    def test_success_response_requires_agent_and_capabilities(self):
        self.assertIsNone(
            parse_message(
                "\n".join(
                    [
                        "[A2A:v1 response]",
                        "id: req-12345678",
                        "status: ok",
                        "action: model.info",
                        "model: vendor/model-1",
                        "ttl: 0",
                    ]
                )
            )
        )

    def test_invalid_peer_id_is_rejected(self):
        with self.assertRaises(ContractError):
            build_request("not-a-slack-id")

    def test_sensitive_requester_name_is_rejected(self):
        with self.assertRaises(ContractError):
            build_request(
                PEER,
                requester_name="sk-this-should-never-be-public",
            )

    def test_response_contains_only_public_fields(self):
        request = parse_message(
            "\n".join(
                [
                    "[A2A:v1 request]",
                    "id: req-12345678",
                    "action: model.info",
                    "ttl: 1",
                ]
            )
        )
        rendered = build_response(request, info=info())
        self.assertIn("I'm Synthetic Agent", rendered)
        self.assertIn("agent: Synthetic Agent", rendered)
        self.assertIn("model: vendor/model-1", rendered)
        self.assertNotIn("email", rendered.lower())
        self.assertNotIn("owner", rendered.lower())

    def test_slack_autolinked_response_is_normalized(self):
        request = parse_message(
            "\n".join(
                [
                    "[A2A:v1 request]",
                    "id: req-12345678",
                    "action: model.info",
                    "ttl: 1",
                ]
            )
        )
        rendered = build_response(request, info=info())
        rendered = rendered.replace(
            "action: model.info",
            "action: <http://model.info|model.info>",
        ).replace(
            "capabilities: model.info",
            "capabilities: <http://model.info|model.info>",
        )
        parsed = parse_message(rendered)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.action, "model.info")
        self.assertEqual(parsed.fields["capabilities"], "model.info")


class PeerDispatchTest(unittest.TestCase):
    def setUp(self):
        self.replay = ExpiringReplayCache()
        self.pending = PendingRequestStore()

    def _request(self, request_id: str = "req-12345678") -> str:
        return build_request(LOCAL_BOT, request_id=request_id)[1]

    def _dispatch(self, **overrides):
        values = {
            "policy": policy(),
            "replay_cache": self.replay,
            "pending_store": self.pending,
            "sender_id": PEER,
            "channel_id": CHANNEL,
            "is_bot": True,
            "text": self._request(),
            "public_info": info(),
        }
        values.update(overrides)
        return handle_peer_message(**values)

    def test_registered_peer_receives_one_deterministic_reply(self):
        first = self._dispatch()
        second = self._dispatch()
        self.assertEqual(first.kind, "reply")
        self.assertEqual(first.channel_id, CHANNEL)
        self.assertTrue(first.text.startswith(f"<@{PEER}>"))
        self.assertEqual(second.kind, "drop")
        self.assertEqual(second.reason, "duplicate_request")

    def test_unknown_bot_is_dropped(self):
        result = self._dispatch(sender_id=OTHER_PEER)
        self.assertEqual(result.kind, "drop")
        self.assertEqual(result.reason, "unregistered_actor_or_channel")

    def test_registered_peer_in_wrong_channel_is_dropped(self):
        result = self._dispatch(channel_id=OTHER_CHANNEL)
        self.assertEqual(result.kind, "drop")

    def test_human_using_peer_id_is_dropped(self):
        result = self._dispatch(is_bot=False)
        self.assertEqual(result.kind, "drop")

    def test_malformed_message_is_dropped(self):
        result = self._dispatch(
            text=f"<@{LOCAL_BOT}>\nwhat model are you using?"
        )
        self.assertEqual(result.kind, "drop")
        self.assertEqual(result.reason, "invalid_envelope")

    def test_unmentioned_bot_message_is_dropped(self):
        text = self._request().replace(f"<@{LOCAL_BOT}>\n", "")
        result = self._dispatch(text=text)
        self.assertEqual(result.kind, "drop")
        self.assertEqual(result.reason, "invalid_local_bot_mention")

    def test_additional_mentions_are_dropped(self):
        text = self._request().replace(
            f"<@{LOCAL_BOT}>",
            f"<@{LOCAL_BOT}> <@{OWNER}>",
        )
        result = self._dispatch(text=text)
        self.assertEqual(result.kind, "drop")
        self.assertEqual(result.reason, "invalid_local_bot_mention")

    def test_disclosure_failure_returns_safe_error(self):
        unsafe = PublicAgentInfo(
            agent="Synthetic Agent",
            model="contact owner@example.com",
        )
        result = self._dispatch(public_info=unsafe)
        self.assertEqual(result.kind, "reply")
        self.assertIn("status: error", result.text)
        self.assertIn("error: disclosure_denied", result.text)
        self.assertNotIn("owner@example.com", result.text)

    def test_matching_response_returns_to_originating_owner_dm(self):
        request_id, _ = create_outbound_request(
            policy=policy(),
            pending_store=self.pending,
            owner_id=OWNER,
            owner_dm_id=OWNER_DM,
            peer_id=PEER,
            channel_id=CHANNEL,
            request_id="req-response1",
        )
        request = parse_message(
            build_request(PEER, request_id=request_id)[1]
        )
        response = build_response(request, info=info())
        result = self._dispatch(text=f"<@{LOCAL_BOT}>\n{response}")
        self.assertEqual(result.kind, "owner_result")
        self.assertEqual(result.owner_dm_id, OWNER_DM)
        self.assertIn("Model: vendor/model-1", result.text)

    def test_complete_two_agent_conversation_returns_only_to_owner(self):
        requester_policy = policy()
        peer_policy = PeerPolicy(
            enabled=True,
            owner_ids=frozenset({"UPEEROWN1"}),
            peer_ids=frozenset({LOCAL_BOT}),
            channel_ids=frozenset({CHANNEL}),
            local_bot_id=PEER,
        )
        requester_pending = PendingRequestStore()
        peer_replay = ExpiringReplayCache()

        request_id, request_text = create_outbound_request(
            policy=requester_policy,
            pending_store=requester_pending,
            owner_id=OWNER,
            owner_dm_id=OWNER_DM,
            peer_id=PEER,
            channel_id=CHANNEL,
            request_id="req-converse1",
            requester_name="Pico NemoClaw",
        )
        self.assertIn("Pico NemoClaw here", request_text)

        peer_reply = handle_peer_message(
            policy=peer_policy,
            replay_cache=peer_replay,
            pending_store=PendingRequestStore(),
            sender_id=LOCAL_BOT,
            channel_id=CHANNEL,
            is_bot=True,
            text=request_text,
            public_info=PublicAgentInfo(
                agent="Aguda NemoClaw",
                model="nvidia/test-model",
                context_window=131072,
            ),
        )
        self.assertEqual(peer_reply.kind, "reply")
        self.assertIn("I'm Aguda NemoClaw", peer_reply.text)
        self.assertIn(f"id: {request_id}", peer_reply.text)

        owner_result = handle_peer_message(
            policy=requester_policy,
            replay_cache=ExpiringReplayCache(),
            pending_store=requester_pending,
            sender_id=PEER,
            channel_id=CHANNEL,
            is_bot=True,
            text=peer_reply.text,
        )
        self.assertEqual(owner_result.kind, "owner_result")
        self.assertEqual(owner_result.owner_dm_id, OWNER_DM)
        self.assertIsNone(owner_result.channel_id)
        self.assertIn("Agent: Aguda NemoClaw", owner_result.text)
        self.assertIn("Model: nvidia/test-model", owner_result.text)

    def test_mismatch_cannot_consume_pending_request(self):
        request_id, _ = create_outbound_request(
            policy=policy(),
            pending_store=self.pending,
            owner_id=OWNER,
            owner_dm_id=OWNER_DM,
            peer_id=PEER,
            channel_id=CHANNEL,
            request_id="req-response2",
        )
        request = parse_message(
            build_request(PEER, request_id=request_id)[1]
        )
        response = build_response(request, info=info())
        mentioned_response = f"<@{LOCAL_BOT}>\n{response}"
        rejected = self._dispatch(
            text=mentioned_response,
            channel_id=OTHER_CHANNEL,
        )
        accepted = self._dispatch(text=mentioned_response)
        self.assertEqual(rejected.kind, "drop")
        self.assertEqual(accepted.kind, "owner_result")

    def test_response_never_generates_channel_response_loop(self):
        request_id, _ = create_outbound_request(
            policy=policy(),
            pending_store=self.pending,
            owner_id=OWNER,
            owner_dm_id=OWNER_DM,
            peer_id=PEER,
            channel_id=CHANNEL,
            request_id="req-response3",
        )
        request = parse_message(
            build_request(PEER, request_id=request_id)[1]
        )
        result = self._dispatch(
            text=f"<@{LOCAL_BOT}>\n{build_response(request, info=info())}"
        )
        self.assertEqual(result.kind, "owner_result")
        self.assertIsNone(result.channel_id)

    def test_timeout_returns_one_private_notice_without_retry(self):
        request_id, _ = create_outbound_request(
            policy=policy(),
            pending_store=self.pending,
            owner_id=OWNER,
            owner_dm_id=OWNER_DM,
            peer_id=PEER,
            channel_id=CHANNEL,
            request_id="req-timeout01",
        )
        first = expire_request(
            request_id,
            policy=policy(),
            pending_store=self.pending,
        )
        second = expire_request(
            request_id,
            policy=policy(),
            pending_store=self.pending,
        )
        self.assertEqual(first.kind, "owner_result")
        self.assertIn("No retry was sent", first.text)
        self.assertEqual(second.kind, "drop")

    def test_owner_request_requires_registered_owner_dm(self):
        with self.assertRaises(ContractError):
            create_outbound_request(
                policy=policy(),
                pending_store=self.pending,
                owner_id=OTHER_PEER,
                owner_dm_id=OWNER_DM,
                peer_id=PEER,
                channel_id=CHANNEL,
            )


class ConfigTest(unittest.TestCase):
    def test_policy_loads_from_environment(self):
        env = {
            "NEMOCLAW_ACTOR_POLICY_ENABLED": "true",
            "NEMOCLAW_OWNER_SLACK_IDS": OWNER,
            "NEMOCLAW_PEER_AGENT_SLACK_IDS": PEER,
            "NEMOCLAW_A2A_CHANNEL_IDS": CHANNEL,
            "NEMOCLAW_LOCAL_BOT_SLACK_ID": LOCAL_BOT,
        }
        loaded = PeerPolicy.from_env(env)
        loaded.validate()
        self.assertEqual(loaded.owner_ids, frozenset({OWNER}))

    def test_disabled_policy_fails_validation(self):
        with self.assertRaises(ContractError):
            PeerPolicy(
                False,
                frozenset({OWNER}),
                frozenset({PEER}),
                frozenset({CHANNEL}),
                LOCAL_BOT,
            ).validate()


if __name__ == "__main__":
    unittest.main()

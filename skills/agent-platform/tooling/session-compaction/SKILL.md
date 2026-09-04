---
name: agent-session-compaction
description: Imported third-party Hermes skill. Read the document and follow its policy-safe workflow.
license: Apache-2.0
---

# Session Compaction Skill — automatic conversation history compression
"""
Triggered by cron or heartbeat.
Checks if the current session has exceeded token threshold,
and if so, summarizes + compresses older messages.
Integrates with OpenClaw's sessions API.
"""

# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# Hermes Nemo Skills

A curated, directly installable Hermes skill bundle for NemoClaw/OpenShell deployments.

## Layout

- `skills/` contains the reviewed Hermes skill directories. Keep this layout when copying into a Hermes skill directory.
- `CATALOG.md` is the organized index of every `SKILL.md` in this repository.
- `scripts/validate-skills.sh` verifies that skill metadata is present before publishing or installation.
- `PENDING_SOURCES.md` records requested sources that were not available on the build host.
- `SOURCE_NOTICES.md` preserves the source and license record for redistributed material.

## Install

Copy the required directory from `skills/` into the agent skill directory, then start a new Hermes session or run the bundle reload command. Deployment-specific credentials and policy configuration belong outside this repository.

## Security

Every skill in this bundle is scanned with [SkillSpector](https://github.com/NVIDIA/skillspector),
NVIDIA's agent-skill vulnerability scanner. CI runs the scan on each pull request
and fails on any new finding.

Run it locally before submitting a change:

```bash
pip install "git+https://github.com/NVIDIA/skillspector.git"
skillspector scan . --no-llm --baseline .skillspector-baseline.yaml
```

- `SECURITY.md` states the trust model these skills are held to and how to report
  a vulnerability.
- `.skillspector-baseline.yaml` records reviewed false positives, each with a
  written justification. Findings in executable files are triaged individually
  rather than suppressed by pattern.

Skills carry no credentials. Each integration names the environment variables it
needs (for example `GITHUB_TOKEN`, `SLACK_BOT_TOKEN`) and reads only those keys;
the operator supplies the values outside this repository.

## Provenance

This repository preserves the source notices and license files shipped with the bundled skills. It is an organized distribution of the reviewed NemoClaw Hermes bundle, not a replacement for upstream projects.

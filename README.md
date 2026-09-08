<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Hermes Nemo Skills

A curated, directly installable Hermes skill bundle for NemoClaw/OpenShell deployments.

## Catalog

[297 active skill directories](CATALOG.md) organized into four top-level groups:

| Group | Skills | Coverage |
| --- | ---: | --- |
| [`skills/agent-platform/`](skills/agent-platform/) | 89 | Hermes, agent collaboration, auto-heal, MCP, agent evaluation, and agent operations |
| [`skills/operations/`](skills/operations/) | 151 | Operator skill tree — `infrastructure/` (Kubernetes, OpenShift including LLM/GPU model serving, SRE, observability), `devops/` (Docker/containers, CI/CD including Argo CD, deployment patterns, cloud DevOps), and `misc/` (trusted-skill installation, Skillspector, shell tooling) |
| [`skills/integrations/`](skills/integrations/) | 13 | Slack, Outlook, GitHub, data-source queries, and cross-source analysis |
| [`skills/workflows/`](skills/workflows/) | 44 | Software development, productivity, creative work, social media, smart home, and gaming |

Each `operations/` category root ships a content-rich `SKILL.md` mapping the
category's subskills — purpose, triggers, key commands, and routing guidance —
so an agent can survey a whole category from one file before loading a specific
subskill. [`CATALOG.md`](CATALOG.md) indexes every skill;
[`skills/CATEGORIES.md`](skills/CATEGORIES.md) is the browsing guide.

## Layout

- `skills/` — the reviewed skill directories. Keep this layout when copying into a Hermes skill directory.
  - `skills/licenses/` — collection-level license files; per-skill `LICENSE` files stay inside their skill directories.
- `CATALOG.md` — organized index of every `SKILL.md` in this repository.
- `SOURCE_NOTICES.md` — source and license record for redistributed material.
- `PENDING_SOURCES.md` — requested sources that were not available on the build host.
- `SECURITY.md` — trust model for the bundle and vulnerability reporting.
- `scripts/validate-skills.sh` — metadata validation gate.
- `.skillspector-baseline.yaml` — reviewed security-scan findings with written justifications.

## Install

Copy the required directory from `skills/` into the agent skill directory, then
start a new Hermes session or run the bundle reload command. The directory layout
is for browsing; Hermes discovers skill commands recursively, and all gateway
authorization rules continue to apply. Deployment-specific credentials and policy
configuration belong outside this repository.

Validate a tree before publishing or installation:

```bash
scripts/validate-skills.sh [skills-root]
```

The script exits non-zero if any `SKILL.md` is missing its Markdown title.

## Security

Every skill in this bundle is scanned with [SkillSpector](https://github.com/NVIDIA/skillspector),
NVIDIA's agent-skill vulnerability scanner. CI (`.github/workflows/skillspector.yml`)
runs the scan on each pull request and fails on any new finding.

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

## Licensing

This repository is licensed under [Apache-2.0](LICENSE); first-party skills are
NVIDIA authorship. Every active skill is MIT- or Apache-2.0-licensed. Skills
derived from upstream projects keep their original licenses, recorded in
[`SOURCE_NOTICES.md`](SOURCE_NOTICES.md) with the collection-level license files
under `skills/licenses/`; non-redistributable or environment-bound material was
removed or replaced with clean-room first-party counterparts.

## Provenance

This repository preserves the source notices and license files shipped with the
bundled skills. It is an organized distribution of the reviewed NemoClaw Hermes
bundle, not a replacement for upstream projects.

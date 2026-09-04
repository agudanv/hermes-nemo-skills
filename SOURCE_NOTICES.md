<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Skill Source Notices

This repository organizes skills by function, not by their source repository.
Original identities do not appear in active skill paths or command names. This
record and the license files in `skills/licenses/` retain the necessary source
and license information for redistributed material.

| Functional location | Source material |
| --- | --- |
| `skills/agent-platform/tooling/` | `sapsapshen/ai-memory-router`, plus miscellaneous community tooling (see removals below) |
| `skills/operations/devops/ci-cd/` | Requested GitOps and delivery sources, including `hermetic-cicd-automation` and the Argo CD materials |
| `skills/operations/devops/` (remainder) | Requested DevOps, automation, and technical-documentation materials, including `flight505-*`, `rohit-toolkit`, and `smartem-devops` |
| `skills/operations/devops/docker/` | `clouddrove/claude-skills` Docker material |
| `skills/operations/infrastructure/kubernetes/` | Requested Kubernetes materials, including `clouddrove-k8s`, `cluster-code`, and related platform guidance |
| `skills/operations/infrastructure/sre/observability/` | Requested observability and monitoring materials |
| `skills/operations/misc/shell/` | Requested shell-scripting and prompt materials |
| `skills/operations/infrastructure/sre/` (remainder) | Original read-only Hermes guidance based on requested layouts that lacked a distributable license |

The license files that accompanied each material set remain with it: bundled
per-skill `LICENSE` files stay inside their functional skill directory, and
collection-level license files are stored under `skills/licenses/` (see the
mapping at the end of this file). The original SRE guidance does not copy
upstream prose, executable code, credentials, or plugin hooks.

All skills remain subject to NemoClaw's gateway policy. A skill does not grant
network, credential, Slack, Outlook, or host-system access.

## Removed material (2026-09-03 license and environment audit)

The following material was removed because its license is not MIT/Apache-2.0
and cannot be relicensed by this repository, or because it cannot execute in
the deployment environment (Linux containers in Kubernetes/OpenShift pods —
no macOS, no Apple hardware, no Homebrew):

| Removed location | Reason |
| --- | --- |
| `operations/infrastructure/kubernetes/cluster-operations/` (9 skills) | © Anthropic PBC — all rights reserved / commercial terms; not redistributable under MIT/Apache. Partially replaced by first-party `cluster-security-audit/` and `gitops-troubleshooting/` |
| `operations/infrastructure/kubernetes/platform-management/` (12 skills) | Custom "Plugin Agent Marketplace — All Rights Reserved" license |
| `operations/infrastructure/kubernetes/operations/` | GPL-2.0 LICENSE; minikube-centric generated index of low value to the OpenShift-based deployment |
| `agent-platform/tooling/powerpoint/` + `workflows/productivity/powerpoint/` | Anthropic-derived proprietary content; SPDX headers on the copy in `workflows/` did not match the content's origin |
| `agent-platform/tooling/{apple-notes,apple-reminders,findmy,imessage}/` | macOS/Apple-hardware bound; impossible inside Linux pods |
| 28 duplicate dirs under `agent-platform/tooling/` | Functional duplicates (0.85–0.99 similarity) of skills that remain in `workflows/` and `integrations/` — violating this file's own duplicate-handling rule; the SPDX-documented `workflows/`/`integrations/` copies were kept |

First-party replacements authored under Apache-2.0 (NVIDIA):
`operations/infrastructure/kubernetes/cluster-security-audit/` and
`operations/infrastructure/kubernetes/gitops-troubleshooting/`. Kubernetes
troubleshooting needs remain covered by the MIT-licensed
`kubernetes/kubernetes-troubleshooting/` and `kubernetes/kubernetes-skill/`.

## Restored Reference Dependencies

On 2026-07-28, every active `SKILL.md` was audited for path-like local
references. Only dependencies that were both missing locally and present at
the corresponding upstream source revision were restored. Runtime examples,
external URLs, and stale paths that do not exist upstream were not imported.

| Functional location | Source revision | Restored dependency types |
| --- | --- | --- |
| `skills/agent-platform/tooling/` | `sapsapshen/ai-memory-router` [`7a38d8e`](https://github.com/sapsapshen/ai-memory-router/tree/7a38d8e7073e61c16eda85681cb32fb68a8657a5) | Referenced scripts and templates |
| `skills/operations/devops/docker/container-fundamentals/` and `skills/operations/infrastructure/kubernetes/fundamentals/` | `clouddrove/claude-skills` [`77a73aa`](https://github.com/clouddrove/claude-skills/tree/77a73aa60287564bd259c72c8940ab42350bc763) | Referenced scripts, Helm examples, Helmfile examples, and license notice |
| `skills/operations/infrastructure/kubernetes/platform-automation/` | `HermeticOrmus/hermetic-academy` [`e9be316`](https://github.com/HermeticOrmus/hermetic-academy/tree/e9be3161c2ce89d1f916fdc66f7a5c29e05cf7d7) | Referenced Helm and manifest assets plus validation script |
| `skills/operations/devops/ci-cd/argocd/` and `skills/operations/infrastructure/sre/observability/{grafana,prometheus}/` | `julianobarbosa/claude-code-skills` [`ac701ad`](https://github.com/julianobarbosa/claude-code-skills/tree/ac701ada10169dc2a7008cb3f8279acdfb3846f5) | Referenced CLI, API, and monitoring helpers plus license notices |
| `skills/operations/infrastructure/kubernetes/failure-analysis/` | `LukasNiessen/kubernetes-skill` [`a34b06a`](https://github.com/LukasNiessen/kubernetes-skill/tree/a34b06ac7df4e372149554af9d107acdef1d91e8) | Referenced Kubernetes failure-analysis guides |

The restored helper scripts are source material, not automatically executed
by a skill. Operators must inspect them and obtain the required approval
before use against a live system.

## Duplicate Handling

Equivalent material is not activated twice. The canonical copies of
`claude-code`, `codex`, `hermes-agent`, `native-mcp`, `opencode`,
`webhook-subscriptions`, and `runbook-creator` remain in their respective
functional categories. As of the 2026-09-03 audit the 28 functional
duplicates that had accumulated under `agent-platform/tooling/` were
deleted; the `workflows/` and `integrations/` copies listed above are the
single active copies.

## Collection-level license files

Collection-level license files (also called *loose licenses*) were moved
from `skills/` into `skills/licenses/` on 2026-09-03. They apply to the
source collections listed here; per-skill licenses are bundled inside each
skill directory.

| File in `skills/licenses/` | License | Applies to |
| --- | --- | --- |
| `autocontext-LICENSE` | Apache-2.0 | agent-platform skills originating from the `autocontext` collection |
| `omnibook-LICENSE` | Apache-2.0 | skills originating from the `omnibook` collection |
| `ecc-LICENSE` | MIT | skills originating from the `ecc` collection |
| `hermes-agent-LICENSE` | MIT | skills originating from the `hermes-agent` collection |
| `hermes-incident-commander-LICENSE` | MIT | the `hermes-incident-commander` material |
| `sre-skills-LICENSE` | MIT | skills originating from the `sre-skills` collection |
| `agentic-awesome-skills-LICENSE-CONTENT` | CC BY 4.0 | documentation of the (now mostly removed) awesome-skills imports under `agent-platform/tooling/` |
| `backup-awesome-skills-LICENSE-CONTENT` | CC BY 4.0 | retained audit-trail copy of the above notice |

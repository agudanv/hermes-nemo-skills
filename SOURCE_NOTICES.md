# Skill Source Notices

This repository organizes skills by function, not by their source repository.
Original identities do not appear in active skill paths or command names. This
record and the included license files retain the necessary source and license
information for redistributed material.

| Functional location | Source material |
| --- | --- |
| `skills/agent-platform/tooling/` | `sapsapshen/ai-memory-router` |
| `skills/operations/ci-cd/` | Requested GitOps and delivery sources, including `hermetic-cicd-automation` and the Argo CD materials |
| `skills/operations/devops/` | Requested DevOps, automation, and technical-documentation materials, including `flight505-*`, `rohit-toolkit`, and `smartem-devops` |
| `skills/operations/docker/` | `clouddrove/claude-skills` Docker material |
| `skills/operations/kubernetes/` | Requested Kubernetes materials, including `clouddrove-k8s`, `cluster-code`, `hermetic-kubernetes-operations`, and related platform guidance |
| `skills/operations/observability/` | Requested observability and monitoring materials |
| `skills/operations/shell/` | Requested shell-scripting and prompt materials |
| `skills/operations/sre/` | Original read-only Hermes guidance based on requested layouts that lacked a distributable license |

The license files that accompanied each material set remain in its functional
collection. The original SRE guidance does not copy upstream prose, executable
code, credentials, or plugin hooks.

All skills remain subject to NemoClaw's gateway policy. A skill does not grant
network, credential, Slack, Outlook, or host-system access.

## Restored Reference Dependencies

On 2026-07-28, every active `SKILL.md` was audited for path-like local
references. Only dependencies that were both missing locally and present at
the corresponding upstream source revision were restored. Runtime examples,
external URLs, and stale paths that do not exist upstream were not imported.

| Functional location | Source revision | Restored dependency types |
| --- | --- | --- |
| `skills/agent-platform/tooling/` | `sapsapshen/ai-memory-router` [`7a38d8e`](https://github.com/sapsapshen/ai-memory-router/tree/7a38d8e7073e61c16eda85681cb32fb68a8657a5) | Referenced scripts and templates |
| `skills/operations/docker/container-fundamentals/` and `skills/operations/kubernetes/fundamentals/` | `clouddrove/claude-skills` [`77a73aa`](https://github.com/clouddrove/claude-skills/tree/77a73aa60287564bd259c72c8940ab42350bc763) | Referenced scripts, Helm examples, Helmfile examples, and license notice |
| `skills/operations/kubernetes/platform-automation/` | `HermeticOrmus/hermetic-academy` [`e9be316`](https://github.com/HermeticOrmus/hermetic-academy/tree/e9be3161c2ce89d1f916fdc66f7a5c29e05cf7d7) | Referenced Helm and manifest assets plus validation script |
| `skills/operations/ci-cd/argocd/` and `skills/operations/observability/{grafana,prometheus}/` | `julianobarbosa/claude-code-skills` [`ac701ad`](https://github.com/julianobarbosa/claude-code-skills/tree/ac701ada10169dc2a7008cb3f8279acdfb3846f5) | Referenced CLI, API, and monitoring helpers plus license notices |
| `skills/operations/kubernetes/failure-analysis/` | `LukasNiessen/kubernetes-skill` [`a34b06a`](https://github.com/LukasNiessen/kubernetes-skill/tree/a34b06ac7df4e372149554af9d107acdef1d91e8) | Referenced Kubernetes failure-analysis guides |

The restored helper scripts are source material, not automatically executed
by a skill. Operators must inspect them and obtain the required approval
before use against a live system.

## Duplicate Handling

Equivalent material was not activated twice. The canonical copies of
`claude-code`, `codex`, `hermes-agent`, `native-mcp`, `opencode`,
`webhook-subscriptions`, and `runbook-creator` remain in their respective
functional categories.

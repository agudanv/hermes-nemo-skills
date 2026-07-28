# Third-Party Skill Provenance

The directories below are copied instruction bundles from the public source
repositories requested by the deployment owner. Each copied bundle retains the
applicable upstream license notice beside the material.

| Category | Bundle | Source |
| --- | --- | --- |
| Kubernetes | `pluginagentmarketplace-kubernetes`, `hippocampus-kubernetes-operations`, `clouddrove-k8s`, `cluster-code`, `hermetic-kubernetes-operations`, `juliano-knative`, `lukas-kubernetes-failure-mode` | Multiple requested Kubernetes sources |
| Docker | `clouddrove-docker` | `clouddrove/claude-skills` |
| Observability | `consult-observability`, `hermetic-observability-monitoring`, `juliano-{grafana,loki,opentelemetry,prometheus}` | Requested observability sources |
| Argo CD / CI/CD | `hermetic-cicd-automation`, `juliano-{argocd,argocd-advanced}` | Requested GitOps and delivery sources |
| DevOps | `flight505-*`, `rohit-toolkit`, `smartem-devops` | Requested DevOps and documentation sources |
| Shell | `hermetic-shell-scripting`, `juliano-shell-prompt` | Requested shell sources |
| Agent platform | `ai-memory-router-hermes` | `sapsapshen/ai-memory-router` |
| SRE | `curated-wrappers` | Original guidance based on the requested unlicensed layouts |

`curated-wrappers` contains original, read-only Hermes guidance based on the
requested source layouts that did not provide a distributable license. It does
not copy their prose, executable code, credentials, or plugin hooks. Imported bundles retain only skill documents, Markdown references, and license notices.

All skills remain subject to NemoClaw's gateway policy. A skill does not grant
network, credential, Slack, Outlook, or host-system access.

## De-duplicated Canonical Skills

The bundle avoids activating equivalent guidance twice. Where an imported
third-party skill overlapped a more complete curated skill, the third-party
copy was omitted and the canonical copy is retained in its functional category:

- `claude-code`, `codex`, `hermes-agent`, `native-mcp`, and `opencode` are in
  `skills/agent-platform/`.
- `webhook-subscriptions` and `runbook-creator` are in `skills/operations/`.

Other third-party skills remain source-namespaced when their content or scope
is meaningfully distinct from the curated collection.

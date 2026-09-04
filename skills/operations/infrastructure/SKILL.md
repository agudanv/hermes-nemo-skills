---
name: infrastructure
description: "Category root for all infrastructure skills in operations/. Load this file first for any Kubernetes, OpenShift, SRE, incident response, observability (Prometheus/Grafana/Loki/OpenTelemetry), LLM/GPU deployment on OpenShift, GitOps, Helm, Terraform, Ansible, Vault, service mesh (Istio/Envoy/Consul/nginx-ingress), or cluster operations question. Each subskill below is summarized with purpose, triggers, key commands, and a pointer to its directory for full detail."
license: Apache-2.0
---

# Infrastructure — Category Skill

Single entry point for the `operations/infrastructure/` skill tree. Read the section for the
domain you need, then load the referenced subskill `SKILL.md` for full detail (progressive
disclosure — this file is the map, not the manual).

Subcategory index files also exist and mirror this structure: `kubernetes/SKILL.md`,
`openshift/SKILL.md`, `sre/SKILL.md`.

---

## 1. Kubernetes (`kubernetes/`)

Index: `kubernetes/SKILL.md` groups these into Fundamentals, Platform Automation,
Troubleshooting & Failure Analysis, Architecture & Patterns, and Security & GitOps
Operations.

### 1.1 Fundamentals

- **`fundamentals/k8s/`** — Core Kubernetes operations, troubleshooting, and platform
  engineering. Triggers: kubectl, pods, deployments, services, ingress, Helm charts, K8s
  manifests, RBAC. Start here for general K8s how-to. Assets: reference docs and scripts.

### 1.2 Platform automation (`kubernetes/platform-automation/`)

Generator-style skills with executable assets:

- **`gitops-workflow/`** — Implement GitOps with ArgoCD and Flux: declarative deployments with
  continuous reconciliation.
- **`helm-chart-scaffolding/`** — Design, organize, and manage Helm charts for templating and
  packaging applications (11 KB + scripts/templates).
- **`k8s-manifest-generator/`** — Create production-ready manifests (Deployments, Services,
  ConfigMaps, Secrets) following best practices and security standards.
- **`k8s-security-policies/`** — Implement NetworkPolicy, PodSecurityPolicy, and RBAC for
  production-grade security.

### 1.3 Failure-mode analysis (KubeShark family)

- **`kubernetes-skill/`** — Failure-mode workflow built on KubeShark: a 7-step process that
  captures cluster context, diagnoses the failure mode, loads the matching reference playbook,
  fixes with risk controls, generates artifacts, validates, and reports under an output
  contract. Prevents hallucinated K8s advice. Failure modes covered: insecure workload
  defaults, resource starvation, network exposure, privilege sprawl, and more — one reference
  playbook per mode in `references/`.
- **`failure-analysis/`** — Condensed sibling of the same family: same failure-mode taxonomy
  (insecure defaults, resource starvation, network exposure, privilege sprawl) in a smaller
  package. Use `kubernetes-skill/` for the full workflow, `failure-analysis/` for quick triage.

### 1.4 Architecture & patterns

- **`kubernetes-architect/`** — Cloud-native infrastructure architecture, advanced GitOps
  (ArgoCD/Flux), enterprise container orchestration design.
- **`kubernetes-deployment/`** — Deployment workflow: container orchestration, Helm charts,
  service mesh, production-ready configurations.
- **`kubernetes-patterns/`** — Workload patterns, resource management, RBAC, probes,
  autoscaling, ConfigMap/Secret handling, kubectl debugging for production deployments.
- **`kubernetes-troubleshooting/`** — Systematic debugging workflows: CrashLoopBackOff,
  OOMKilled, ImagePullBackOff, resource problems, networking.
- **`knative/`** — Knative serverless on Kubernetes: Serving, Eventing, Functions,
  scale-to-zero autoscaling, event-driven architectures, traffic splitting (blue-green).

### 1.5 Security & GitOps operations (first-party)

Two skills authored in-repo for day-2 operations on production clusters:

- **`cluster-security-audit/`** — Read-only security audit workflow with `kubectl`/`oc`:
  privileged-workload census, OpenShift SCC review (`oc adm policy scc-review`), RBAC
  escalation-path analysis, PodSecurity Admission labels, NetworkPolicy coverage, secret
  hygiene, and a severity-ranked findings report. Use for "audit this cluster".
- **`gitops-troubleshooting/`** — GitOps day-2 failures: Argo CD apps stuck OutOfSync or
  Degraded, sync-wave/hook ordering, server-side-apply field-manager conflicts, drift
  triage (external mutation vs mutating controllers vs manager fights), rollback decision
  (git revert vs break-glass `argocd rollback`), Argo Rollouts canary analysis. Pair with
  `platform-automation/gitops-workflow/` (setup) and `kubernetes-troubleshooting/`
  (workload-level failures).

---

## 2. OpenShift (`openshift/`)

Index: `openshift/SKILL.md`.

### 2.1 `openshift-llm-deploy/` — flagship LLM/GPU deployment skill (29 KB, hardened)

Use when: inspecting GPU/model capacity, live GPU utilization, GPU memory, power/temperature
telemetry, model-serving metrics (queue depth, KV-cache usage), or deploying/removing an
LLM via vLLM or NVIDIA Dynamo on OpenShift.

**Cluster access**

- Always use the wrapper binaries `/chart-bin/oc` and `/chart-bin/kubectl` (they carry the
  correct kubeconfig/context). Never pass `--insecure-skip-tls-verify`.

**Status & metrics (read-only paths)**

- `scripts/cluster-status.sh` — cluster status only: scheduled GPU requests plus the
  SANDBOXES / KATA_PODS / NEMOCLAW inventory. This is the answer to "what's on the cluster".
- `scripts/gpu-metrics.sh` — live DCGM telemetry. Consumer labels are
  `exported_namespace` / `exported_pod` / `exported_container` — **never** bare
  `namespace`/`pod` (those collide with kube-state labels).
- `scripts/query-metrics.sh` — arbitrary PromQL via a Thanos port-forward.
- Metrics collection requires the PodMonitors in `templates/` (`dynamo-podmonitor.yaml`,
  `vllm-podmonitor.yaml`) and `enableUserWorkload: true` in cluster monitoring.
- `references/metrics.md` — recipe table mapping each question ("is the GPU busy?", "is the
  queue backing up?") to the exact PromQL.

**Deploying a model**

`scripts/deploy-model.sh` is the **only** allowed deploy command. Flags:

```
--namespace --release --model --platform --node --gpus
--storage-class --pvc-size --memory-request --memory-limit
--hf-secret --max-model-len
--deployment-mode dynamo|standard-vllm [--allow-fallback]
--expose
```

Output markers to parse: `DYNAMO_RESULT`, `FALLBACK_RESULT`, `STANDARD_VLLM_RESULT`,
`DEPLOYMENT_RESULT`, `DIAGNOSIS_CAUSE`, `DIAGNOSIS_ACTION`, `VLLM_IMAGE_SOURCE`, `ENDPOINT`.
HuggingFace tokens are handled by a masked flow; wait for `HF_SECRET_READY:<secret-name>`.

Hard safety rules:

- Never schedule onto a node tainted `node.ocs.openshift.io/storage=true:NoSchedule`.
- When more than one storage class exists, `--storage-class` must be chosen by the user —
  do not guess.
- Verification sequence after deploy: pod health → `/v1/models` → sample completion → forced
  tool-call. `VERIFY_TOOL_CALL=not-observed` is an acceptable outcome, not a failure.

**Removing a model**

`scripts/remove-model.sh` — two-phase by design: run `--action inventory` first, show the
user, then `--action delete --confirm`. `--purge-storage` only after explicit user approval.

**Assets**: `scripts/` (14), `templates/` (6 PodMonitor/deploy templates),
`references/metrics.md`, `dynamo-defaults.yaml`, `SOURCE.md` (provenance).

### 2.2 OpenShift operations

`sre/openshift-operations/` (in the SRE tree) — safely investigate OpenShift cluster, node,
operator, upgrade, and workload problems using **read-only evidence before approved
remediation**. Pair with `kubernetes/kubernetes-troubleshooting/` for pod-level failure
diagnosis and `kubernetes/cluster-security-audit/` to verify security findings.

---

## 3. SRE (`sre/`)

Index: `sre/SKILL.md` groups these into Incident Response, Observability, Runbooks &
Documentation, and Operational Foundations.

### 3.1 Incident response family (6 skills)

| Skill | Use when |
| --- | --- |
| `incident-response/` | Systematic investigation of production incidents: triage, data gathering, impact assessment, root cause analysis |
| `incident-commander/` | Autonomous incident detection, RCA, and self-healing for Linux/Docker production environments (server down, high load, disk full) |
| `incident-responder/` | Hands-on rapid problem resolution with modern observability tooling |
| `incident-response-incident-response/` | Advanced/extended incident-response patterns (deep-dive companion) |
| `incident-response-smart-fix/` | AI-assisted debugging pipeline: observe → hypothesize → fix with observability-platform evidence |
| `incident-runbook-templates/` | Production-ready runbook templates: detection, triage, mitigation, resolution, communication |

Escalation path: `incident-response/` (investigate) → `incident-responder/` (mitigate) →
`incident-commander/` (coordinate/automate) → `incident-runbook-templates/` (institutionalize).

### 3.2 Observability family

Platform skills (`sre/observability/`):

- **`prometheus/`** — Query the Prometheus HTTP API: PromQL execution, targets, alerts.
- **`grafana/`** — Full Grafana HTTP API: dashboards, data sources, folders, alerting,
  annotations, users, teams, organizations.
- **`loki/`** — Grafana Loki log aggregation: deployment, S3/Azure storage backends,
  querying, retention.
- **`opentelemetry/`** — OTEL Collector configuration, Kubernetes deployment,
  traces/metrics/logs pipelines, instrumentation, troubleshooting.
- **`consulting/`** — Observability strategy: maturity assessment, what to instrument and why.

Implementation guides (`sre/observability/implementation/`):

- **`prometheus-configuration/`** — Stand up Prometheus collection/storage for infrastructure
  and applications.
- **`grafana-dashboards/`** — Build production dashboards for system and application metrics.
- **`distributed-tracing/`** — Jaeger and Tempo: trace requests across microservices, find
  bottlenecks.
- **`slo-implementation/`** — Define SLIs/SLOs with error budgets and alerting.

Plus **`sre/observability-setup/`** — bootstrap metrics, logs, and traces into an application
from zero (instrumentation, dashboards, distributed tracing).

### 3.3 Runbooks, readiness, and operations

- **`runbook-creator/`** — Templates and patterns for writing operational runbooks and
  playbooks.
- **`production-readiness/`** — Go-live checklist: reliability, observability, security, and
  operational requirements gates.
- **`sre-operations/`** — Evidence-first SRE workflow: incidents, capacity, logs, on-call
  runbooks, postmortems, reliability engineering.
- **`infrastructure-orchestration/`** — Coordinate infra/platform/SRE/deployment work without
  assuming privileges or making unapproved production changes.

---

## 4. Configuration generator stubs (25 skills)

Auto-activating micro-skills (~2.2 KB each) under `infrastructure/` root, named
`devops-infra-<topic>`. Each follows the same structure (Overview → When to Use →
Instructions → Examples → Prerequisites → Output → Error Handling) and triggers on its topic
name. Use them for quick, conventional configs; for deep work use the full skills above.

| Group | Skills |
| --- | --- |
| Terraform | `terraform-module-creator`, `terraform-provider-config`, `terraform-state-manager` |
| Helm | `helm-chart-generator`, `helm-values-manager` |
| GitOps deploy | `argocd-app-deployer`, `flux-gitops-setup` |
| K8s resources | `kubernetes-configmap-handler`, `kubernetes-deployment-creator`, `kubernetes-ingress-config`, `kubernetes-secrets-manager`, `kubernetes-service-manager` |
| Mesh & ingress | `istio-service-mesh-config`, `envoy-proxy-config`, `consul-service-discovery`, `nginx-ingress-manager` |
| Security | `cert-manager-setup`, `vault-secrets-integrator` |
| Observability | `prometheus-config-generator`, `grafana-dashboard-creator`, `alertmanager-rules-config`, `fluentd-config-generator`, `elasticsearch-index-manager` |
| Ansible | `ansible-playbook-generator`, `ansible-role-creator` |

---

## Routing quick reference

| You need to... | Load |
| --- | --- |
| Debug a pod/workload | `kubernetes/kubernetes-troubleshooting/` → `kubernetes/kubernetes-skill/` (failure modes) |
| Check cluster health | `kubernetes/kubernetes-troubleshooting/` (workloads) → `kubernetes/kubernetes-skill/` (failure-mode playbooks) |
| Audit security / RBAC / SCCs | `kubernetes/cluster-security-audit/` (audit) → `platform-automation/k8s-security-policies/` (author fixes) |
| Fix a stuck or drifting GitOps app | `kubernetes/gitops-troubleshooting/` (setup: `platform-automation/gitops-workflow/`) |
| Upgrade/administer a cluster | `kubernetes/fundamentals/k8s/` + platform GitOps repo |
| Write or validate manifests | `kubernetes/kubernetes-patterns/` or `platform-automation/k8s-manifest-generator/` |
| Set up GitOps | `platform-automation/gitops-workflow/` |
| Harden a cluster | `kubernetes/cluster-security-audit/` (audit) + `platform-automation/k8s-security-policies/` (fix) |
| Deploy an LLM on OpenShift GPUs | `openshift/openshift-llm-deploy/` (only path — never hand-roll) |
| Investigate an OCP problem | `sre/openshift-operations/` (read-only first) |
| Respond to an incident | `sre/incident-response/` → `sre/incident-responder/` → `sre/incident-commander/` |
| Write a runbook | `sre/runbook-creator/` or `sre/incident-runbook-templates/` |
| Stand up metrics/logs/traces | `sre/observability-setup/` then `sre/observability/implementation/*` |
| Query Prometheus/Grafana/Loki APIs | `sre/observability/{prometheus,grafana,loki}/` |
| Define SLOs | `sre/observability/implementation/slo-implementation/` |
| Prepare for go-live | `sre/production-readiness/` |
| Generate a Terraform/Helm/Ansible/etc. config | matching stub in §4 |

# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# Skill Catalog

This index is generated from the reviewed `skills/` tree.

## Top-Level Categories

- `agent-platform/`: Hermes, agent collaboration, auto-heal, MCP, and agent operations.
- `operations/`: DevOps, Kubernetes, Docker, OpenShift, observability, Argo CD/CI-CD, incidents, SRE, and production readiness.
- `integrations/`: Slack, Outlook, GitHub, and cross-source data work.
- `workflows/`: software development, productivity, creative work, social media, smart home, and gaming.
- `third-party/`: reviewed external documentation bundles organized by operations category.

See [`skills/CATEGORIES.md`](skills/CATEGORIES.md) for the browsing guide.

## OpenShift Model Serving

- [`openshift-llm-deploy`](skills/operations/openshift-llm-deploy/SKILL.md): Safely
  discover, deploy, verify, inventory, and remove Hugging Face model-serving
  workloads in a chart-provisioned Hermes/OpenShell sandbox. Prefers a
  supported Dynamo deployment and uses standard vLLM only after an explicit
  Dynamo failure.

## Third-Party Operations Collection

`skills/third-party/` contains 244 additional, source-namespaced skill definitions arranged by function:

- `kubernetes/`: Kubernetes, OpenShift, manifests, Helm, cluster operations, and platform troubleshooting.
- `docker/`: Docker container workflows.
- `observability/`: metrics, logs, traces, Prometheus, Grafana, Loki, and OpenTelemetry.
- `argocd-cicd/`: Argo CD, GitOps, CI/CD, and deployment pipelines.
- `devops/`: general DevOps, delivery, automation, and technical documentation.
- `sre/`: incident response, reliability, and infrastructure coordination.
- `shell/`: shell scripting and shell quality checks.
- `agent-platform/`: Hermes-oriented agent, memory, and workflow guidance.

See [`skills/third-party/PROVENANCE.md`](skills/third-party/PROVENANCE.md) for source mapping and license handling.

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Skill Catalog

This index covers the reviewed `skills/` tree: 297 active skill directories.

## Top-Level Categories

- `agent-platform/`: Hermes, agent collaboration, auto-heal, MCP, and agent operations.
- `operations/`: operator skill tree with three category roots — `infrastructure/` (Kubernetes, OpenShift, Terraform, service mesh, SRE, observability), `devops/` (Docker/containers, CI/CD including Argo CD, deployment patterns, cloud DevOps, technical documentation, Kanban agent workflows), and `misc/` (trusted-skill installation, Skillspector, shell tooling).
- `integrations/`: Slack, Outlook, GitHub, and cross-source data work.
- `workflows/`: software development, productivity, creative work, social media, smart home, and gaming.

See [`skills/CATEGORIES.md`](skills/CATEGORIES.md) for the browsing guide.

## Operations Learning

- [`devops-learning-path`](skills/operations/devops/devops-learning-path/SKILL.md):
  Turn a hands-on DevOps goal into a focused, safe, evidence-based sequence of
  Linux, cloud, Kubernetes, SRE, CI/CD, Git, or DevSecOps practice.

## OpenShift Model Serving

- [`openshift-llm-deploy`](skills/operations/infrastructure/openshift/openshift-llm-deploy/SKILL.md): Safely
  discover, deploy, verify, inventory, and remove Hugging Face model-serving
  workloads in a chart-provisioned Hermes/OpenShell sandbox. Prefers a
  supported Dynamo deployment and uses standard vLLM only after an explicit
  Dynamo failure.

## Functional Skill Collections

The active skill directories are organized beside canonical skills:

- `skills/agent-platform/tooling/`: agent extensions, memory, model, and workflow guidance.
- `skills/operations/devops/ci-cd/`: Argo CD, GitOps, secrets, and delivery pipelines.
- `skills/operations/devops/` (remainder): infrastructure automation, foundations, documentation, and general DevOps practice.
- `skills/operations/devops/docker/`: container fundamentals and Docker workflows.
- `skills/operations/infrastructure/kubernetes/`: Kubernetes fundamentals, platform automation, failure analysis, gitops, manifests, security, networking, and the first-party `cluster-security-audit`/`gitops-troubleshooting`/`kubernetes-architect`/`kubernetes-deployment` replacements.
- `skills/operations/infrastructure/sre/`: reliability and infrastructure coordination, including the observability stack (metrics, logs, traces, Grafana, Loki, OpenTelemetry, Prometheus, SLOs).
- `skills/operations/infrastructure/` (remainder): Terraform, Helm, Ansible, service mesh, Vault, and adjacent platform tooling.
- `skills/operations/misc/shell/`: shell quality checks, defensive scripting, and prompt configuration.

See [`SOURCE_NOTICES.md`](SOURCE_NOTICES.md) for source and license handling.

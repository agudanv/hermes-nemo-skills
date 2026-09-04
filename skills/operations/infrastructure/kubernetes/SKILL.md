---
name: kubernetes-infrastructure-index
description: "Index of Kubernetes skills under operations/infrastructure/kubernetes/: fundamentals, platform automation, failure-mode analysis, troubleshooting, architecture and patterns, and first-party security/GitOps operational skills."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Kubernetes Skills Consolidated

Unified Kubernetes skill category covering fundamentals, platform automation,
troubleshooting and failure analysis, security and GitOps operations, and
advanced patterns.

## Sub-Skills

### Fundamentals
- **fundamentals/k8s** — Core concepts: pods, services, deployments, RBAC, networking

### Platform Automation
- **platform-automation/k8s-manifest-generator** — Manifest templating
- **platform-automation/k8s-security-policies** — NetworkPolicy/PSS/RBAC authoring
- **platform-automation/gitops-workflow** — ArgoCD/Flux patterns
- **platform-automation/helm-chart-scaffolding** — Chart development

### Failure Analysis
- **kubernetes-skill** — 7-step failure-mode workflow with reference playbooks
- **failure-analysis** — Condensed failure-mode triage

### Troubleshooting
- **kubernetes-troubleshooting** — Systematic failure analysis methodology

### Security & GitOps Operations (first-party)
- **cluster-security-audit** — Live-cluster security audit with kubectl/oc (SCCs, RBAC escalation paths, NetworkPolicy coverage, secret hygiene)
- **gitops-troubleshooting** — Argo CD day-2 failures: sync waves, drift, server-side-apply conflicts, rollback

### Advanced Patterns
- **kubernetes-patterns** — Operators, controllers, CRDs, admission webhooks
- **kubernetes-deployment** — Advanced deployment patterns
- **kubernetes-architect** — Cluster architecture design, HA, topology
- **knative** — Serverless on K8s: Serving, Eventing, Functions

## Usage

```bash
# Load entire Kubernetes category
skill load kubernetes

# Load specific sub-skill
skill load kubernetes.kubernetes-troubleshooting
skill load kubernetes.cluster-security-audit
skill load kubernetes.gitops-troubleshooting
skill load kubernetes.kubernetes-patterns
```

## Agent Compatibility

Works with Hermes, Codex, Cursor, and any agent supporting the skill protocol. Sub-skills declare their own `whenToUse` triggers for automatic routing.

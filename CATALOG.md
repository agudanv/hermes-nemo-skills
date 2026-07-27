# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# Skill Catalog

This index is generated from the reviewed `skills/` tree.

## OpenShift Model Serving

- [`openshift-llm-deploy`](skills/openshift-llm-deploy/SKILL.md): Safely
  discover, deploy, verify, inventory, and remove Hugging Face model-serving
  workloads in a chart-provisioned Hermes/OpenShell sandbox. Prefers a
  supported Dynamo deployment and uses standard vLLM only after an explicit
  Dynamo failure.

## Third-Party Operations Collection

`skills/third-party/` contains 251 additional, source-namespaced skill definitions arranged by function:

- `kubernetes/`: Kubernetes, OpenShift, manifests, Helm, cluster operations, and platform troubleshooting.
- `docker/`: Docker container workflows.
- `observability/`: metrics, logs, traces, Prometheus, Grafana, Loki, and OpenTelemetry.
- `argocd-cicd/`: Argo CD, GitOps, CI/CD, and deployment pipelines.
- `devops/`: general DevOps, delivery, automation, and technical documentation.
- `sre/`: incident response, reliability, and infrastructure coordination.
- `shell/`: shell scripting and shell quality checks.
- `agent-platform/`: Hermes-oriented agent, memory, and workflow guidance.

See [`skills/third-party/PROVENANCE.md`](skills/third-party/PROVENANCE.md) for source mapping and license handling.

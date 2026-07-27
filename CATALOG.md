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

`skills/third-party/` contains 251 additional, source-namespaced skill definitions. The namespaced layout keeps equally named upstream skills discoverable without silently replacing one another.

- `pluginagentmarketplace-kubernetes`, `hippocampus-kubernetes-operations`, `clouddrove-k8s`, `cluster-code`, and `lukas-kubernetes-failure-mode` cover Kubernetes, cluster lifecycle, GitOps, security, and troubleshooting.
- `clouddrove-docker`, `smartem-devops`, and `flight505-devops-*` cover Docker, DevOps fundamentals, advanced platform operations, and technical docs.
- `consult-observability`, `hermetic-observability-monitoring`, and `juliano-{opentelemetry,grafana,loki,prometheus}` cover telemetry and observability operations.
- `hermetic-cicd-automation`, `juliano-{argocd,argocd-advanced,knative}`, and `rohit-toolkit` cover CI/CD, GitOps, delivery, Python, and orchestration.
- `ai-memory-router-hermes` is the requested Hermes-oriented collection.
- `curated-wrappers` provides original, policy-safe guidance for the requested SRE, OpenShift, and infrastructure-orchestration references that lacked a distributable license.

See [`skills/third-party/PROVENANCE.md`](skills/third-party/PROVENANCE.md) for source mapping and license handling.

---
name: openshift-infrastructure-index
description: "Index of OpenShift skills under operations/infrastructure/openshift/: LLM/GPU model deployment via openshift-llm-deploy and OpenShift-specific operations."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# OpenShift Skills Consolidated

Unified OpenShift skill category for LLM model deployment, cluster operations, and platform-specific patterns.

## Sub-Skills

### LLM Model Deployment
- **openshift-llm-deploy** — Complete LLM deployment on OpenShift
  - **Templates:**
    - `dynamo-vllm-graph-deployment.yaml` — NVIDIA Dynamo + vLLM GraphDeployment
    - `dynamo-tensorrtllm-graph-deployment.yaml` — Dynamo + TensorRT-LLM
    - `vllm-deployment.yaml` — Standard vLLM deployment
    - `model-download-job.yaml` — Model download/init container
    - `dynamo-podmonitor.yaml` — Prometheus PodMonitor for metrics
  - **Scripts:**
    - `deploy-model.sh` — End-to-end model deployment
    - `dynamo-first-deploy.sh` — First-time Dynamo setup
    - `diagnose-deployment.sh` — Deployment troubleshooting
    - `verify-openai-endpoint.sh` — OpenAI API compatibility check
    - `resolve-vllm-image.sh` / `resolve-dynamo-image.sh` — Image resolution
    - `list-storage-classes.sh` — Storage class discovery
    - `gpu-metrics.sh` / `query-metrics.sh` — GPU/utilization metrics
    - `remove-model.sh` — Cleanup
    - `cluster-status.sh` — Cluster health overview

### Cluster Operations
- **openshift-operations** — OpenShift-specific operations (moved from SRE foundations)

## Usage

```bash
# Load entire OpenShift category
skill load openshift

# Load LLM deployment skill
skill load openshift.openshift-llm-deploy

# Run deployment script directly
./files/skills/infrastructure/openshift/openshift-llm-deploy/scripts/deploy-model.sh \
  --model glm-5.3-fp8 \
  --namespace runai-inference \
  --platform b200 \
  --gpus 1
```

## Key Features

- **NVIDIA Dynamo Integration** — Native GraphDeployment CR support
- **Multi-backend** — vLLM, TensorRT-LLM, llama.cpp
- **GPU Awareness** — Node selection, resource quotas, MIG support
- **Observability Built-in** — PodMonitor, GPU metrics, OpenAI endpoint verification
- **Storage Flexibility** — Ceph RBD, NVMe, PVC templates

## Agent Compatibility

Works with Hermes, Codex, Cursor, and any agent supporting the skill protocol. The `openshift-llm-deploy` skill declares `whenToUse` triggers for LLM deployment intents.

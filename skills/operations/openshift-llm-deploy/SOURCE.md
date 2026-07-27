# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# Source and Runtime Prerequisites

This directory was imported without behavioral changes from:

- Repository: `ssh://git@gitlab-master.nvidia.com:12051/aguda/openshell-hermes.git`
- Commit: `f0b83f5b48b9a0a2b13cdd50b810b574966d5642`
- Path: `charts/hermes-webui-openshell/files/skills/openshift-llm-deploy`

## Intended Environment

This is a Hermes/OpenShell chart skill, not a generic standalone Kubernetes
deployment recipe. It requires a `hermes-webui-openshell` installation that
provides the following runtime integration:

- `/chart-bin/oc` and `/chart-bin/kubectl` wrappers with a projected local
  service-account token.
- `${HERMES_HOME}/skills/operations/openshift-llm-deploy/dynamo-defaults.yaml`, rendered
  from the chart's values.
- `${HERMES_HOME}/skills/operations/openshift-llm-deploy/hf-token-intake.yaml`, rendered
  from the chart's Hugging Face token-intake settings when that flow is enabled.
- The `llm-runner` ServiceAccount and the RBAC, Secret lifecycle, and runtime
  resources described by the chart.

Copying this directory into a different agent environment does not provision
those dependencies. Keep the source chart and this imported skill aligned when
the deployment contract changes.

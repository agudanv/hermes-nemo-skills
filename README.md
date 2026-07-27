# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
# Hermes Nemo Skills

A curated, directly installable Hermes skill bundle for NemoClaw/OpenShell deployments.

## Layout

- `skills/` contains the reviewed Hermes skill directories. Keep this layout when copying into a Hermes skill directory.
- `CATALOG.md` is the organized index of every `SKILL.md` in this repository.
- `scripts/validate-skills.sh` verifies that skill metadata is present before publishing or installation.
- `PENDING_SOURCES.md` records requested sources that were not available on the build host.

## Install

Copy the required directory from `skills/` into the agent skill directory, then start a new Hermes session or run the bundle reload command. Deployment-specific credentials and policy configuration belong outside this repository.

## Provenance

This repository preserves the source notices and license files shipped with the bundled skills. It is an organized distribution of the reviewed NemoClaw Hermes bundle, not a replacement for upstream projects.

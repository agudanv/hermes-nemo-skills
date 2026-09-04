---
name: sre-infrastructure-index
description: "Index of SRE skills under operations/infrastructure/sre/: incident response family, observability stack, runbooks, production readiness, and operational foundations."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# SRE Skills Consolidated

Unified Site Reliability Engineering skill category covering incident response, observability, runbooks, production readiness, and operational foundations.

## Sub-Skills

### Incident Response
- **incident-commander** — Incident command structure, roles, communication
- **incident-responder** — Hands-on response procedures, mitigation playbooks
- **incident-response** — Core incident lifecycle: detection → resolution → postmortem
- **incident-response-incident-response** — Advanced incident patterns
- **incident-response-smart-fix** — Automated remediation, self-healing
- **incident-runbook-templates** — Runbook templates, standardization

### Observability
- **observability** — Full observability stack
  - **observability/prometheus** — Metrics collection, rules, alerting
  - **observability/grafana** — Dashboards, visualization, alerting UI
  - **observability/loki** — Log aggregation, querying, retention
  - **observability/opentelemetry** — Distributed tracing, instrumentation
  - **observability/consulting** — Observability strategy, maturity model
  - **observability/implementation** — Rollout patterns, migration
- **observability-setup** — Bootstrap observability stack from scratch

### Runbooks & Documentation
- **runbook-creator** — Runbook authoring, maintenance, automation
- **production-readiness** — Production readiness reviews, checklists, gates

### Operational Foundations
- **sre-operations** — SRE practices: SLO/SLI, error budgets, toil reduction
- **infrastructure-orchestration** — Infrastructure as code, GitOps, drift detection

## Usage

```bash
# Load entire SRE category
skill load sre

# Load specific sub-skill
skill load sre.incident-commander
skill load sre.observability.prometheus
skill load sre.runbook-creator
skill load sre.production-readiness
```

## Incident Response Flow

```
Detection → Triage → Mitigation → Resolution → Postmortem
   │           │          │           │           │
   ▼           ▼          ▼           ▼           ▼
incident-  incident-  incident-  incident-  runbook-
commander  responder  response   response   creator
   │           │          │           │           │
   └───────────┴──────────┴───────────┴───────────┘
                    │
                    ▼
            observability stack
            (prometheus, loki, tempo, grafana)
```

## Agent Compatibility

Works with Hermes, Codex, Cursor, and any agent supporting the skill protocol. Sub-skills declare their own `whenToUse` triggers for automatic routing (e.g., "incident", "outage", "alert firing", "SLO breach").

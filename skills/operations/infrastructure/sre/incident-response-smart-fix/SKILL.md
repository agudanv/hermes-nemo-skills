---
name: incident-response-smart-fix
description: "Hypothesis-driven remediation pipeline for live incidents: capture a baseline, observe evidence across metrics, logs, and traces, form falsifiable root-cause hypotheses, run minimum-blast-radius experiments, and verify every fix against the baseline before fleet rollout on Kubernetes/OpenShift. Use when the user asks for automated debugging, self-healing, a root-cause pipeline, hypothesis-driven remediation, or evidence-backed fixes instead of guess-and-restart patching."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Incident Response: Smart Fix

## Purpose

Evidence-driven remediation loop for an agent operating against live Kubernetes/OpenShift systems. The skill converts an unexplained symptom into a verified fix through four disciplined stages: observe, hypothesize, experiment, verify. Every hypothesis must be falsifiable, every experiment must be smaller than its guardrail, and every fix must beat a baseline captured before any change was made.

## When to Use

- A system is degraded (error rate, latency tail, crash loops, OOMKills) and the cause is unknown or contested.
- A recent change (deploy, config edit, scaling or node event) is suspected but unproven.
- Multiple plausible causes must be discriminated cheaply before committing to one.
- The user wants automated debugging, self-healing, a root-cause pipeline, or hypothesis-driven remediation with guardrails.

Hand-off points:

- Impact is customer-visible and growing; mitigation now matters more than root cause -> `incident-responder`.
- A full incident framework, severity levels, and role assignments are needed -> `incident-response`.
- Incident is contained and deep causal analysis is next -> `failure-analysis`.
- The verified fix should be persisted as an executable runbook -> `runbook-creator`.

## Core Loop

The loop exits only through VERIFIED (fix held through its watch window) or ESCALATE (impact exceeded a guardrail). A fix applied without a captured baseline is an incident amplifier, not a fix.

```text
        +----------+
        |          |   wrong outcome: rollback, refine hypothesis
        v          |
     OBSERVE       |
        |          |
        v          |
  HYPOTHESIZE <----+   statement + prediction:
        |              "if H is true, metric M must show W by time T"
        |              not falsifiable -> rewrite before testing
        v
   EXPERIMENT        one change only, minimum blast radius,
        |            rollback armed before apply
        v
     VERIFY          hold through watch window, watch adjacent metrics
        |
        +-- stable, no adjacent regressions -> DONE: promote fix, write runbook
        +-- watch-window breach or regression -> ESCALATE to `incident-responder`
```

Stage discipline:

- **Observe.** Snapshot the baseline before touching anything. Quantify the symptom: magnitude, start time, affected population. List every change event in the window. Distinguish what changed from what is merely coincident in time.
- **Hypothesize.** One cause per hypothesis, stated as `H: <cause> produces <effect>`. Attach a prediction that evidence can falsify: a metric, log pattern, or trace shape that must (or must not) appear. No prediction, no test.
- **Experiment.** Change exactly one variable. Choose the smallest arena that yields signal (staging namespace, one canary pod, one cordoned node). Precompute and re-verify the rollback command before applying.
- **Verify.** Compare against the baseline with numeric acceptance criteria. Watch the adjacents: the metrics you did not set out to improve. Hold the fix through a watch window scaled to incident severity before fleet promotion.

## Evidence Sources

| Signal | Source | Skill |
| --- | --- | --- |
| Counters, gauges, histograms, SLOs | Prometheus | `observability/prometheus` |
| Error bursts, stack traces, log patterns | Loki | `observability/loki` |
| Distributed latency attribution, spans | OpenTelemetry | `observability/opentelemetry` |
| Dashboard context, historical baselines | Grafana | `observability/grafana` |

Query patterns per signal class (metric spikes, log error bursts, p99 tails, crash loops, OOMKills) are in `resources/implementation-playbook.md`, with hypothesis templates, experiment design, and the pitfall catalog.

## Guardrails

1. **No fix without a captured baseline.** Queries and outputs are saved to the incident log before the first mutation. Without a before, there is no after.
2. **Staging first** when a staging environment exists; production experiments must take the canary path.
3. **Canary before fleet.** Ramp 1 pod -> 10% -> 50% -> 100% of service capacity, holding each step for at least two complete SLO evaluation windows. Never jump straight to fleet.
4. **Rollback plan is mandatory and armed.** Exact revert commands written, reviewed, and executable by a second party before the experiment applies.
5. **Blast-radius budget.** Exceeding any budget escalates rather than improvising.

| Change class | First arena | Max blast radius without escalation |
| --- | --- | --- |
| Code hotfix | staging, then canary pod | 10% of service traffic |
| Config or env var change | staging or one labeled pod | one deployment |
| Resource limit change | canary pod | one deployment |
| Node-level (daemonset, kernel) | one cordoned node | one node |
| Cluster-wide (RBAC, admission, mesh) | never experiment in-band | requires `incident-responder` |

Beyond the budget table: **irreversible or customer-facing mutations require explicit human approval** at the point of risk. The loop stops and asks.

## Escalate to `incident-responder` When

- Customer-facing impact grows while the loop is still in OBSERVE or HYPOTHESIZE.
- Two full loop iterations produce no discriminating evidence.
- Rollback was executed and the system is still degraded: the change was not the cause, or not the only cause.
- The candidate fix requires a blast radius beyond the budget table above.
- The incident meets SEV1/SEV2 criteria; mitigation takes priority over root cause.

## Artifacts

Two records travel with every smart-fix loop; templates, queries, and a worked example are in `resources/implementation-playbook.md`:

- **Hypothesis register** -- every hypothesis, its prediction, and its falsifying observation, including the rejected ones.
- **Experiment record** -- change applied, arena, rollback command, predicted versus observed outcome, and promotion decision.

## Cross-References

- `incident-response` -- overall incident workflow and severity framework
- `incident-responder` -- mitigation-first operations during an active incident
- `failure-analysis` -- deep causal analysis after containment
- `runbook-creator` -- persist the verified fix as an executable runbook
- `observability` -- evidence collection (prometheus, grafana, loki, opentelemetry sub-guides)
- `kubernetes-troubleshooting` -- platform-level triage when the cause is the cluster, not the workload
- `production-readiness` -- post-fix readiness review of the change

---
name: incident-response-incident-response
description: "Deep-dive reference for running the full incident lifecycle on major incidents: detection, triage, mitigation, resolution, and blameless postmortem, plus incident command structure (Incident Commander, Operations, Communications, Scribe), severity classification matrices, customer impact assessment with error-budget burn math, and communication templates with cadence rules. Use when managing a major incident end to end, running incident command for SEV1/SEV2 events, performing customer impact assessment, writing a postmortem, or when asked about incident lifecycle phases, severity re-classification, executive updates, or customer-facing notices."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Incident Response: Extended Lifecycle Deep Dive

Extended playbook for major incidents (SEV1/SEV2), companion to the core `incident-response` skill: command structure, impact math, managed communications, rigorous postmortems.

## When to Use This Skill

| Skill | Scope | Reach for it when |
| --- | --- | --- |
| `incident-response` | Core lifecycle | Any incident; standard detect-fix-review flow |
| `incident-responder` | Hands-on mitigation | Running rollbacks, kubectl, failovers yourself |
| `incident-commander` | Coordination and automation | Running the bridge, delegating, automating status updates |
| This skill | Extended deep dive | SEV1/SEV2 lifecycle gates, impact math, comms templates, postmortem discipline |

Supporting skills: `incident-runbook-templates` (runbooks used in mitigation), `incident-response-smart-fix` (assisted remediation), `observability` (detection signals), `failure-analysis` (Kubernetes forensics), `production-readiness` (pre-incident readiness), `sre-operations` (error budgets and steady state).

## Incident Lifecycle Playbook

Five phases with explicit entry and exit criteria. Do not skip gates under pressure; log every transition in the incident timeline.

### Phase 1: Detect

Signals, most reliable first: alerting rules (Prometheus/Alertmanager per `observability`), synthetic probes, support tickets, anomaly detection, human reports.

Actions:

1. Acknowledge the alert; silence it only after acknowledgment.
2. Open an incident record with a tracking ID (for example `INC-20260903-014`).
3. Record the impact start time, not the alert time; the gap is your detection gap.
4. Make an initial severity guess; refine it in triage.

Entry criteria: a sustained alert breach (not a flap), or a credible human report.
Exit criteria: incident record open, responder engaged, triage started. Suspected SEV1: within 5 minutes.

### Phase 2: Triage

Goal: answer what is broken, who is affected, how bad.

Actions:

1. Establish blast radius: single pod, node, zone, region, or global.
2. Correlate with change: deploys, config, certificate rotations, and dependency releases in the last 24 hours; most incidents are change-induced.
3. Classify severity using the matrix below.
4. For SEV1/SEV2: page an Incident Commander, open the incident channel and bridge.
5. Form a mitigation hypothesis; write it down even if uncertain.

Entry criteria: detection confirmed.
Exit criteria: severity assigned, IC named for SEV1/SEV2, mitigation hypothesis recorded.

### Phase 3: Mitigate

Goal: stop customer impact by the fastest safe path. Mitigation is not root-cause repair.

Preference order: roll back the suspect change > fail over to healthy capacity > scale out > feature-flag disable > hotfix. Prefer reversible actions; log every action with a timestamp.

Entry criteria: severity assigned and hypothesis formed.
Exit criteria: customer impact stopped or reduced below the severity threshold, verified by external signals (synthetics, customer-visible metrics), not just internal dashboards. Then hold a stability window: 30 minutes for SEV1, 15 for SEV2.

### Phase 4: Resolve

Goal: confirm root cause and land a permanent fix.

Actions:

1. Root-cause analysis: 5-whys, change diffing; use `failure-analysis` for Kubernetes-layer forensics.
2. Permanent fix with regression coverage. A rollback left in place is a mitigation, not a resolution.
3. Verify error-budget burn has returned to baseline.

Entry criteria: mitigation holding through the stability window.
Exit criteria: root cause identified (or explicitly documented as unknown, with a detection-gap action item), permanent fix deployed, steady state confirmed.

### Phase 5: Review

Goal: learn, and feed fixes back into the system.

Actions: postmortem within 48 hours for SEV1 (72 max for SEV2); action items filed with owners and deadlines; track to closure.

Entry criteria: incident resolved.
Exit criteria: postmortem published, action items ticketed, follow-up review scheduled.

## Incident Command Structure

Formal roles for SEV1/SEV2. One person may hold multiple roles, but never combine IC and hands-on operations during a SEV1.

| Role | Owns | Does not |
| --- | --- | --- |
| Incident Commander (IC) | Severity, priorities, escalation, go/no-go on risky actions | Hands-on debugging |
| Operations Lead | Technical execution; directs responders | External communication |
| Communications Lead | Status page, internal updates, executive and customer messaging; fields inbound questions | Technical decisions |
| Scribe | Timeline log: timestamps, decisions, actions, hypothesis changes | Investigation |

Small teams: two people = IC+Communications, Operations+Scribe. Solo: drop Scribe first (keep rough notes), then Communications (broadcast-only); split IC/Operations only at SEV3 or lower.

### Handoff Protocol (incidents over 4 hours or crossing timezones)

1. Outgoing IC writes a handoff brief: current severity, active mitigations, open hypotheses, next three actions, pending communications.
2. Fifteen-minute overlap call; walk the Scribe's timeline together.
3. Incoming IC announces takeover in the incident channel: "I am IC as of 08:00 UTC."
4. Update the incident record owner. The outgoing IC stays reachable for 30 minutes.
5. Never hand off mid-action; complete or abort in-flight changes first.

## Severity Classification

| Severity | Customer impact | Data loss risk | SLA exposure | Revenue at risk | Response |
| --- | --- | --- | --- | --- | --- |
| SEV1 | >50% of users, or all of a tier; core function down | Active or unrecoverable | Breach active or imminent | >$100k/hour or contractual penalty | All hands; 15-min comms; exec notice within 1 hour |
| SEV2 | 10-50% of users; major degradation | Potential, recoverable | Burn rate >10x | $10k-100k/hour | Dedicated team; 30-min comms; exec notice within 4 hours |
| SEV3 | <10% of users; workaround exists | None | Burn rate 2-10x | <$10k/hour | Business hours; daily update |
| SEV4 | Internal only; cosmetic | None | Negligible | None | Backlog; fix-forward |

Classify on the worst dimension that applies; do not average across dimensions.

### Re-classification Triggers

Upgrade when: scope grows to new regions or segments; duration exceeds 2x the initial estimate; data loss is newly discovered; security involvement is identified; executive or major customer escalation.

Downgrade when: mitigation holds through the stability window; affected traffic falls below the next threshold; impact re-scopes to workaround-available.

Rules: any responder may propose; only the IC decides. Announce re-classification with the reason, exactly as the initial severity was announced. Never silently downgrade.

## Customer-Impact Assessment

### Affected-Segment Estimation

Compute from traffic data, not guesses:

1. Baseline: requests per minute per segment (region, tier, product surface) from the same hour over the last 7 days.
2. Affected segment: error rate >5% or p99 latency >3x baseline, sustained for 5 minutes.
3. Report as: "2 of 6 regions, approximately 22% of weekly active users, approximately 18% of request volume."

### Failed-Transaction Accounting

```text
failed_tx = baseline_rpm x duration_min x (observed_error_rate - baseline_error_rate)
```

Count user-visible failures separately from internal retries that eventually succeeded; retries inflate system error counts, not customer harm. For revenue exposure, multiply failed transactions by the segment's average transaction value.

### Error-Budget Burn Math

A 99.9% SLO over 30 days yields a 0.1% error budget: 43.2 minutes of full-outage equivalent, or the corresponding failed-request count.

```text
burn_rate = observed_error_ratio / budget_ratio
```

Burn rate 1 consumes the budget exactly at month end. Page on fast burn (~14x over 1 hour); ticket on slow burn (~2x over 3 days).

Worked example:

- Service SLO: 99.9%; traffic: 2.0M requests/day (60M per 30-day month).
- Budget: 0.001 x 60,000,000 = 60,000 failed requests per month.
- Incident: 45 minutes; affected region carries 40% of traffic; 85% error rate there.
- Requests in window: 2,000,000 / 1440 x 45 = 62,500 total; affected: 62,500 x 0.40 = 25,000.
- Failed: 25,000 x 0.85 = 21,250.
- Budget consumed: 21,250 / 60,000 = 35.4% of the monthly budget in 45 minutes.
- Burn rate: global error ratio in the window is 21,250 / 62,500 = 0.34 vs. budgeted 0.001, so 340x.
- Projection: at this rate the full budget exhausts in about 127 minutes. This is a paging incident, not a ticket.

## Communication

Cadence rules:

| Severity | Internal channel | Status page | Executive | Customer-facing |
| --- | --- | --- | --- | --- |
| SEV1 | Every 15 min | Every 30 min | Within 1 hour, then hourly | Within 30 min of confirmation |
| SEV2 | Every 30 min | Hourly | Within 4 hours | Within 2 hours |
| SEV3 | Daily | On resolution | Weekly digest | On request |
| SEV4 | On resolution | None | None | None |

Always hit the promised cadence, even if the update is "no change" -- silence reads as loss of control. State what you know, what you do not, and when the next update arrives. Never speculate externally on root cause; never name individuals or vendors.

### Internal Status Template

```text
[INC-20260903-014] SEV2 - Payments API elevated errors
Status: Mitigating
Impact: ~18% of checkout requests failing in us-east; other regions normal
Started: 14:02 UTC | Detected: 14:06 UTC | IC: j.smith
Current action: rolling back release 1.42.7 (suspected cause)
Next update: 15:00 UTC or on material change
```

### Executive Update Template

```text
Subject: SEV2 - Payments API - impact contained, resolution in progress
What happened: Release 1.42.7 introduced a connection-pool regression at 14:02 UTC.
Customer impact: ~4,200 customers; est. 21,250 failed transactions; ~$48k revenue at risk.
Current state: Rollback 80% complete; error rate falling.
Next steps: Complete rollback, verify, root-cause analysis, postmortem within 48 hours.
ETA to resolution: 16:00 UTC | Next update: 15:30 UTC
Business risk: SLA credit exposure est. $12k; no renewal-risk accounts affected.
```

### Customer-Facing Notice Template

```text
Title: Elevated error rates on Payments API (US East)
We are investigating elevated error rates affecting payment processing in the US East
region since 14:02 UTC. Affected customers may see failed checkout attempts. No data
has been lost. A fix is being deployed now. Next update by 15:30 UTC.
```

Reference the status page and incident channel via environment variables (for example `STATUS_PAGE_URL`, `INCIDENT_CHANNEL`); never hardcode URLs in templates.

## Postmortem

Blameless structure, in this order:

1. Summary: three sentences -- what happened, the quantified impact, how it was resolved.
2. Impact: users and segments affected, failed transactions, budget burned, SLA credits (from the assessment above).
3. Timeline: UTC timestamps from the Scribe log; include detection gap (impact start to detection) and time to mitigate.
4. Root cause and contributing factors: the technical cause plus process and environment factors that enabled it. Never stop at "human error"; ask why the system allowed the action.
5. What went well: detection speed, rollback automation, communication discipline.
6. What went poorly: gaps, delays, lucky escapes.
7. Action items: table with ID, action, type (prevent / detect / mitigate / process), owner (a named individual, never a team), deadline, and priority.
8. Where we got lucky: near-misses that did not produce impact this time.

### Follow-Up Tracking Discipline

- File every action item as a ticket before the postmortem is published; link each from the document.
- Suggested deadlines: detection improvements 14 days, prevention 30 days, documentation 7 days.
- Review open items weekly until closed; escalate items slipping more than two weeks.
- Track recurrence: the same root-cause class within 90 days is an action-item process failure; re-open the review.
- Feed MTTD, MTTR, and recurrence metrics back into `sre-operations` reliability reviews.

---
name: incident-responder
description: "Hands-on rapid incident response and mitigation for Kubernetes and cloud services: severity triage (P0-P3), a first-15-minutes checklist, a choose-one mitigation playbook (rollback, scale out, circuit-break, traffic shift, restart with cause capture), evidence capture for postmortems, and status communication cadence. Use when production is down, you suspect an outage, you need to mitigate an incident fast, during rapid response to alerts, or when investigating service degradation."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Incident Responder

Operational playbook for the mitigation phase of an incident: restore service first, understand root cause second, preserve evidence throughout. Commands assume `kubectl` against the affected cluster.

Escalation chain across sibling skills: investigate with `incident-response` -> mitigate with `incident-responder` (this skill) -> coordinate with `incident-commander` -> institutionalize with `incident-runbook-templates` / `runbook-creator`.

## Severity Triage Matrix

Classify before acting: severity drives response time, cadence, and who gets paged. When in doubt, take the higher severity; downgrading is cheap, late escalation is not.

| Severity | User impact | Scope | Examples | Response expectation |
| ---------- | ------------- | ------- | ---------- | ---------------------- |
| P0 | Total outage or data loss; no workaround | All or most users, or a contractual-availability customer | Cluster-wide outage; database unreachable; data corruption in progress; security breach | Page immediately; all hands; mitigation starts within 5 min; execs notified within 30 min |
| P1 | Major function degraded; painful workaround or none | Significant subset of users or one critical journey | Checkout errors at 20%; p99 latency 10x SLO; one region down | Page on-call; mitigation starts within 15 min; updates every 30 min |
| P2 | Degraded experience; workaround exists | Limited subset, or internal users only | One replica failing behind a healthy pool; stalled batch job; low-traffic 5xx | Acknowledge in business hours; mitigate within 4 h; updates every 2 h |
| P3 | Minor or cosmetic; no user-visible impact | Single component, easily routed around | Stale dashboard panel; idle canary crashlooping; disk at 70% with slow growth | Ticket, not a page; fix within the sprint |

Triage in order: users affected? -> fraction of traffic or tenants? -> self-worsening? -> workaround or failover?

## First 15 Minutes Checklist

Execute in order; do not skip the timeline.

1. **Declare the incident.** State it in the incident channel: severity, one-line summary, responder name. Declaration unlocks authority for disruptive action.
2. **Assign roles.** Even with two people: one Incident Commander (coordinates, communicates) and one Operator (types commands). Hand coordination to `incident-commander` if it outgrows one channel.
3. **Start the timeline.** Append-only with UTC timestamps, one line per command, observation, and decision.
4. **Snapshot current state before changing anything.** Run the capture block below; save output to durable storage outside the cluster.
5. **Check the obvious.** Recent deploys, config changes, feature-flag flips in the last 2 hours. Most incidents are change-induced.
6. **Pick exactly one mitigation** from the playbook; do not stack.

State capture block (run once, save everything):

```bash
# Cluster and node health
kubectl get nodes -o wide
kubectl top nodes 2>/dev/null || true

# Workload state, affected namespace
NS=affected-namespace
kubectl -n "$NS" get pods -o wide
kubectl -n "$NS" get deploy,sts,ds,svc,ingress,hpa,pdb

# Recent events, sorted by time
kubectl -n "$NS" get events --sort-by=.lastTimestamp | tail -n 50

# Restart and crash signals
kubectl -n "$NS" get pods --field-selector=status.phase!=Running
kubectl -n "$NS" get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[*].restartCount}{"\n"}{end}'

# Live resource pressure
kubectl top pods -n "$NS" 2>/dev/null || true
```

## Mitigation Playbook (Choose One)

Pick the single most likely mitigation. Stacking destroys attribution: you will not know which one worked or what to learn.

| If the trigger is... | Mitigation | Why this one |
| ---------------------- | ------------ | -------------- |
| A deploy within the last 2 h correlates with symptoms | Rollback deploy | Fastest known-good state |
| Load-driven saturation: CPU/mem at limit, HPA maxed, queue growing | Scale out | Adds capacity without changing code |
| A single dependency or new code path is failing | Circuit-break / feature flag | Removes the poison path without a deploy |
| One node, zone, or ingress path is bad | Traffic shift / drain | Removes the sick unit |
| Wedged process, deadlock, leaked connections | Restart with cause capture | Clears runtime state, but only after evidence is taken |

### Option A: Rollback deploy

```bash
# Roll back to the previous revision
kubectl -n "$NS" rollout undo deployment/<name>

# Or pin to a specific known-good revision
kubectl -n "$NS" rollout undo deployment/<name> --to-revision=<N>

# Watch until complete
kubectl -n "$NS" rollout status deployment/<name> --timeout=300s
```

Verification: error rate and latency return to the pre-deploy baseline within 5 min; `kubectl -n "$NS" get pods` shows the old image tag fully rolled out.

### Option B: Scale out

```bash
# Manual scale past the HPA ceiling
kubectl -n "$NS" scale deployment/<name> --replicas=<N>

# Stop the HPA fighting the manual scale
kubectl -n "$NS" patch hpa <name> --type merge -p '{"spec":{"minReplicas":<N>}}'
```

Verification: `kubectl top pods -n "$NS"` shows per-pod CPU/memory dropping; queue depth and p99 latency trend down within 5-10 min. Check `kubectl describe nodes | grep -A5 Allocated` for headroom first.

### Option C: Circuit-break / feature flag

```bash
# Flip the flag; configmap example when no flag service exists
kubectl -n "$NS" patch configmap <flags-cm> --type merge -p '{"data":{"FEATURE_X_ENABLED":"false"}}'

# Restart consumers if config is read at boot
kubectl -n "$NS" rollout restart deployment/<name>
```

Verification: calls to the failing dependency drop to zero in metrics; user-facing error rate falls toward the defined fallback (degraded but up).

### Option D: Traffic shift / drain

```bash
# Cordon the suspect node
kubectl cordon <node>

# Drain gracefully, honoring PDBs
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data --grace-period=60

# For a zonal shift: scale down the bad zone or pull it from the
# load balancer / ingress backend pool per your platform's mechanism
```

Verification: pods reschedule onto healthy nodes and reach Ready; health checks from the load balancer pass; per-node or per-zone error contribution disappears from dashboards.

### Option E: Restart with cause capture

Capture why the process wedged before restarting, or the postmortem dies here.

```bash
# Previous logs before they rotate away
kubectl -n "$NS" logs <pod> -c <container> --previous --timestamps > /tmp/<pod>-previous.log 2>&1 || true

# Goroutine/thread dumps if exposed, then current logs
kubectl -n "$NS" exec <pod> -c <container> -- sh -c 'kill -QUIT 1; sleep 2' 2>/dev/null || true
kubectl -n "$NS" logs <pod> -c <container> --timestamps --tail=2000 > /tmp/<pod>-current.log

# Now restart
kubectl -n "$NS" delete pod <pod>
```

Verification: replacement pod reaches Ready and error rates drop. If it wedges identically within minutes, return to triage and pick a different mitigation.

## Evidence Capture for Postmortem

Evidence is perishable: events expire after roughly an hour by default, `--previous` logs vanish on pod deletion, metrics downsample. Capture early, store outside the cluster.

```bash
# Events (default retention ~1h; grab now)
kubectl -n "$NS" get events --sort-by=.lastTimestamp -o wide > /tmp/events.log

# Cluster-wide if the blast radius is unclear
kubectl get events -A --sort-by=.lastTimestamp | tail -n 200 > /tmp/events-all.log

# Current and previous logs for every affected pod
for p in $(kubectl -n "$NS" get pods -o name); do
  kubectl -n "$NS" logs "$p" --all-containers --timestamps --tail=5000 > "/tmp/$(basename "$p")-current.log" 2>&1 || true
  kubectl -n "$NS" logs "$p" --all-containers --previous --timestamps > "/tmp/$(basename "$p")-previous.log" 2>&1 || true
done

# Describe captures probe failures, image pulls, OOM kills, scheduling
kubectl -n "$NS" describe pods > /tmp/describe-pods.log

# Metrics: see observability/prometheus for instant/range PromQL and
# observability/grafana for dashboard export pinned to the UTC incident window.
```

Timeline rules:

- Append-only, UTC timestamps, one fact per line. Corrections get a new line marked `CORRECTION`; never edit history.
- Record commands and output summaries, decisions with the reasoning available at the time, and every external communication.
- The timeline plus the captures above are the mandatory postmortem inputs. Structure lives in `incident-runbook-templates` and `runbook-creator`.

## Observability Tooling Pointers

Prefer the sibling observability skills over improvising queries under pressure:

- `observability/prometheus` -- instant PromQL for error rate, latency percentiles, saturation (USE/RED), and alert state; range queries in the incident window for before/after comparison.
- `observability/grafana` -- dashboards pinned to the incident time range, panel export for evidence, annotating the mitigation moment for the postmortem.
- `observability/loki` -- label-scoped log hunts filtering on the failing request or trace ID, confirming the mitigation silenced the error pattern.

Baseline loop: after each action, check one golden signal (usually error rate) at 1- and 5-min granularity before declaring success.

## Communication

Never miss a scheduled update even with nothing new; "still investigating, next update at HH:MM UTC" is valid.

| Severity | Channel | Cadence | Audience |
| ---------- | --------- | --------- | ---------- |
| P0 | Incident channel + bridge call | Every 15-20 min | Engineering, support, exec sponsor, comms |
| P1 | Incident channel | Every 30 min | Engineering, support leads |
| P2 | Incident channel or ticket | Every 2 h | Owning team, support |
| P3 | Ticket | Daily or on resolution | Owning team |

Status update template:

```text
[STATUS] <severity> <service> -- <YYYY-MM-DD HH:MM UTC>
Summary: <one sentence, current user impact>
Impact: <who/what is affected, error rate or % if known>
Current action: <the single mitigation in progress>
Next update: <HH:MM UTC>
Incident Commander: <name>  Operator: <name>
```

Stakeholder map:

| Stakeholder | When to engage | What they need |
| ------------- | ---------------- | ---------------- |
| On-call secondary | P0-P1 immediately | Timeline access, command readiness |
| Service owner team | Any severity touching their service | Technical detail, deploy history |
| Customer support | P0-P1, or any user-visible impact | User-facing summary, workaround |
| Exec sponsor | P0 within 30 min | Impact magnitude, honest ETA, not detail |
| Security team | Any breach or data-exposure suspicion | Preserve evidence; freeze destructive actions |
| Comms/legal | P0 with external or regulated impact | Approved external wording only |

Rules: one voice per audience; no speculation in status updates, only what is verified and being tried; every update goes into the timeline.

## When to Escalate

- Mitigation exhausted or blast radius growing -> hand coordination to `incident-commander`.
- Symptoms recur, root cause unknown -> deep investigation with `incident-response`.
- Resolved -> codify with `incident-runbook-templates` or `runbook-creator` so the next responder executes, not improvises.

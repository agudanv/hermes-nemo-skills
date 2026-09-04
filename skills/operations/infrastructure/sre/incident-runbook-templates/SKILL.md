---
name: incident-runbook-templates
description: "Incident runbook templates: a structure standard (owner, last-verified, escalation, dashboards metadata; detection with false-positive notes; triage decision trees; mitigation steps with exact command, expected output, verification, rollback; resolution and follow-up), templates for CrashLoopBackOff, OOMKilled, high API latency, certificate expiry, disk/node pressure, and database connection exhaustion, plus a worked OpenShift example and communication templates. Use when asked to write a runbook, create an incident playbook template, build an on-call runbook, or standardize detection, triage, and mitigation steps."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Incident Runbook Templates

A runbook lets any on-call engineer with zero context mitigate a known failure by executing steps in order. Commands use `kubectl`; `oc` is a drop-in replacement on OpenShift. Copy the closest template, replace every `<placeholder>`, and execute every command (staging, drill, or incident) before setting `last-verified`. One alert maps to one runbook; the alert message embeds the runbook id. For a bespoke runbook, see `runbook-creator`.

## Runbook Structure Standard

Five mandatory sections, in order. A runbook missing any is a draft; never link a draft from an alert.

### Metadata Block

```yaml
id: RUN-<nnn>
title: <one-line failure name>
service: <service> / <namespace>
owner: <owning team>            # accountable, not merely notified
last-verified: <YYYY-MM-DD>     # date every command was last executed
review-cadence: <90d|180d>
expected-severity: <SEV-1|2|3>
escalation:
  primary: <on-call rotation>
  secondary: <peer rotation; engaged after 15 min unmitigated>
  management: <eng manager; engaged after 30 min unmitigated>
dashboards: [<golden-signal URL>, <dependency URL>]
alerts: [<alert name(s) that open this runbook>]
depends-on: [<databases, upstream services>]
```

### Detection

Alert reference (name, firing threshold, evaluation window, runbook link embedded in the alert); human-visible symptoms; false-positive note: benign conditions that fire the same alert and how to recognize them.

### Triage Decision Tree

An ordered ASCII tree, one screen max, routing to a mitigation step or another runbook. The first branch splits on the most discriminating signal (exit code, metric shape, scope), not the most common cause.

### Mitigation Steps

Numbered M1..Mn, least-invasive first, read-only diagnostics before mutations. Every step carries: Action (one imperative); Command (exact, namespaced); Expected output (literal); Verification (observable signal); Rollback (exact undo, or an explicit "none"). A mutating step without a recorded rollback is a process bug.

### Resolution and Follow-Up

Recovery criteria (alert clear for N cycles, error rate under SLO for T minutes); escalation trigger if mitigation fails within a stated timeout; follow-up actions with owners and due dates.

## Template Library

### CrashLoopBackOff

Detection: `KubePodCrashLooping`-class alert; dependents see intermittent 5xx.

```text
Pod restarting?
 +-- exit 137 / OOMKilled --> OOMKilled template
 +-- exit 1-2 with stack trace --> M3 if it began with the last rollout, else M4 (page owner)
 +-- CreateContainerConfigError --> missing ConfigMap/Secret key --> M4
 +-- ImagePullBackOff --> registry/pull-secret issue, other runbook
```

M1/M2 -- diagnose (no rollback): `kubectl -n <ns> get pods -l app=<name> -o wide`; `describe pod/<pod>` (Last State = reason + exit code); `logs <pod> --previous --tail=100`; events via `--field-selector involvedObject.name=<pod>`.

M3 -- rollback: `kubectl -n <ns> rollout undo deployment/<name>`; `rollout status deployment/<name> --timeout=180s`. Expected: `rolled back`, then `successfully rolled out`. Verify: pods `Running 1/1`, restarts frozen. Rollback: `rollout undo --to-revision=<n>`.

M4 -- fix forward: `kubectl -n <ns> apply -f <fixed>.yaml`; `rollout status`. Rollback: M3.

Resolution: alert clear two evaluation windows; errors under SLO 15 min. Follow-up: CI check that referenced ConfigMap keys exist. The worked example below is this template filled end-to-end.

### OOMKilled

Detection: exit code 137, reason `OOMKilled`; restarts climbing without a new deploy.

Diagnose (no rollback): `kubectl -n <ns> get pod <pod> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.exitCode}'` (expect `137`); `top pod -l app=<name> --containers`; limit via `get deploy <name> -o jsonpath='{.spec.template.spec.containers[*].resources}'`.

Triage: steady under 80% of limit with spikes = limit too low; monotonic growth = leak.

Mitigate: `kubectl -n <ns> set resources deployment/<name> --limits=memory=<new-limit>` (limit too low) or `kubectl -n <ns> rollout restart deployment/<name>` (leak). Expected: `resource requirements updated` / `restarted`. Verify: no new 137 exits for 24h. Rollback: restore the recorded previous limit.

Resolution: restarts flat 24h. Follow-up: heap profile if leak; alert at 80% of limit.

### High-Latency API

Detection: latency SLO burn alert, e.g. `histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m]))) > <p99-budget>`.

Triage: one endpoint slow = handler/query regression; all endpoints = pod saturation (`top pods`), HPA at max, downstream latency, or DB pool (template below).

Mitigate: record `kubectl -n <ns> get deploy <name> -o jsonpath='{.spec.replicas}'`, then `kubectl -n <ns> scale deployment/<name> --replicas=<n>`. Expected: `deployment.apps/<name> scaled`. Verify: p99 under budget within 10 min. Rollback: scale back to the recorded count.

Resolution: burn rate under 1x for 30 min. Follow-up: capacity review; autoscaling headroom.

### Certificate Expiry

Detection: expiry alerts at 30/14/7 days; manual sweep:

```bash
kubectl -n <ns> get secret <tls-secret> -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -subject -enddate
echo | openssl s_client -connect <host>:443 -servername <sni> 2>/dev/null | openssl x509 -noout -subject -enddate
```

Expected: `notAfter` more than 14 days out. Served cert older than stored = a replica missed the rotation; restart it.

Triage: renewal blocked by DNS01/HTTP01 solver failure, issuer rate limit, or a deploy overwriting the Secret with a committed static cert.

Mitigate (cert-manager): `kubectl -n <ns> get certificate -o wide` (READY True?) and `describe certificate/<name>` events; back up and force reissue: `get secret <tls-secret> -o yaml > /tmp/<tls-secret>.bak`, `delete secret <tls-secret>`. Expected: secret recreated within minutes; `READY True`. Verify: served `notAfter` is new; alerts clear. Rollback: `kubectl apply -f /tmp/<tls-secret>.bak` (only if the old cert is unexpired).

Resolution: all endpoints serve the new chain. Follow-up: alert on `READY False`; audit the repo for committed certs.

### Disk Pressure and Node Pressure

Detection: node condition `DiskPressure`/`MemoryPressure`/`PIDPressure`; filesystem alerts; evicted pods.

Diagnose (no rollback): `kubectl get node <node> -o jsonpath='{.status.conditions[?(@.type=="DiskPressure")].status}'` (expect `True`); evicted pods via `kubectl get pods -A --field-selector status.phase=Failed -o wide | grep <node>`; `kubectl debug -it node/<node> --image=<registry>/toolbox:<tag> -- chroot /host df -h` (mount above 85%).

Mitigate: `kubectl cordon <node>`; in the debug shell `crictl rmi --prune`, `journalctl --vacuum-time=2d`, `du -xh /var/lib/containers | sort -h | tail -5`; then `kubectl uncordon <node>`. Expected: condition flips `False` within minutes. Verify: evictions stop; usage under 80%. Rollback: cordon/uncordon reverse directly; pruned images re-pull on demand.

Follow-up: fix the noisy source (crashing app logs, unbounded local PV); alert at 75%.

### Database Connection Exhaustion

Detection: `FATAL: sorry, too many clients already` (PostgreSQL) or pool acquire timeouts.

Diagnose (no rollback): `kubectl -n <db-ns> exec <pg-pod> -c postgres -- psql -U <admin> -d <db> -c "SHOW max_connections;"` and `-c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"`. Triage: an `idle in transaction` pile points at one leaking service (`application_name`, `client_addr`).

Mitigate: M1 -- `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle in transaction' AND xact_start < now() - interval '15 minutes';` via psql (one row per killed pid). M2 -- `kubectl -n <ns> rollout restart deployment/<leaky-service>`. Verify: errors stop; activity count falls. Rollback: none (clients reconnect). M3 (raise `max_connections`) is a last resort requiring a DB restart; revert after the leak fix.

Resolution: activity under 70% of `max_connections` for 30 min. Follow-up: fix the leak; per-service pool limits; alert at 80% of max.

## Worked Example: Pod CrashLoopBackOff on OpenShift

A complete runbook, filled in -- the minimum acceptable "good" for anything linked from an alert.

```yaml
id: RUN-104
title: order-processor pods CrashLoopBackOff in prod-checkout
service: order-processor / prod-checkout (OpenShift)
owner: checkout-platform
last-verified: 2026-08-28
review-cadence: 90d
expected-severity: SEV-2
escalation:
  primary: checkout-oncall
  secondary: integration-oncall      # after 15 min unmitigated
  management: checkout-eng-manager   # after 30 min unmitigated
dashboards: [https://grafana.example.internal/d/checkout-golden]
alerts: [KubePodCrashLooping, CheckoutSubmit5xx]
depends-on: [order-db, kafka/checkout-events]
```

**Detection.** Alert `KubePodCrashLooping` (restarts > 3 in 1h) on `prod-checkout`, app `order-processor`; a subset of checkout submits returns 5xx while the route balances across crashing and healthy pods. False positive: the weekly soak test fires the same alert name in `stg-checkout`, which pages a different rotation.

**Triage.**

```text
Exit code from `oc describe`:
 +-- 137 / OOMKilled --> RUN-107 (memory-limit runbook)
 +-- 1 + config FATAL in previous logs --> M3 if a rollout happened
 |    in the last 60 min (`oc rollout history`), else M4
 +-- CreateContainerConfigError --> M4 (missing key)
```

**Mitigation.**

M1 -- confirm scope (no rollback): `oc -n prod-checkout get pods -l app=order-processor`. Expected:

```text
NAME                              READY  STATUS             RESTARTS  AGE
order-processor-b4c9d6d8d-2q9zz   0/1    CrashLoopBackOff   7         22m
order-processor-b4c9d6d8d-p7k4m   0/1    CrashLoopBackOff   6         22m
```

Verify: all replicas affected = deployment-level cause (config or image), not a node problem.

M2 -- read the failure (no rollback):

```bash
pod=$(oc -n prod-checkout get pods -l app=order-processor -o jsonpath='{.items[0].metadata.name}')
oc -n prod-checkout describe pod/"$pod" | grep -A4 'Last State'
oc -n prod-checkout logs "$pod" --previous --tail=20
```

Expected: `Exit Code: 1`, and `FATAL: required config key DB_POOL_MIN missing from ConfigMap checkout-runtime`.

M3 -- roll back (under 3 min): `oc -n prod-checkout rollout undo deployment/order-processor`; `oc -n prod-checkout rollout status deployment/order-processor --timeout=180s`. Expected: `deployment.apps/order-processor rolled back`, then `deployment "order-processor" successfully rolled out`. Verify: pods `Running 1/1`, checkout 5xx at baseline within 5 min, alert clears at the next evaluation. Rollback: `oc rollout undo deployment/order-processor --to-revision=<n>` from `oc rollout history`.

M4 -- fix forward (only after rollback or with product-owner approval):

```bash
oc -n prod-checkout get cm checkout-runtime -o yaml > /tmp/checkout-runtime.bak
${EDITOR:-vi} /tmp/checkout-runtime.bak     # restore the DB_POOL_MIN key
oc -n prod-checkout apply -f /tmp/checkout-runtime.bak
oc -n prod-checkout rollout restart deployment/order-processor
```

Expected: `configmap/checkout-runtime configured`, then `deployment.apps/order-processor restarted`. Verify: new pods `Running`; startup log shows `DB_POOL_MIN=8 loaded`. Rollback: apply the original ConfigMap from git and repeat the restart.

**Resolution.** Recovered when checkout 5xx is at baseline for 15 min AND the alert has been clear for two cycles. If pods still crashloop 10 min after M3, escalate to integration-oncall (ConfigMap renamed out of band).

**Follow-up.** Postmortem with the previous-logs excerpt and the guilty commit; CI check failing builds when a deployment references a key absent from `checkout-runtime` (owner: checkout-platform, due +14d); drill this runbook at the next game day.

## Communication Templates

Update on cadence even when nothing changed; communication is a scheduled deliverable.

### Internal Status Update

```markdown
[SEV-2] order-processing degraded in prod-checkout
Impact:      ~18% of checkout submits failing since 14:02 UTC.
Detected:    KubePodCrashLooping on order-processor (Runbook RUN-104).
Mitigation:  Rollback of revision 47 applied 14:21 UTC; verifying.
Next update: 14:35 UTC, or immediately on change.
```

Rules: SEV-1 every 15 min, SEV-2 every 30, SEV-3 hourly; UTC timestamps; every update names the next update time; bad news early and flat.

### Customer-Facing Notice

```markdown
Subject: Elevated checkout errors

We are investigating an issue causing some checkout attempts to fail.
Completed orders are not affected; please retry after a few minutes.
Next update by 15:30 UTC.
```

Rules: plain language; never node names, namespaces, internal alert names, or vendor detail; always a next-update time; resolution notice states the window plus a one-sentence confirmed cause. Legal review before any notice mentioning customer data.

## Maintenance Discipline

### Review Cadence

| Runbook class | Max age of last-verified | When exceeded |
| --- | --- | --- |
| Front line for SEV-1/2 alerts | 90 days | Staleness report pages the runbook owner |
| Other verified runbooks | 180 days | Owner notified in triage review |
| Any runbook | immediate | Dependency/tooling change, reworded alert, or a failed drill command or branch |

### Last-Verified Enforcement

`last-verified` is truthful only if every command was executed with output captured; enforce it in CI:

```bash
for rb in runbooks/RUN-*.md; do
  verified=$(grep -oE 'last-verified: [0-9-]+' "$rb" | cut -d' ' -f2)
  age=$(( ($(date +%s) - $(date -d "$verified" +%s)) / 86400 ))
  [ "$age" -gt "${RUNBOOK_MAX_AGE_DAYS:-180}" ] && { echo "STALE (${age}d): $rb"; exit 1; }
done
```

A runbook past its cadence gets an `UNVERIFIED -` title prefix and is unlinked from alerts until re-executed. Staleness pages the owner, never the on-call.

### Drill Scheduling

- Quarterly game day for runbooks covering the top quartile of alert volume (all others at least annually); a new runbook must survive one dry drill before it may be linked from an alert.
- Inject matching faults in staging: bad config key, near-expiry certificate, saturated connection pool, full node filesystem.
- Score each drill: time-to-detect, time-to-mitigate, wrong branches taken, failed commands. Every failed command becomes a runbook PR within 48h; `last-verified` updates only after the corrected version passes.

## Related Skills

- `runbook-creator` -- authoring when no template fits.
- `incident-responder` -- live-incident execution; these templates are its content.
- `incident-response-incident-response` -- lifecycle: severity, communications, postmortem.

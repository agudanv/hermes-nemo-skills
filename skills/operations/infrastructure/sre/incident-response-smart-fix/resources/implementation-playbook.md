<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Smart Fix: Implementation Playbook

Operational companion to the `incident-response-smart-fix` skill: concrete commands, query patterns, and record templates for the observe -> hypothesize -> experiment -> verify loop on Kubernetes/OpenShift. Assumes the agent runs inside a Linux pod with cluster access; no macOS tooling, no pipe-to-shell installers.

## 1. Tooling and Environment

| Tool | Purpose | Notes |
| --- | --- | --- |
| `kubectl` | Cluster state, logs, events, exec, debug | On OpenShift substitute `oc` (see `openshift-operations`) |
| `curl` + `jq` | Prometheus/Loki HTTP APIs | Always available; preferred over extra CLIs |
| `logcli` | Optional: interactive Loki queries | Pinned binary install below |

Environment variables referenced by name only, never values: `KUBECONFIG`, `PROM_URL`, `LOKI_URL`, `ARTIFACT_DIR`.

```bash
export ARTIFACT_DIR="${ARTIFACT_DIR:-/tmp/smartfix-$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$ARTIFACT_DIR"
```

If `logcli` is required, install a pinned release binary with a checksum (never pipe to a shell):

```bash
LOGCLI_VERSION="3.4.2"                        # pin per environment
LOGCLI_SHA256="<sha256-of-release-binary>"    # record the expected digest
curl -fsSLo /tmp/logcli.zip \
  "https://github.com/grafana/loki/releases/download/v${LOGCLI_VERSION}/logcli-${LOGCLI_VERSION}-linux-amd64.zip"
unzip -q -o /tmp/logcli.zip -d /tmp
install -m 0755 "/tmp/logcli-${LOGCLI_VERSION}-linux-amd64" /usr/local/bin/logcli
echo "${LOGCLI_SHA256}  /usr/local/bin/logcli" | sha256sum -c -
```

Every recipe here works over the Loki HTTP API (`${LOKI_URL}/loki/api/v1/query_range`, same `curl -sG` shape as 2.1) without `logcli`.

## 2. Loop Artifacts

### 2.1 Baseline Capture (mandatory, before any mutation)

Snapshot cluster state and key metrics into `${ARTIFACT_DIR}`; every later comparison runs against this.

```bash
NS="payments"
kubectl -n "$NS" get deploy,pod,svc,endpointslice,hpa,pdb -o wide \
  > "${ARTIFACT_DIR}/topology-before.txt"
kubectl -n "$NS" get deploy <deployment> -o yaml \
  > "${ARTIFACT_DIR}/deploy-before.yaml"
kubectl -n "$NS" get events --sort-by=.lastTimestamp \
  > "${ARTIFACT_DIR}/events-before.txt"
kubectl -n "$NS" top pods > "${ARTIFACT_DIR}/top-before.txt" 2>/dev/null || true
```

```bash
curl -sG "${PROM_URL}/api/v1/query_range" \
  --data-urlencode 'query=histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{namespace="payments"}[5m])))' \
  --data-urlencode "start=$(date -u -d '2 hours ago' +%s')" \
  --data-urlencode "end=$(date -u +%s)" \
  --data-urlencode "step=300" | jq . > "${ARTIFACT_DIR}/p99-baseline.json"
```

### 2.2 Hypothesis Register

One entry per hypothesis; rejected hypotheses stay in the register with their falsifier, which prevents re-testing dead ends.

```text
ID: H1
Statement: If <cause X> produces <symptom Y>, then <observable M> on
           <system S> must show <W> by <horizon T>.
Source evidence: <queries, log links, deploy timestamps>
Falsifier: <the observation that kills this hypothesis>
Status: proposed | testing | confirmed | rejected
```

### 2.3 Experiment Record

```text
ID: E1
Hypothesis under test: H1
Change (exactly one): <what is being changed>
Arena: staging | canary pod | single node | staging namespace
Predicted observation: <copied verbatim from H1>
Rollback (pre-verified): <exact commands>
Result: prediction-confirmed | prediction-violated | inconclusive
Decision: promote | rollback | refine hypothesis
```

## 3. Investigation Recipes by Signal

### 3.1 Metric Spikes (Prometheus)

Quantify the spike, isolate the affected population, overlay change events.

Quantify versus comparison windows:

```promql
sum by (namespace) (rate(http_requests_total{status=~"5.."}[5m]))
sum by (namespace) (rate(http_requests_total{status=~"5.."}[5m] offset 1h))
```

Isolate the population (top contributor usually names the suspect):

```promql
topk(10, sum by (namespace, service, handler) (rate(http_requests_total{status=~"5.."}[5m])))
```

Overlay change events: pods that (re)started inside the spike window are first suspects:

```promql
sum by (namespace, pod) (changes(container_start_time_seconds{namespace="payments"}[30m]))
sum by (namespace, pod) (increase(kube_pod_container_status_restarts_total{namespace="payments"}[30m]))
```

Rule saturation in or out before blaming code:

```promql
# CPU throttling fraction per pod
sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{namespace="payments"}[5m]))
  /
sum by (pod) (rate(container_cpu_cfs_periods_total{namespace="payments"}[5m]))

# Memory headroom: working set as a fraction of the limit
topk(10,
  max by (namespace, pod, container) (container_memory_working_set_bytes{namespace="payments", container!=""})
    /
  max by (namespace, pod, container) (kube_pod_container_resource_limits{namespace="payments", resource="memory"}))
```

Scrape hygiene: use a range at least 4-5x the scrape interval; a 30s scrape with a 1m rate window returns holes, not truth.

### 3.2 Log Error Bursts (Loki LogQL)

Burst volume by namespace:

```logql
sum by (namespace) (count_over_time({namespace="payments"} |= "error" [10m]))
```

Filter to a level, render just the message:

```logql
{namespace="payments", app="checkout"} | json | level="error" | line_format "{{.msg}}"
```

Match a family of failures without parsing:

```logql
sum by (pod) (rate({namespace="payments", app="checkout"} |~ "(?i)(timeout|deadline exceeded|connection refused)" [5m]))
```

Group otherwise-unique lines by shape:

```logql
sum by (msg) (
  count_over_time({namespace="payments", app="checkout"} |= "error" | pattern "<_> <level> <msg>" [10m])
)
```

Procedure:

1. Locate onset: compare consecutive windows (`offset 1h`, `offset 2h`) or a Grafana Explore histogram (see `observability/grafana`).
2. Rank message families; sample 3-5 representative raw lines per family.
3. Align onset with deploy/restart timestamps from 3.1. Onset within 2 minutes of a rollout is a deploy candidate; onset at a traffic peak with no change event is a load candidate.
4. Distrust silence without confirmation: flat zero at burst time plus a sudden backfill later is ingestion lag, not recovery (pitfalls, 7.4).

### 3.3 Latency Tails (p99 Decomposition)

Decide whether the whole distribution moved (overload) or only the tail (contention, slow dependency, retries), then attribute the tail.

```promql
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{service="checkout"}[5m])))
histogram_quantile(0.50, sum by (le) (rate(http_request_duration_seconds_bucket{service="checkout"}[5m])))
```

| p50 | p99 | Reading | First suspects |
| --- | --- | --- | --- |
| flat | up | tail-only pathology | queueing, GC pauses, lock contention, one slow dependency, retries |
| up | up proportionally | systemic overload | saturation, insufficient replicas, expensive change in hot path |
| up | down | recovery in progress or traffic shifted | verify population mix before celebrating |

Rank handlers by their own tail:

```promql
topk(10,
  histogram_quantile(0.99,
    sum by (le, handler) (rate(http_request_duration_seconds_bucket{service="checkout"}[10m]))))
```

Weigh traffic share (`http_request_duration_seconds_count`); a hot handler at a mediocre p99 can own the aggregate tail.

Retry amplification: if downstream calls roughly doubled at the same moment, a timeout-plus-retry policy is multiplying load during degradation:

```promql
sum(rate(dependency_request_duration_seconds_count{service="checkout"}[5m]))
sum(rate(dependency_request_duration_seconds_count{service="checkout"}[5m] offset 1h))
```

Runtime pauses and throttling (names vary by client library; adapt):

```promql
histogram_quantile(0.99, sum by (le, pod) (rate(gc_pause_seconds_bucket{namespace="payments"}[5m])))
sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{namespace="payments"}[5m]))
```

Use distributed traces (see `observability/opentelemetry`) when multiple downstreams are involved; per-dependency histograms cannot show critical-path serialization.

### 3.4 Crash Loops

Classify the exit, then match the class to a cause family.

```bash
kubectl -n "$NS" get pods --sort-by=.status.containerStatuses[0].restartCount
kubectl -n "$NS" get pod <pod> -o jsonpath='{range .status.containerStatuses[*]}{.name}{" exit="}{.lastState.terminated.exitCode}{" reason="}{.lastState.terminated.reason}{"\n"}{end}'
kubectl -n "$NS" logs <pod> --previous --tail=200
kubectl -n "$NS" describe pod <pod> | sed -n '/Events:/,$p'
```

| Code | Meaning | First places to look |
| --- | --- | --- |
| 0 | process exited cleanly | short-lived entrypoint under a restart policy; PID 1 reaping (see `hermes-s6-container-supervision`) |
| 1 | uncaught application error | `--previous` logs; missing env var; failed config parse |
| 126 | command cannot execute | missing exec bit, bad shebang, wrong arch |
| 127 | command not found | image tag drift, entrypoint renamed in new build |
| 134 | SIGABRT | native assert, glibc abort, JVM fatal error |
| 137 | SIGKILL (128+9) | OOMKill (check `reason`) or liveness-probe kill |
| 139 | SIGSEGV | native extension, JIT bug, corrupted shared lib |
| 143 | SIGTERM (128+15) | shutdown exceeded `terminationGracePeriodSeconds`; slow drain under liveness deadline |

Distinguish process exit from probe kill: `lastState.terminated.reason` is `Error` for app exits and `OOMKilled` for cgroup kills; probe kills surface as `Liveness probe failed` Warning events with exit 137 or 143. A restart loop with healthy logs points at probe timing (probe timeout shorter than a slow endpoint, missing startup probe on a cold cache).

Verify the running image matches intent before chasing code:

```bash
kubectl -n "$NS" get pod <pod> -o jsonpath='{range .spec.containers[*]}{.name}{" "}{.image}{"\n"}{end}'
kubectl -n "$NS" get deploy <deployment> -o jsonpath='{.spec.template.spec.containers[*].image}{"\n"}'
```

If live spec and GitOps source disagree, switch to `gitops-troubleshooting`.

### 3.5 OOMKills (cgroup Memory Analysis)

Confirm the OOMKill, characterize the growth shape, separate leak from underprovisioning.

```bash
kubectl -n "$NS" get pod <pod> -o jsonpath='{range .status.containerStatuses[*]}{.name}{" reason="}{.lastState.terminated.reason}{" exit="}{.lastState.terminated.exitCode}{"\n"}{end}'
```

```promql
max by (namespace, pod, container) (kube_pod_container_status_last_terminated_reason{reason="OOMKilled"} == 1)
sum by (pod) (increase(kube_pod_container_status_restarts_total{namespace="payments"}[1h]))
```

Growth shape on `container_memory_working_set_bytes` decides the hypothesis class:

| Shape | Class | Next step |
| --- | --- | --- |
| monotonic climb proportional to requests | leak | correlate with QPS; profile |
| step change at deploy time | new build footprint | diff resource usage old vs new cohort |
| steady but pinned at limit | underprovisioned limit | raise limit as canary experiment |
| sawtooth with periodic reset | cache or batch window | bound cache; spread batch schedule |

Node-level forensics when pod metrics are inconclusive (cgroup v2 paths; v1 uses `/sys/fs/cgroup/memory/memory.usage_in_bytes` and `memory.failcnt`):

```bash
kubectl debug node/<node> -it --image=ubuntu:24.04 -- chroot /host sh -c \
  'cat /sys/fs/cgroup/memory.peak 2>/dev/null; cat /sys/fs/cgroup/memory.events'
kubectl debug node/<node> -it --image=ubuntu:24.04 -- chroot /host sh -c \
  'grep -E "^(anon|file|slab|sock|workingset_refault) " /sys/fs/cgroup/memory.stat'
```

Interpretation:

- `memory.events` `oom_kill` increments confirm the cgroup delivered the kill.
- Working set is roughly `memory.current - inactive_file`: the kernel reclaims page cache, so growth dominated by `file` rarely OOMs a cgroup; growth dominated by `anon` does.
- JVM: verify container awareness (`-XX:+UseContainerSupport`, default since JDK 8u191/11) and set `-XX:MaxRAMPercentage` below 75% when the process also allocates off-heap (Netty arenas, direct buffers, JNI). Python: `MALLOC_ARENA_MAX` for glibc arena bloat. Node: watch `--max-old-space-size` against the limit.
- Node-level pressure (Burstable pods evicted first): check `node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.10` and kubelet eviction events; that path is platform work, see `kubernetes-troubleshooting`.

Canary test for underprovisioned: raise only the limit on one canary pod. Prediction: restarts stop AND working set plateaus below the new limit. If restarts stop but growth continues monotonically, the limit raise bought time -- the leak hypothesis is confirmed instead, and the fix is a profile plus bounded caches, not a bigger number.

## 4. Hypothesis Templates

Canonical form:

```text
If <cause X> is producing <symptom Y>, then <observable M> must show
<W> by <horizon T>; observing <not-W> refutes it.
```

Cheap refutation first: if the prediction is checkable against telemetry that already exists, check it before designing any experiment. Many hypotheses die free. Filled examples by class:

- **Deploy regression.** If the 14:02 build causes the p99 spike, then pods started after 14:02 (cohort by `container_start_time_seconds`) must show higher p99 than pre-14:02 pods on the same traffic mix.
- **Connection pool exhaustion.** If pool exhaustion causes the 5xx burst, then the in-flight gauge must plateau at the pool cap while request rate drops (saturation sawtooth), and raising only pool size on a canary must remove the plateau.
- **GC contention.** If GC pauses cause the p99 tail, then pause-time histograms must spike in the same 5-minute windows as the tail, and a canary with doubled heap must cut p99 by the predicted fraction.
- **Cache cold start.** If cache misses cause read latency after the restart, then hit ratio must drop at restart time and recover with the same time constant as the latency; pre-warming one canary must skip the slow window.
- **Memory leak.** If an unbounded cache causes the OOMKill, then `anon` memory per 1k requests must be roughly constant (footprint grows with cumulative traffic, not concurrency), and bounding the cache on a canary must flatten the slope.
- **Probe timing.** If the liveness probe kills slow-but-alive pods under CPU throttling, then throttled-period spikes must precede each restart, and a canary with doubled probe timeout must stop the loop without code changes.
- **Config drift.** If an env change (not the image) causes the symptom, then two pods on the same image digest but different ConfigMap revisions must differ on the symptom metric.

Rules:

- One cause per hypothesis. "The deploy and the traffic spike" is two hypotheses; test the cheaper first.
- The prediction must name an observable and a horizon. "It will get better" is not a prediction.
- Record the falsifier before running anything; after-the-fact rationalization is how correlation becomes doctrine.

## 5. Experiment Design

### 5.1 Minimum Blast Radius

Choose the smallest arena whose population includes the failing population and whose noise floor is below the predicted effect size.

| Arena | Use for | Notes |
| --- | --- | --- |
| staging namespace | anything testable off production traffic | required first stop when staging exists |
| single canary pod | code, config, limits, probe tuning | traffic share ~ replica share unless a splitter exists |
| one cordoned node | daemonset, kernel, kubelet changes | `kubectl cordon` first; drain after canary is stable |
| traffic-split canary | user-facing behavior changes | ingress canary annotations, mesh weights, or gateway routes |
| whole cluster | never in this loop | escalate; see blast-radius budget in SKILL.md |

Detectability check: the predicted effect must exceed baseline variance:

```promql
stddev_over_time(histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{service="checkout"}[5m])))[1h:5m])
```

If the predicted improvement is smaller than one standard deviation of the baseline, extend the canary hold or increase canary share; otherwise the experiment cannot conclude.

### 5.2 Canary and Dark-Launch Patterns

Manual replica canary (no mesh required): clone the deployment with a distinct name and the same Service selector labels; its share is approximately its replica share.

```bash
kubectl -n "$NS" get deploy checkout -o yaml \
  | sed -e 's/name: checkout$/name: checkout-canary/' \
        -e 's/image: \(.*\):.*/image: \1:<candidate-tag>/' \
        -e '/resourceVersion/d' -e '/uid:/d' -e '/creationTimestamp/d' \
  | kubectl apply -f -
kubectl -n "$NS" scale deploy/checkout-canary --replicas=1
```

Label cohorts explicitly (`track: canary` vs `track: stable` on the pod template) so every comparison query can disaggregate:

```promql
histogram_quantile(0.99, sum by (le, track) (rate(http_request_duration_seconds_bucket{service="checkout"}[5m])))
```

With an ingress or mesh splitter, ramp by weight instead of replicas. Default ramp (tighten holds to your SLO evaluation window; never shorter):

| Step | Share | Minimum hold | Promote when |
| --- | --- | --- | --- |
| 0 | 1 pod | 15 min | canary error rate <= stable cohort |
| 1 | 10% | 2 evaluation windows | p99 within 10% of prediction, no adjacent regression |
| 2 | 50% | 2 evaluation windows | same, plus saturation headroom unchanged |
| 3 | 100% | watch window begins | hand to verification, section 6 |

Dark-launch: run the candidate with a distinct label set and zero external traffic; drive it with synthetic checks (below) or mirrored traffic. Use when even 1-in-N customer exposure is unacceptable.

### 5.3 Synthetic Checks

```bash
while sleep 1; do
  curl -s -o /dev/null --max-time 5 \
    -w '%{http_code} %{time_total}\n' \
    "http://checkout-canary.payments.svc:8080/healthz/diag"
done | tee -a "${ARTIFACT_DIR}/synth-canary.tsv"
```

For continuous probes use blackbox_exporter (`probe_duration_seconds` / `probe_success` per target; see `observability/prometheus`). Synthetic checks detect dead, not slow: pair them with histogram queries, and route a fraction of probes through the external path -- internal-only probes can stay green while the edge is red.

### 5.4 One-Variable Rule

Change exactly one variable per experiment. If the fix needs a new image and an env change, run them as two experiments in sequence; combined, neither result is attributable. The explicit exception is rollback itself, which restores the whole prior state at once.

## 6. Verification and Regression Watch

### 6.1 Acceptance Criteria (numeric, written before applying)

```text
The fix is accepted only if, during the watch window:
  - p99 < 450 ms in 95% of 5-minute windows on the fixed population
  - 5xx rate < 0.1% of requests on the fixed population
  - restart count delta = 0 on the fixed population
  - downstream connection count within 120% of pre-fix baseline
  - no adjacent regression (section 6.3) for 2 consecutive windows
```

### 6.2 Watch Window by Severity

| Severity at time of fix | Watch window | Coverage required |
| --- | --- | --- |
| SEV4/SEV5 | 2h post-promotion | current traffic regime |
| SEV3 | 24h | at least one peak |
| SEV1/SEV2 | 72h | full traffic cycle: peak, trough, one batch window |

### 6.3 Adjacent-Regression Watchlist

A fix that improves its target while degrading a neighbor is a relocation, not a fix. Watch:

- error rate and p99 of sibling services sharing the touched dependency
- connection counts, queue depths, saturation of the shared downstream
- CPU throttling and memory headroom after limit or flag changes
- HPA actuation churn (`increase(kube_horizontalpodautoscaler_status_current_replicas[1h])`) indicating a flapping signal
- cost-adjacent counters when the fix raises limits or replica counts

```promql
sum by (service) (rate(http_requests_total{status=~"5..", namespace="payments"}[5m]))
```

### 6.4 Regression Trigger

Any acceptance criterion or adjacent metric breaching for two consecutive evaluation windows: execute the armed rollback, record the breach in the experiment record, re-enter the loop at HYPOTHESIZE. Do not patch forward from a breached watch window.

On success: promote to full fleet, keep the watch window running, hand the verified procedure to `runbook-creator`, and review the change against `production-readiness` before closing the incident.

## 7. Common Pitfalls

### 7.1 Correlation versus Causation

Trap: a deploy timestamp sits near the spike, rollback "fixes" it, and the real cause (cache warmup cycle, cron-driven traffic pattern, cert rotation) returns on its own schedule. Countermeasure: demand mechanism evidence. The hypothesis must chain cause to effect through an observable intermediate -- queue depth, hit ratio, pool saturation -- not time proximity. Test: if removing all timestamps collapses the story, it was coincidence.

### 7.2 Fix-the-Symptom

Trap: restart clears the leak (timer reset), more replicas mask a deadlock, a bigger limit hides the leak until the node dies. Countermeasure: every fix must survive the withdrawal test -- the hypothesis predicts what happens when the fix is removed, and the verification plan names the metric proving the underlying growth actually stopped. Raising a limit is a stopgap only with a leak hypothesis under test.

### 7.3 Config-versus-Code Confusion

Trap: the image digest is identical across good and bad pods, so code is exonerated -- but a ConfigMap or env edit landed silently; Kubernetes does not restart pods on ConfigMap change unless the deployment spec references a hash of it. Countermeasure: compare runtime state, not intent: `kubectl exec <pod> -- env | sort` on canary versus stable cohorts, `kubectl diff -f <manifest>` against the live object, `helm get values` versus the repo. If drift between Git and cluster is the story, that is `gitops-troubleshooting` territory.

### 7.4 Cache Poisoning of Evidence

Traps:

- **Prometheus staleness and restart windows:** a series dies when its pod dies; a single-scrape gauge right after a restart shows absence, not zero. Wait two scrape intervals before trusting post-change reads; aggregate by cohort rather than per-pod series that churn.
- **Loki backfill:** an ingester or agent outage later delivers old lines; a "burst" may be arrival time, not event time. Compare log timestamp against ingestion time, or corroborate with metrics.
- **Endpoint staleness:** kube-proxy and endpoint controllers lag scale events; brief 5xx during scale-down can be connection reuse to a terminating pod, not an app error. Check EndpointSlice object timestamps against the error window.
- **Dashboard time drift:** a Grafana panel pinned to a stale range looks like "no spike." Regenerate with explicit `start`/`end` API queries (see `observability/grafana`).

### 7.5 Goodhart on Synthetic Checks

Probes targeting a load-balanced virtual IP can be routed only to healthy pods and stay green while a cohort fails. Pin a fraction of probes to specific pod IPs or use the external ingress path; disaggregate synthetics by target.

### 7.6 Averages Hide Bimodality

A canary at 10% traffic moves the fleet mean by almost nothing even when it is on fire. Always split comparison queries by cohort label (`track`, image digest, or `container_start_time_seconds` cohort) before concluding "no change."

## 8. Worked Example: p99 Spike After Deploy

Symptom: alert fires, `payments/checkout` p99 at 2.3s versus a 400ms SLO, starting 14:05.

1. **Observe.** Baseline snapshot (2.1). p50 flat, p99 stepped at 14:05: tail-only pathology. `changes(container_start_time_seconds[30m])` shows 6 pods started 14:02-14:03 (deploy). Throttling flat. Log family `pool acquire timeout` jumps at 14:05.
2. **Hypothesize.** H1: the new build defaults the DB pool to 50 (was 200), queuing under normal concurrency. Prediction: in-flight gauge on post-14:02 pods plateaus at ~50 while stable pods do not; p99 excess is wait time, not query time (downstream span durations flat in traces).
3. **Experiment.** Canary `checkout-canary` from the new image with only the pool-size env restored to 200. Predicted: canary p99 under 400ms within 15 minutes while the main fleet stays at 2s. Rollback armed: `kubectl -n payments delete deploy/checkout-canary` (additive canary, no shared state).
4. **Verify.** Canary p99 340ms at minute 12; stable cohort unchanged. Adjacent check: DB connection count rose 4x as predicted and stays within 120% of the pre-deploy baseline; DB CPU flat. Ramp 1 pod -> 10% -> 50% -> 100% with two-window holds. Watch 72h (SEV2). No breach.
5. **Done.** Fix promoted; register updated with H1 confirmed and H2 (GC) rejected by flat pause histograms; procedure handed to `runbook-creator`.

## 9. Cross-References

- `incident-response`: incident framework, severity, roles
- `incident-responder`: mitigation-first mode; escalation target
- `failure-analysis`: post-containment deep analysis
- `runbook-creator`: verified fix becomes a runbook
- `observability`: prometheus, grafana, loki, opentelemetry guides
- `kubernetes-troubleshooting`: node pressure, networking
- `openshift-operations`: `oc` equivalents of commands here
- `gitops-troubleshooting`: live-versus-repo drift
- `hermes-s6-container-supervision`: PID 1, exit-0 loops
- `production-readiness`: promoted-fix readiness review
- `sre-operations`: SLO policy for watch windows

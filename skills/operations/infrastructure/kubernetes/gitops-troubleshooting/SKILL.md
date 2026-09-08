---
name: gitops-troubleshooting
description: "Diagnose and resolve GitOps day-2 failures: Argo CD applications stuck OutOfSync or Degraded, failing syncs and hooks, server-side apply field-manager conflicts, configuration drift, and rollback decisions, including Argo Rollouts canary analysis. Use when an Argo CD application will not sync, shows Unknown/Degraded health, drifts from the repository, or when deciding between git revert and argocd rollback."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# GitOps Troubleshooting

Operational workflows for when a GitOps-managed cluster stops matching
its repository. This skill handles **day-2 failure diagnosis and
recovery**; for initial Argo CD/Flux setup, repository layout, and sync
policy configuration use `kubernetes-gitops-workflow` in
`platform-automation`, and for workload-level failures (CrashLoopBackOff,
OOMKilled, ImagePullBackOff) use `kubernetes-troubleshooting`.

## Triage matrix

Determine `status` and `health` first; the combination routes the case:

```bash
argocd app get <app>          # or, without the CLI:
kubectl -n argocd get applications.argoproj.io <app> -o yaml
```

| Status | Health | Route |
|---|---|---|
| Synced | Healthy | Done — perceived problem is elsewhere (monitoring, DNS) |
| Synced | Degraded | Workload issue → `kubernetes-troubleshooting`; manifests match repo |
| OutOfSync | Healthy | Drift or manifest-shaping issue → Phase 4/5 below |
| OutOfSync | Degraded | Both: fix sync first, then workload; worst quadrant |

`Pending` beyond a minute means the app controller is wedged or the
repo/cluster connection is down — check controller logs before blaming
the app (Phase 2).

## Phase 1 — Read the actual error

Never reason from the badge alone; fetch the typed condition:

```bash
kubectl -n argocd get app <app> -o jsonpath='{.status.conditions}' | jq .
# operation state of the last sync attempt:
kubectl -n argocd get app <app> -o jsonpath='{.status.operationState}' | jq '.message, .phase, .startedAt, .finishedAt'
```

Common failure messages map to distinct causes — match the symptom
before touching anything:

- `ComparisonError: ... failed to load ...` — repo revision vanished
  (rebased/force-pushed branch): pin `targetRevision` to a tag or a
  branch that is not rewritten, never a moving SHA.
- `rpc error ... connection refused` to the repo server — network/SSO/
  token problem between Argo components, not the application.
- `one or more tasks failed waiting for ... hooks` → Phase 3.
- `Error render manifest ... cluster has no application current status` —
  controller namespace watch issue; inspect component health in Phase 2.

## Phase 2 — Health of the GitOps control plane

```bash
kubectl -n argocd get pods
# Each app's fate hangs off these three:
kubectl -n argocd logs deploy/argocd-application-controller --tail=200
```

Check specifically for: `CompareLive` errors flooding controller logs
(bad CRDs on mocked resources), repo-server restarts (manifest render
OOM — the commonly missed one: giant vendored charts in one app), and
`argocd-repo-server` pod restarts correlating with `Unknown` health on
*mathematically all* apps (control-plane problem, not fifteen app
problems).

## Phase 3 — Sync/hook ordering failures

A sync that hangs with wave resources stuck `Progressing` is almost
always a wave annotation problem.

```bash
# What is pending and why:
argocd app get <app>   # appears under "sync jobs" / resource status
kubectl -n <app-ns> get <kind> <name> -o jsonpath='{.metadata.annotations}' | jq 'keys'
```

Verify the implicit contract:

1. Hooks (`argocd.argoproj.io/hook: PreSync|Sync|PostSync`) complete
   before their wave's normal resources start — a failed job hook with a
   `backoffLimit: 0` wedges the sync until deleted or fixed.
2. Wave numbers (`argocd.argoproj.io/sync-wave: "N"`) must be **strings**
   and strictly increasing within a dependency chain; `"10"` < `"9"`
   lexicographically is a classic silent misorder.
3. A wave member that never becomes healthy (custom resource no health
   check) blocks the next wave: either add correct readiness, or split
   it into its own app.

Recovery for a wedged job: fix the job spec in Git (do not hand-edit the
running job — next sync would restore the broken one), then
`argocd app sync <app> --force --prune=false` in a maintenance window
only after the upstream cause is resolved.

## Phase 4 — Drift: is Git or the cluster lying?

```bash
argocd app diff <app>          # live vs target, per-resource
# Restrict to one object when the diff is pages long:
argocd app diff <app> --revision <sha>
```

Distinguish three drift species:

1. **Real external mutation** — someone `kubectl edit`ed/cliqued a field.
   Check the field's ownership trail first (below). Resolution: revert
   the change (or commit it — sometimes the mutation was the fix and the
   repo is wrong); never just `--force` sync over an unexplained mutation
   without knowing which side is desired.
2. **Mutating controllers** — route controllers (OpenShift's
   `route.openshift.io`, `ingress` shapers, cert-manager annotations,
   HPA `spec.replicas`) write fields the repo also declares, repeatedly.
   Resolution: remove the fields from Git as secrets of the cluster's
   authority, or configure `ignoreDifferences` (below).
3. **Manager conflict** — server-side apply field-manager fights.
   Resolution: Phase 5.

Field ownership forensics:

```bash
kubectl get <kind> <name> -n <ns> --show-managed-fields \
  | grep -A3 'manager:'        # who owns which fields
kubectl get <kind> <name> -n <ns> -o json | jq '.metadata.managedFields' | jq -r '.[] | .manager'
```

**`ignoreDifferences` discipline** (the anti-pattern guardrail): it is
for fields a running controller legitimately owns (HPA-managed
`spec.replicas`, defaulted nodePorts, generated TLS SANs). It is NOT a
fire extinguisher for drift you cannot explain — that hides real
mutation and belongs in an incident report, not the Application spec.

## Phase 5 — Server-side apply conflicts

```bash
kubectl apply -f app.yaml --server-side --field-manager=argocd  # what Argo does
# When it errors with "field is owned by a different manager":
kubectl get <kind> <name> -o json | jq -r '.metadata.managedFields[] | select(.fieldsV1 != null) | .manager'
```

Resolve by *choosing an owner*:

- Non-GitOps tooling that legitimately co-owns the object → list
  `.spec.syncOptions: ["ServerSideApply=true"]` and set
  `argocd.argoproj.io/compare-options: IgnoreExtraneous` per-resource or
  use managed-namespace metadata in overlays; last resort is
  conflating ownership in `ignoreDifferences` after the operator confirms
  the split is durable.
- One-off kubectl imperative drift → `kubectl apply set-last-applied -f
  app.yaml --create-annotation --dry-run=client -o yaml` to inspect,
  then let Argo's next SSA pass absorb it, or delete and let Git
  recreate.
- Helm hand-managed → migrate cleanly: fully uninstall the Helm release
  (keeping CRDs and webhook configs with `--keep-history` if needed) and
  let the Application adopt the resources, rather than letting two
  managers fight forever.

## Phase 6 — Rollback decisions

The GitOps rule: **the fix travels through Git.** Ranked choices:

1. **Git revert** (default): `git revert <bad-sha>` → normal sync rolls
   the cluster back while keeping audit trail and forward progress
   aligned with the repo. On Argo ApplicationSets referencing a branch,
   revert lands automatically; on tag pins, cut a new tag.
2. **`argocd app rollback <app> <rollback-id>`** — *break-glass only*:
   drives the app's `deploy` history ignoring the repo. It disables
   auto-sync on the app until re-enabled. Use when git revert + sync
   would be slower than an outage costs; commit the follow-up revert
   immediately after, or the next auto-sync re-applies the bad revision
   (the classic double-outage trap).
3. **Bottom-up delete/restore of one resource** — almost never right;
   escalate to incident response instead.

Check **before** rollback that `revisionHistoryLimit` (default 10) still
holds the target revision — long-lived apps often discover their wanted
rollback id has been garbage-collected; git-level revert (option 1) has
no such limit.

## Phase 7 — Argo Rollouts (canary analysis)

When progressive delivery is part of the pipeline:

```bash
kubectl argo rollouts status rollout/<name> -n <ns>   # if plugin available
kubectl -n <ns> get rollout <name> -o jsonpath='{.status}' | jq .
kubectl -n <ns> get analysistemplates,analysisruns
```

Degraded canaries: drain the failure analysis first
(`.status.conditions` on the AnalysisRun: metric name failing, its
configured failureLimit, and recent measurements) — `kubectl argo
rollouts abort <name>` is correct, but a fixed-threshold metric that
fires on a transient spike deserves a threshold fix in Git, not just an
aborted rollout.

## Phase 8 — Evidence capture

Before any recovery action, snapshot for the incident record and repo
notes:

```bash
argocd app get <app> > "evidence-${app}-$(date -u +%Y%m%dT%H%M%SZ).log"
kubectl -n argocd get app <app> -o yaml > "appcr-${app}.yaml"
argocd app diff <app> > "diff-${app}.log" 2>&1
```

## Cross-references

- `kubernetes-gitops-workflow` (platform-automation) — setup, repository
  layout, sync policy semantics (prune/selfHeal).
- `kubernetes-troubleshooting` — the Synced/Degraded path: pod crashes,
  resource exhaustion, image/network problems.
- `cluster-security-audit` — verifying post-incident that a privilege
  or exposure removed via GitOps actually stayed removed.

## Safety

- Never disable `selfHeal`/`prune` as a first response to drift — that
  widens the vulnerability window; diagnose the drift species first.
- Rollbacks and `--force` syncs are production-side effects: propose,
  wait for operator approval, execute, then immediately restore the
  repo-to-cluster invariant.
- All `argocd` CLI steps assume the CLI is present in the running image
  (`command -v argocd`); prefer the `kubectl -n argocd` equivalents
  shown when it is not.

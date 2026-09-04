---
name: kubernetes-deployment
description: "Production deployment workflow for Kubernetes and OpenShift: manifest structure (Deployment, Service, probes, resources, PodDisruptionBudget), Helm values layering and atomic upgrades with rollback, progressive delivery (canary vs blue-green, Argo Rollouts), rollout safety controls, and autoscaling with HPA/VPA. Use when asked to deploy to Kubernetes, build a Helm chart workflow, run a canary deployment, execute a production rollout, or define a release strategy."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Kubernetes Deployment

Operational reference for shipping a workload to Kubernetes/OpenShift. Cluster design: `kubernetes-architect`. Bootstrapping: `platform-automation`. Basics: `fundamentals`.

## Manifest Structure

A production workload is at minimum four objects: Deployment, Service, PodDisruptionBudget, and (on shared clusters) NetworkPolicy. Annotated baseline:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-api
spec:
  replicas: 3
  revisionHistoryLimit: 5                        # old ReplicaSets kept for rollback
  minReadySeconds: 10                            # hold Ready before rollout advances
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1                                # extra pods during update
      maxUnavailable: 0                          # never drop below spec.replicas
  selector:
    matchLabels:
      app.kubernetes.io/name: inference-api      # immutable; never put version here
  template:
    metadata:
      labels:
        app.kubernetes.io/name: inference-api
    spec:
      terminationGracePeriodSeconds: 60          # must exceed worst-case shutdown
      containers:
        - name: app
          image: registry.example.com/inference/api@sha256:REPLACE_WITH_DIGEST  # pin by digest
          ports:
            - containerPort: 8080
          startupProbe:                          # gates liveness during slow starts
            httpGet: { path: /healthz, port: 8080 }
            failureThreshold: 30                 # 30 x 10s = 5 min startup budget
            periodSeconds: 10
          readinessProbe:                        # drives Service endpoints
            httpGet: { path: /readyz, port: 8080 }
            periodSeconds: 5
            failureThreshold: 3
          livenessProbe:                         # restart on deadlock; keep cheap
            httpGet: { path: /healthz, port: 8080 }
            periodSeconds: 20
          resources:
            requests:                            # scheduler + HPA utilization base
              cpu: 500m
              memory: 1Gi
            limits:
              memory: 1Gi                        # limit == request avoids OOM inversion
---
apiVersion: v1
kind: Service
metadata:
  name: inference-api
spec:
  selector:
    app.kubernetes.io/name: inference-api        # matches pod labels, not Deployment
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: inference-api
spec:
  minAvailable: 2                                # drains/upgrades keep 2 pods
  selector:
    matchLabels:
      app.kubernetes.io/name: inference-api
```

Rules:

- Readiness and liveness endpoints must be distinct: a liveness check that hits a downstream (database, queue) restarts every pod when the downstream flaps.
- `maxUnavailable: 0` protects the rollout; the PDB protects node drains. Verify `ALLOWED DISRUPTIONS >= 1` (`kubectl get pdb`) before maintenance.

## Helm Workflow

### Values layering

Later value files win on key collision:

```bash
helm upgrade --install inference-api ./charts/inference-api \
  --namespace inference --create-namespace \
  -f charts/inference-api/values.yaml \          # base chart defaults
  -f deploy/env/prod.yaml \                      # env overrides
  --set image.digest=sha256:REPLACE_WITH_DIGEST  # per-release scalar injected by CI
  --atomic --timeout 10m
```

Reserve `--set` for scalars, never structured config. Keep secrets out of values files; reference a pre-created Secret by name.

### Review before apply

Render, lint, and diff before apply (helm-diff pinned):

```bash
helm template inference-api ./charts/inference-api -f deploy/env/prod.yaml > rendered.yaml
helm lint ./charts/inference-api -f deploy/env/prod.yaml
helm plugin install https://github.com/databus23/helm-diff --version v3.9.14
helm diff upgrade inference-api ./charts/inference-api -f deploy/env/prod.yaml
```

### Hooks and weights

Hooks run outside normal resource ordering; sequence them with `hook-weight` (ascending, ties by name):

```yaml
metadata:
  annotations:
    "helm.sh/hook": pre-upgrade
    "helm.sh/hook-weight": "-5"                  # runs before weight-0 hooks
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
```

Hooks get no `helm diff` coverage and no automatic rollback. Make them idempotent: a failed hook under `--atomic` reverts release resources but not hook side effects, so migrations must be reversible.

### Upgrade and rollback

```bash
helm history inference-api -n inference
helm rollback inference-api 3 -n inference --wait
```

`--atomic` (implied `--wait`) auto-rolls-back on failure; size `--timeout` to the startupProbe worst case. Rollback re-applies an old manifest but not CRDs, hook side effects, or volume data: pass the explicit revision from `helm history` and rehearse the drill (checklist below).

## Progressive Delivery

| Concern | Rolling update | Blue-green | Canary |
| --- | --- | --- | --- |
| Extra capacity | ~1 pod (surge) | 2x full fleet | 1-2 pods |
| Traffic shift | none (pod-proportional) | all-at-once | weighted %, header routing |
| Blast radius | medium | high (instant switch) | low, bounded by canary % |
| Rollback speed | slow re-roll | instant Service switch | set weight to 0 |
| Requires | any cluster | 2x quota | mesh or weighted ingress |

Rolling fits stateless services with solid readiness gates; blue-green buys instant cutover at 2x capacity; canary adds metric-gated promotion (error rate, p99). For automated metric-gated delivery use Argo Rollouts (`kubectl argo rollouts get rollout <name> --watch`, `promote`, `abort`). When a GitOps controller manages the rollout and drift or sync loops appear, debug with `gitops-troubleshooting`.

## Health and Rollout Safety

| Probe | Failure action | Use for |
| --- | --- | --- |
| startupProbe | delays liveness until success | slow starts (model load, cache warm) |
| readinessProbe | removes pod from endpoints | temporary unavailability |
| livenessProbe | restarts container | unrecoverable deadlock only |

`minReadySeconds` catches crash-loops that pass a single readiness check. Derive surge/unavailable from capacity: `maxUnavailable: 0` requires surge quota; on a full cluster use `maxSurge: 0, maxUnavailable: 1`.

Rollout operations (`kubectl`; on OpenShift substitute `oc`, same subcommands):

```bash
kubectl rollout status deploy/inference-api -n inference --timeout=600s
kubectl rollout history deploy/inference-api -n inference
kubectl rollout undo deploy/inference-api -n inference --to-revision=42
kubectl rollout pause deploy/inference-api -n inference   # halt mid-rollout for checks
kubectl rollout resume deploy/inference-api -n inference
kubectl get replicasets -n inference                      # old RS at 0, new RS at spec
```

A stuck rollout is usually a failing readiness probe (`kubectl describe pod`), surge-quota exhaustion, or a PDB blocking old-ReplicaSet scale-down.

## Autoscaling

HPA baseline:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: inference-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: inference-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70                 # % of requests.cpu; requests must be set
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300            # 5 min cooldown
      policies: [ { type: Percent, value: 25, periodSeconds: 60 } ]
    scaleUp:
      stabilizationWindowSeconds: 0              # react fast to load increase
      policies: [ { type: Pods, value: 4, periodSeconds: 60 } ]
```

Rules:

- HPA utilization is computed against `requests`, not limits; missing requests silently disable the metric.
- VPA: start in recommendation mode (`updateMode: "Off"`), read `kubectl get vpa inference-api-vpa -o jsonpath='{.status.recommendation}'`, then enable `Auto`. Never run HPA and VPA on the same metric; pair HPA-on-custom-metric with VPA-on-resource.
- Cluster autoscaler (or Karpenter) provisions nodes only if scaled-up pod requests fit a node group below its max size; strict PDBs block scale-down drains.
- An HPA must target the Rollout object, not its underlying Deployment, when Argo manages the rollout.

## Production-Readiness Checklist

Gate every first production release on:

- [ ] Distinct readiness/liveness endpoints; startupProbe if startup exceeds 30s; probes verified under load.
- [ ] `resources.requests` set for every container; memory limit equals request for latency-critical services.
- [ ] PDB present with `ALLOWED DISRUPTIONS >= 1`, verified via `kubectl drain --dry-run=server`.
- [ ] NetworkPolicy restricts ingress/egress to expected peers; audit with `cluster-security-audit`.
- [ ] Image pinned by digest (`image@sha256:...`); tag-only references rejected in CI.
- [ ] Rollback drill in staging: `helm rollback` / `kubectl rollout undo` timed, observed returning to Ready.
- [ ] HPA load-tested; scale-down stabilization validated against real traffic shape.
- [ ] `terminationGracePeriodSeconds` matches observed shutdown; app handles SIGTERM and drains in-flight requests.

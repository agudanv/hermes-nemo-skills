---
name: devops-troubleshooter
description: "Rapid structured diagnosis of DevOps failures: CI/CD breaks, Kubernetes/OpenShift deploy failures, environment drift, container build issues. Covers failing stages, flaky tests, dependency resolution, registry auth, ImagePullBackOff, CrashLoopBackOff, pending pods, manifest diffing, cache busting, and lockfile conflicts. Use when a pipeline failed, deploy broken, environment drift suspected, CI failing, or you need to debug a broken deployment."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# DevOps Troubleshooter

Operational runbook for evidence-driven diagnosis of DevOps failures on Linux, with `kubectl`, `oc`, `helm`, and GitOps CLI access. Install missing CLIs as pinned release binaries, never via curl-to-shell installers.

## Method: Symptom to Verified Fix

Follow the loop strictly; gather evidence before touching state.

1. Symptom. One sentence: what fails, since when, blast radius (users, environments, pipelines). Capture exact error text and exit code. Ask first: what changed? Recent deploys, config edits, cert or token rotations, node maintenance, upstream incidents.
2. Hypothesis. Rank 2-3 candidate causes by likelihood times cost to check; run the cheapest discriminating test first. Always keep "the last change caused this" on the list.
3. Evidence. One read-only command per hypothesis, full output captured. Never mutate state while gathering; mutation contaminates the signal.
4. Minimal fix. Smallest reversible change, one variable at a time. Snapshot state first (see Evidence Discipline).
5. Verify. Define success criteria before applying: exit code 0, rollout complete, probe passing, metric at baseline. Watch a 5-15 minute regression window.

Time-box: 15 minutes without new evidence on a hypothesis means abandon and re-rank. Two failed loops -> escalate.

## CI/CD Breaks

### Reading build logs

Pull the full log first; never diagnose a pasted tail.

```bash
# GitLab
glab ci trace <job-id> > build.log
# GitHub Actions
gh run view <run-id> --log-failed > build.log
# Jenkins
jenkins-cli console <job-name> <build-number> > build.log
```

Then reduce:

```bash
grep -nE 'ERROR|FAIL(ED)?|fatal:|panic:|Traceback' build.log
grep -nE 'exit code [1-9]|Exit status [1-9]' build.log
grep -nE 'OOMKilled|No space left|Segmentation fault|Killed' build.log
```

Exit codes:

| Code | Meaning | Typical cause |
| --- | --- | --- |
| 0 | success | - |
| 1 | general error | test or assertion failure |
| 124 | `timeout` expired | hung step, slow network |
| 126 | not executable | missing `+x`, wrong shebang |
| 127 | command not found | image drift, PATH change |
| 137 | SIGKILL (128+9) | OOM in runner, cgroup limit |
| 143 | SIGTERM (128+15) | job cancelled, runner evicted |

### Failing stages

- Reproduce locally in the runner image: `docker run --rm -it <ci-image> bash`.
- Diff last green vs first red job: image tag, runner version, env var names. Exit 137 on a stable job is runner OOM; raise memory or split the step.

### Flaky tests

Definition: same commit, rerun passes. Confirm by re-running the exact failed SHA with no changes.

```bash
for i in $(seq 1 20); do ./run-test.sh <name> && echo PASS || echo "FAIL run $i"; done
```

Root causes by frequency: test-order dependence, wall-clock assumptions, shared state (DB rows, files, fixed ports), runner contention, unmocked network. Mitigate by pinning seeds, using ephemeral ports, isolating state per test, and quarantining with a retry budget of exactly one; unlimited retries hide regressions.

### Dependency resolution failures

- npm: `npm ls <pkg>` finds the conflict path; `npm ci` reproduces CI exactly; pin in `package.json` rather than leaving `--force` or `--legacy-peer-deps` in place.
- pip: `pip install --dry-run -r requirements.txt` previews resolution; `pip check` after install; constrain the conflicting transitive dependency.
- Go: `go mod tidy`, then `git diff go.mod go.sum`; `go mod verify`.
- Intermittent 401/403 from artifact proxies: stale credentials in `.npmrc`, `.pip.conf`, or CI variables. Rotate via the CI secret store; reference variable names (`NPM_TOKEN`, `PIP_INDEX_URL`), never values.

### Registry auth

```bash
# List configured registries (keys only, never print secrets)
jq -r '.auths | keys[]' "$DOCKER_CONFIG/config.json"
# Inspect a Kubernetes pull secret
kubectl get secret <pull-secret> -n <ns> \
  -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d | jq -r '.auths | keys[]'
# Prove auth works with a minimal pull
docker pull <registry>/<repo>:<tag>
```

Frequent causes: expired robot token, SSO expiry, CI variable overwritten at group level, registry IP allowlist change.

## Deploy Failures

### Rollout triage and rollback

```bash
kubectl rollout status deploy/<app> -n <ns> --timeout=60s
kubectl rollout history deploy/<app> -n <ns>
kubectl rollout undo deploy/<app> -n <ns> --to-revision=<n>
kubectl rollout pause deploy/<app> -n <ns>   # stop the bleeding while diagnosing
# OpenShift DeploymentConfig
oc rollout status dc/<app> -n <ns>
oc rollout history dc/<app> -n <ns>
oc rollback <app> -n <ns> --to-version=<n>
```

### ImagePullBackOff

`kubectl describe pod` Events confirm the cause. Causes in frequency order:

| Cause | Check |
| --- | --- |
| Tag does not exist (typo, failed push) | `crane ls <registry>/<repo>` or `docker manifest inspect <img>:<tag>` |
| Missing or expired pull credentials | pull secret exists, not expired, attached to the right ServiceAccount |
| Registry unreachable from nodes | node DNS, egress proxy, NetworkPolicy |
| Registry rate limit | anonymous pull quota (for example Docker Hub); authenticate pulls |
| Digest mismatch after re-tag | pull by digest: `<img>@sha256:...` |

### CrashLoopBackOff first steps

```bash
kubectl logs <pod> -n <ns> -c <container> --previous   # logs of the crashed run
kubectl get events -n <ns> --sort-by=.lastTimestamp | tail -30
kubectl describe pod <pod> -n <ns> | sed -n '/Last State/,/Ready/p'
```

Map `lastState.terminated.reason` to action:

| Reason | Meaning | First action |
| --- | --- | --- |
| `Error`, exit 1 | app config or startup failure | read `--previous` logs; check env vars, ConfigMap, mounted secrets |
| `OOMKilled` | memory limit hit | compare usage to limit; raise the limit or fix the leak |
| `Completed` | main process exited 0 | entrypoint should not exit; check command and args |
| probe failure | liveness kills a slow-but-healthy app | check startup time; add a `startupProbe` or lengthen `initialDelaySeconds` |

A missing `optional: false` env or secret key blocks pod creation; it shows in Events as `secret "x" not found`, never in logs.

### Pending pods

```bash
kubectl describe pod <pod> -n <ns> | sed -n '/Events/,$p'
kubectl describe node <node> | sed -n '/Allocated resources/,/Events/p'
kubectl get pvc -n <ns>
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
```

Causes: requests exceed allocatable capacity, taints without tolerations, unsatisfiable nodeSelector or affinity, unbound PVC (storage class missing or provisioner down), quota exhaustion (`kubectl describe resourcequota -n <ns>`).

## Environment Drift

### Config skew between environments

```bash
# Compare kustomize overlays
diff -u <(kustomize build overlays/dev) <(kustomize build overlays/prod)
# Compare rendered Helm output against live cluster state
helm template <release> <chart> -n <ns> -f values-<env>.yaml | kubectl diff -f -
# Compare local manifests against live
kubectl diff -f manifests/ -n <ns>
```

For ConfigMap or Secret skew across clusters, compare hashes, never values:

```bash
kubectl --context dev get cm <name> -n <ns> -o yaml | sha256sum
kubectl --context prod get cm <name> -n <ns> -o yaml | sha256sum
```

### Secret rotation failures

- Expired TLS: `kubectl get secret <tls-secret> -n <ns> -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -dates`.
- Zero-outage rotation: create new secret version, update consumers, rolling-restart (`kubectl rollout restart deploy/<app> -n <ns>`), verify, then revoke the old credential. Apps that cache credentials at startup need a restart; canary one pod first.

### Git vs cluster (GitOps)

```bash
argocd app get <app> --refresh        # sync status and conditions
argocd app diff <app>                 # desired vs live
argocd app history <app>              # recent syncs
flux get kustomizations -n <ns>       # Flux equivalent
flux diff kustomization <name> -n <ns>
```

`OutOfSync` causes: manual `kubectl` edits on a GitOps-managed resource, failed sync (read `.status.conditions`), `ignoreDifferences` masking real drift, or a commit on the wrong branch or environment directory. Controller internals go to `gitops-troubleshooting`.

## Build Issues

### Layer cache busting

- Order Dockerfile instructions least-to-most volatile: base, system packages, lockfiles, dependency install, source copy.
- `COPY package*.json ./ && npm ci` before `COPY . .`, so source-only changes reuse the dependency layer.
- A wrong or missing `.dockerignore` busts the cache: `COPY . .` hashes the whole context, including `.git`.
- `docker buildx build --progress=plain .` shows exactly which step cache-misses; a one-off `docker build --no-cache` isolates stale-layer problems from code problems.
- CI: key `--cache-from`/`--cache-to` (registry type) on a stable ref; a cold cache after a runner image change looks like a code regression.

### Base-image CVE bumps

- Rebuild with `docker build --pull`; without it a stale local base persists silently.
- Scan before promoting: `trivy image <img>:<tag>` or `grype <img>:<tag>`; gate on severity per policy.
- Pin bases by digest (`FROM <img>@sha256:...`) and bump deliberately in a reviewable PR; mutable tags make builds non-reproducible and CVE state untraceable.
- Green yesterday, red today, zero code changes: the base image or the vulnerability database moved, not your code.

### Lockfile conflicts

- Never hand-merge `package-lock.json`, `yarn.lock`, `poetry.lock`, `Pipfile.lock`, `go.sum`. Take one side and regenerate (`npm install`, `yarn install`, `poetry lock --no-update`, `go mod tidy`) on a pinned toolchain, and commit manifest plus lock together. Cross-version lockfiles (different Node or Python majors) conflict in phantom ways; pin the toolchain in CI and the dev container.

## Evidence Discipline

- Log everything: `script -a troubleshoot-$(date -u +%Y%m%dT%H%M%SZ).log` before starting, or paste command plus output into the ticket as you go. Postmortems die from missing evidence.
- Record constants: UTC timestamps, cluster and context (`kubectl config current-context`), namespace, app version or image digest, last known good time.
- Snapshot before mutating: `kubectl get deploy <app> -n <ns> -o yaml > backup-<app>-<ts>.yaml`. Every fix must be reversible to this snapshot.
- Never fix in production what you cannot reproduce in staging. If reproduction is impossible, gate the change behind a canary or feature flag with a defined rollback trigger.
- One change per verify cycle; simultaneous changes make verification meaningless.
- Record root cause, fix, and the discriminating command that proved it. That trio seeds a runbook (see `runbook-creator`).

## Escalation

| Situation | Route to |
| --- | --- |
| Production-impacting or user-facing outage | `incident-responder`, `incident-response` |
| Argo CD or Flux sync failures, drift loops, controller internals | `gitops-troubleshooting` |
| Node-level or control-plane failures beyond app scope | `kubernetes-troubleshooting`, `failure-analysis` |
| Post-incident: codify the fix as a runbook | `runbook-creator` |
| Skill building after the fire is out | `devops-learning-path` |

Escalate early with the evidence log attached: symptom, hypotheses tried, commands and outputs, blast radius.

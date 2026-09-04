---
name: cluster-security-audit
description: "Audit the live security posture of a Kubernetes or OpenShift cluster from the command line: inventory privileged workloads, review OpenShift Security Context Constraints, inspect RBAC for escalation paths, check PodSecurity Admission labels, measure NetworkPolicy coverage, and flag secret-handling risks. Use when asked to perform a security review or audit of a cluster, check SCCs, find over-privileged service accounts, or assess namespace isolation."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Cluster Security Audit

A read-mostly workflow for inspecting the security posture of a running
Kubernetes or OpenShift cluster with `kubectl`/`oc` and producing a
prioritized findings report. This skill audits what is already deployed;
for writing new policies (NetworkPolicy, Pod Security Standards, RBAC
design) use the `kubernetes-k8s-security-policies` skill in
`platform-automation`, and pair its remediation patterns with this
audit's findings.

## When to use

- "Security review", "audit this cluster/namespace", "who can do what here"
- Onboarding an existing cluster into managed scope
- Post-incident verification that a privilege was actually removed
- Pre-production gate before exposing a service

## Rules of engagement

1. **Read-only first.** Every command in the discovery phase is a `get`,
   `describe`, or `auth can-i`. No audit step mutates the cluster.
2. **Changes are proposals.** Remediation goes into the findings report
   (resource, finding, severity, suggested fix). Apply changes only after
   the operator approves, and prefer a GitOps repo commit over imperative
   `kubectl edit` so the fix is reviewable and revertible.
3. **Never exfiltrate secret values.** Audits report secret *names,
   types, and mounting workloads* — never print or store the data. When
   in doubt, use `kubectl get secret -o yaml` fields selectively (`.type`,
   `.metadata.name`, key names only: `-o jsonpath='{.data}' | tr ',' '\n' | cut -d: -f1`).
4. **Scope explicitly.** Record the namespaces, cluster, date, and
   identity (`kubectl auth whoami` / `oc whoami`) in the report header.

## Phase 1 — Workload attack-surface census

Start with what runs, where it runs from, and with which privileges.

```bash
# All pods that request privileged or host access
kubectl get pods -A -o json | jq -r '.items[] | select(
  .spec.containers[].securityContext.privileged // false or
  .spec.hostNetwork // false or
  .spec.hostPID // false or
  .spec.hostIPC // false) | "\(.metadata.namespace)/\(.metadata.name)"' | sort -u

# Containers running as root (UID 0 or missing runAsNonRoot)
kubectl get pods -A -o json | jq -r '.items[] | . as $p |
  .spec.containers[] | select(
    ((.securityContext.runAsNonRoot // $p.spec.securityContext.runAsNonRoot) // true) | not
  ) | "\($p.metadata.namespace)/\($p.metadata.name)  container=\(.name)"'

# HostPath volumes and hostPort bindings
kubectl get pods -A -o json | jq -r '.items[] |
  (.spec.volumes[]? | select(.hostPath) | "hostPath \(.hostPath.path) on \(.metadata.namespace)/\(.metadata.name)"),
  (.spec.containers[].ports[]? | select(.hostPort) | "hostPort \(.hostPort) on \(.metadata.namespace)/\(.metadata.name)")' | sort -u

# Ability to escalate: absent allowPrivilegeEscalation=false is itself a finding
kubectl get pods -A -o json | jq -r '.items[] | select(
  .spec.containers[].securityContext.allowPrivilegeEscalation != false) |
  "\(.metadata.namespace)/\(.metadata.name)"'
```

On OpenShift, most of the above is constrained by SCCs, so expect fewer
hits than on vanilla Kubernetes — and treat every hit as high severity,
because something had to opt the workload in.

## Phase 2 — OpenShift SCC audit

Security Context Constraints decide what a pod may request. The audit
answers two questions: which SCCs exist and do workloads map to the
least-privileged one that still works?

```bash
# Inventory (default set: anyuid, hostaccess, hostmount-anyuid, hostnetwork,
# node-exporter, nonroot, privileged, restricted, restricted-v2)
oc get scc

# Who *can* use the dangerous ones: anyuid, privileged, hostaccess
oc adm policy who-can use scc anyuid
oc adm policy who-can use scc privileged

# What SCC a given pod/service account would actually get (labels resolved)
oc adm policy scc-review -n <namespace> -z <serviceaccount>

# Check a specific user/SA against a specific SCC before granting it
oc adm policy scc-subject-review -n <namespace> -z <serviceaccount> privileged
```

Findings to record:

| Pattern | Severity | Notes |
|---|---|---|
| `system:cluster-admins` outside break-glass | High | Verify each member is intentional |
| RoleBindings to `scc` `privileged`/`anyuid` for app namespaces | High | Prefer `restricted-v2` + targeted UID ranges |
| `privileged` SCC used by non-DaemonSet workloads | High | DaemonSets need review, not auto-pass |
| Namespace default SA with `anyuid` | Med | First pod gets root-capable runtime |

## Phase 3 — RBAC audit

```bash
# What can the current (or a target) identity do — includes delegated rights
kubectl auth can-i --list -n <namespace>
kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa>

# Bindings that grant cluster-admin (built-ins first, then strays)
kubectl get clusterrolebindings -o json | jq -r '.items[] |
  select(.roleRef.name == "cluster-admin") |
  "\(.metadata.name): \(.subjects // [] | map(.kind + "/" + .name) | join(", "))"'

# Wildcard verbs/resources — the silent superusers
kubectl get clusterroles,roles -A -o json | jq -r '.items[] |
  .rules[]? | select((.verbs // []) | index("*") or (.resources // []) | index("*")) |
  "\(.roleKind // "Role") \(.roleNamespace // "cluster")/\(.roleName // "?")"'

# Escalation verbs: escalate/bind/impersonate outside admin groups
kubectl get clusterroles,roles -A -o json | jq -r '.items[] |
  .rules[]? | select((.verbs // []) | (index("escalate") or index("bind") or index("impersonate"))) |
  "escalation-verb in \(.roleNamespace // "cluster")/\(.roleName // .metadata.name // "?")"'
```

Interpretation rules:

- `verbs: ["get","list"]` on `secrets` in a namespace an SA shouldn't
  read is a data-exfiltration path — treat as High.
- A Role that can `bind` Roles can self-amplify. Trace what it can bind.
- `impersonate` on users/groups enables privilege spoofing — reserve
  for audit tooling, scope to specific users/groups, never `*`.

## Phase 4 — PodSecurity Admission labels

```bash
# Sweep enforcement levels across all namespaces
kubectl get namespaces -o json | jq -r '.items[] | "\(.metadata.name): enforce=\(.metadata.labels["pod-security.kubernetes.io/enforce"] // "-") audit=\(.metadata.labels["pod-security.kubernetes.io/audit"] // "-")"'
```

Evaluate: every namespace should carry an explicit `enforce` level
(`baseline` minimum for infra, `restricted` for app workloads). On
OpenShift, SCCs remain the operative control — PodSecurity labels should
not contradict the SCC strategy (document which control is authoritative).
Gaps are Medium findings; propose the staged rollout `warn → audit →
enforce` per namespace in the report.

## Phase 5 — NetworkPolicy coverage

```bash
# Which namespaces have any NetworkPolicy
kubectl get ns --no-headers | while read ns _; do
  printf '%-30s %s\n' "$ns" "$(kubectl get networkpolicy -n "$ns" --no-headers 2>/dev/null | wc -l | tr -d ' ') policies"
done

# Exposed Service inventory (external entry points)
kubectl get svc -A -o wide | grep -E 'LoadBalancer|NodePort'
```

A namespace with **zero** NetworkPolicies is a flat network — every pod
can reach every pod cluster-wide (and often every node, via hostPorts).
Record per-namespace: policy count, whether a `default-deny` ingress
policy exists, and whether exposed Services have restrictive policies.
When remediating, author the policies with `k8s-security-policies` and
roll out by first adding allow policies, then the default-deny.

## Phase 6 — Secret hygiene

```bash
# Census by type; abnormal growth of kubernetes.io/service-account-token is noise,
# growth of Opaque in app namespaces deserves a review of what they unlock
kubectl get secrets -A -o json | jq -r '.items[] | "\(.type)"' | sort | uniq -c

# Secrets exposed as environment variables (visible via /proc, crash dumps, exec)
kubectl get deploy,sts,ds -A -o json | jq -r '.items[] |
  . as $w | .spec.template.spec.containers[] |
  (.envFrom[]? | select(.secretRef.name != null) |
     "envFrom: \($w.metadata.namespace)/\($w.metadata.name) -> \(.secretRef.name)"),
  (.env[]? | select(.valueFrom.secretKeyRef != null) |
     "env:      \($w.metadata.namespace)/\($w.metadata.name) -> \(.valueFrom.secretKeyRef.name)")'

# Long-lived service-account tokens bound to pods (legacy auto-mount)
kubectl get pods -A -o json | jq -r '.items[] |
  select(.spec.automountServiceAccountToken // true) |
  "\(.metadata.namespace)/\(.metadata.name)"'
```

Report secret *references* only, never contents. Findings: env-injected
credentials without a rotation story; missing workspaces RBAC boundary
around secret reads; projected-token migration opportunities for
long-lived `service-account-token` secrets.

## Phase 7 — Report

Emit markdown with this shape (keep it operator-consumable):

```markdown
# Security audit — <cluster> — <date> — auditor <identity>
Scope: <namespaces or "cluster-wide">

## Findings
| Severity | Location | Finding | Suggested remediation |
|---|---|---|---|
| High | ns/foo deploy/bar | privileged: true without justification | drop to restricted-v2; justification missing |

## Verified-good
- <controls confirmed healthy — matters as much as the gaps>

## Recommended follow-ups
- <ordered list, each mapped to a suggested change and review path>
```

Severity guide: **High** = privilege escalation, exfiltration, or exposure
path; **Medium** = missing/weak isolation likely to become High; **Low** =
hygiene/mismatch (labels, defaults). Every High finding gets a suggested
fix command or diff the operator can review before running.

## Cross-references

- `kubernetes-k8s-security-policies` (platform-automation) — authoring
  the NetworkPolicy/PSS/RBAC remediations this audit proposes.
- `kubernetes-troubleshooting` — when a finding turns out to be a
  workload failure rather than a policy gap.
- `openshift-llm-deploy` — example of the restricted guardrails expected
  on inference workloads in this environment.

## Safety

All commands above are read-only. The audit exists to *reduce* privilege
and exposure; any remediation that grants rights, opens ports, or edits
RBAC is an operator-approved follow-up, never an in-audit side effect.

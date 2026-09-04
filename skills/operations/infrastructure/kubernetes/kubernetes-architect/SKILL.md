---
name: kubernetes-architect
description: "Design Kubernetes and OpenShift cluster and platform architecture: HA control plane and etcd topology with latency budgets, node pools, taints/tolerations/affinity, availability-zone spread, CNI selection (Calico, Cilium, OVN-Kubernetes), Ingress vs Gateway API, service mesh adoption decisions, storage classes and RWO/RWX tradeoffs, multi-tenancy models (namespace-per-team vs cluster-per-team), OpenShift SCC/Routes specifics, and capacity planning with overcommit ratios and cluster autoscaling. Use when asked to design a cluster, review Kubernetes architecture, plan an HA topology, evaluate multi-tenancy, choose a CNI, or run capacity planning for a new or existing platform."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Kubernetes Architect

Decisions and tradeoffs for designing Kubernetes and OpenShift clusters: control
plane topology, networking, storage, tenancy, and capacity, ending in a signed-off
decision record. This skill is the decision layer: execution is
`kubernetes-deployment`, baseline concepts are `fundamentals`, reusable workload
shapes are `kubernetes-patterns`.

## Design-Review Workflow

Run every engagement as a four-step loop. Do not skip to options before constraints
are written down; most bad cluster designs are constraint-discovery failures, not
technology-selection failures.

1. Requirements: workload inventory (stateless, stateful, batch, GPU), expected QPS
   and object counts, latency SLOs, data residency, team count and skill level,
   upgrade cadence tolerance.
2. Constraints: budget, cloud vs bare metal, existing network (MTU, BGP), air-gap or
   proxy needs, hardware refresh cycle, regulatory isolation boundaries.
3. Options table: for each major decision (topology, CNI, storage, tenancy) list 2-4
   candidates with cost, operational burden, and risk columns. Reject with reasons,
   not silently.
4. Decision record: one page per decision - context, options considered, decision,
   consequences, revisit trigger. Store next to the platform repo so
   `gitops-troubleshooting` investigations can trace why the cluster looks the way
   it does.

### Design deliverable checklist

- [ ] Control plane topology diagram (AZ layout, etcd placement, LB for API server)
- [ ] Node pool inventory with taints, labels, and sizing per pool
- [ ] CNI choice with datapath, policy, and observability justification
- [ ] Ingress/Gateway and service-mesh position (adopt, defer, or reject, with reason)
- [ ] Storage class matrix (workload type to class to backup/snapshot strategy)
- [ ] Tenancy model with RBAC, quota, and NetworkPolicy templates
- [ ] Capacity model: headroom targets, overcommit ratios, autoscaling plan
- [ ] Upgrade and failure-domain runbook hooks (`kubernetes-patterns` HA shapes)
- [ ] Security posture baseline to hand to `cluster-security-audit` after build

## Cluster Topology

### HA control plane

- Minimum 3 control plane nodes for quorum; 5 only when you need to survive two
  simultaneous failures or span 3+ failure domains with room. Never 2 or 4 (even
  numbers worsen quorum math).
- Spread across 3 availability zones. A 3-node plane tolerates loss of one full AZ.
- Stacked etcd (co-located with API servers) is fine up to roughly 500 nodes or
  moderate churn. External etcd earns its operational cost past that, or when API
  server and etcd must scale/patch independently.
- Front the API server with a stable L4 virtual IP (keepalived/haproxy on-prem, cloud
  LB in cloud). Point kubeconfig, kubelets, and controllers at the VIP, never at a
  single member.

### etcd sizing and latency budgets

| Metric | Budget | Notes |
| --- | --- | --- |
| WAL fsync p99 | < 10 ms | Sustained higher values mean slow disks; put etcd on dedicated NVMe |
| Backend commit p99 | < 25 ms | Watch `etcd_disk_backend_commit_duration_seconds` |
| RTT between members | < 10 ms same region | Cross-region etcd is not supported; stretch within a metro only |
| DB size quota | 2 GiB default, 8 GiB hard max | Alarm at ~80 percent; defrag after compaction to reclaim |
| Heartbeat / election | 100 ms / 1000 ms defaults | Raise only for high-latency links, never below defaults |

Defragment on a schedule (weekly is typical) after history compaction; a fragmented
3 GiB store may hold only 800 MiB of live data. Take periodic snapshots and verify
restores - an untested snapshot is not a backup.

### Node pools, taints, and affinity

- Separate pools by failure/upgrade blast radius and workload class: `system`
  (ingress, DNS, monitoring), `general` (stateless services), `stateful` (storage-
  pinned), `gpu` (accelerated), `batch` (preemptible/spot).
- Taint specialized pools so only intended workloads schedule:
  `gpu=true:NoSchedule`, `storage=local:NoSchedule`. Keep the system pool tainted
  `CriticalAddonsOnly` or equivalent so tenant workloads never crowd out DNS.
- nodeAffinity for soft steering (prefer the SSD pool for databases),
  topologySpreadConstraints keyed on `topology.kubernetes.io/zone` for hard AZ
  spread, podAntiAffinity so replicas never share a node.
- Reserve N+1 capacity per AZ so node or zone loss reschedules without queueing.

## Networking

### CNI comparison

| Dimension | Calico | Cilium | OVN-Kubernetes |
| --- | --- | --- | --- |
| Datapath | iptables or eBPF; overlay (VXLAN) or native routing with BGP | eBPF native; overlay or native; kube-proxy replacement | OVS-based Geneve overlay; the OpenShift default |
| NetworkPolicy | Full; plus GlobalNetworkPolicy and staged policies | Full; L7 (HTTP/DNS) policy and FQDN egress rules | Full v1 policy; AdminNetworkPolicy for cluster-wide baseline |
| Egress IP / gateway | Egress gateway (namespaced egress IPs) | Egress Gateway with stable source IPs | Native EgressIP per namespace; primary use case in OpenShift |
| Encryption | WireGuard or IPsec | WireGuard or IPsec, transparent | IPsec (opt-in, cluster-wide) |
| Observability | Flow logs, Typha scaling metrics | Hubble flow UI, L7 visibility, service map | OVN/OVS flow dumps; solid but less turnkey |
| Best fit | BGP-friendly bare metal, mixed Windows/Linux, mature policy needs | eBPF shops wanting kube-proxy-less scale and L7 policy | OpenShift, or where egress IP and AdminNetworkPolicy are required |

Cilium when eBPF observability and kube-proxy replacement drive the design; Calico
when BGP fabric integration or Windows nodes are in scope; OVN-Kubernetes on
OpenShift unless a documented requirement says otherwise - replacing the default CNI
multiplies upgrade risk.

### Ingress vs Gateway API

- Ingress: fine for simple HTTP host/path routing; annotation soup for anything
  advanced (timeouts, canary, header rewrites differ per controller).
- Gateway API: role-split resources (GatewayClass/Gateway for platform team,
  HTTPRoute for app teams), portable traffic splitting, and a real spec for L4.
  Choose Gateway API for new platforms; keep Ingress for legacy or single-team
  clusters where the added CRDs buy nothing.

### Service mesh: adoption decision

Adopt a mesh (Istio, Linkerd) only when at least two of these are hard requirements:
policy-mandated mTLS with per-workload identity, L7 traffic management the ingress
layer cannot express, or cross-cluster service discovery. Do NOT adopt when the
driver is observability alone - metrics plus eBPF flow data cover it cheaper; when
the team is smaller than the mesh's operational surface (a second control plane to
upgrade, debug, and capacity-plan); or when the sidecar tax exceeds ~10 percent of
node budget.

### DNS and CoreDNS

- Tune `ndots: 2` (default 5) on pods resolving mostly external names; this cuts
  search-domain expansion queries 4-5x.
- NodeLocal DNSCache once CoreDNS exceeds a few thousand QPS per node or conntrack
  pressure from UDP DNS flows appears.
- 1 replica per ~8-16 nodes with AZ anti-affinity; `cache 30` or higher for stable
  records; `autopath` only with understood memory tradeoffs.
- Keep `negative_ttl` low; long negative caching delays headless endpoint failover.

## Storage

- One StorageClass per durability/performance tier, named by contract not product:
  `fast-local`, `replicated-block`, `shared-file`. Exactly one default class.
- RWO block: best performance and simplest failover, ideal for databases and queues.
  RWX file: needed when pods share content, but adds a network hop, throughput
  ceiling, and a new failure domain; prefer app-level replication (object storage,
  Kafka) over RWX when possible.
- VolumeSnapshots are crash-consistent copies, not backups: real backups leave the
  cluster (Velero, array replication) and are restore-tested quarterly.
- TopoLVM: local NVMe with LVM thin provisioning; near-bare-metal IOPS for
  databases, node-pinned volumes, so replicate at the app layer and document
  node-loss recovery.
- ODF (Ceph-backed): RBD for RWO, CephFS for RWX, RGW for S3; budget 3+ dedicated
  storage nodes, replication factor 3, and per-node CPU/RAM overhead. One API for
  block/file/object on-prem; TopoLVM when raw latency beats flexibility.

## Multi-Tenancy

### Namespace-per-team vs cluster-per-team

| Dimension | Namespace-per-team | Cluster-per-team |
| --- | --- | --- |
| Isolation | Soft: RBAC + NetworkPolicy + ResourceQuota; shared API server and etcd | Hard: separate control plane, etcd, nodes, credentials |
| Blast radius | A bad actor or noisy team can degrade shared control plane | Contained to one cluster; control plane survives |
| Cost | Lowest; amortized control plane and bin-packing | Highest; control plane tax per team, worse utilization |
| RBAC complexity | Grows combinatorially; needs policy-as-code (RBAC templates, admission policies) | Simple per cluster; complexity moves to fleet management |
| Upgrade cadence | Single train; all teams move together | Per-cluster windows; version skew across fleet must be managed |
| Best for | Internal product teams, dev/test, homogeneous trust | Regulated workloads, hard customer isolation, hostile or untrusted tenants |

Hybrid is common: shared clusters per trust tier (prod regulated, prod standard,
non-prod), namespaces per team inside each. Whatever the model, enforce per-namespace
ResourceQuota, LimitRange, default-deny NetworkPolicy, and Pod Security Standards
from day one - retrofitting any of these into a live shared cluster is painful.

## OpenShift Specifics

- SCC vs PSA: OpenShift enforces Security Context Constraints by default
  (`restricted-v2` mirrors the PSS restricted profile), integrated with service
  accounts and router/registry workloads. Prefer SCC on OpenShift; add Pod Security
  Admission labels only as a portable supplement, and never enforce both against
  the same pods without checking for conflicting denials.
- Routes vs Ingress: Routes are first-class, served by the HAProxy router, with
  edge, re-encrypt, and passthrough termination plus sharding, per-route timeouts,
  and session affinity. Ingress objects are converted and work but expose fewer
  knobs. Routes for re-encrypt or passthrough; either for plain edge TLS.
- OVN-Kubernetes is the default and supported CNI: NetworkPolicy, egress IP, egress
  firewall, and multicast are native. Plan no CNI swap without a written
  requirement forcing it.
- Diagnostics: `oc adm must-gather` (support bundle), `oc adm inspect <resource>`
  (API tree snapshot), `oc adm node-logs <node> -u kubelet` (journald without SSH),
  `oc adm top nodes/pods` (capacity), `oc adm drain` (cordon+evict). Check `oc get
  co` first - degraded ClusterOperators explain most platform symptoms.

## Capacity Planning

### Requests, limits, and overcommit

- Set requests from observed p95 usage plus 20-30 percent headroom; review
  quarterly or run a VPA in recommendation mode.
- CPU: limits optional on latency-sensitive services (throttling spikes tails);
  use `static` CPU management and Guaranteed QoS for hot paths. Memory: always set a
  limit at or above request - memory overcommit OOM-kills instead of throttling.
- Overcommit (sum of requests / allocatable): CPU 2:1 to 4:1 for web/batch mixes,
  memory 1:1 to 1.5:1; GPU and stateful pools 1:1.
- Keep cluster-wide spare allocatable >= largest node so autoscaling keeps up and
  node loss never strands pods Pending.

### Autoscaling

- Cluster Autoscaler: stable predefined node groups; scales on pending-pod
  pressure.
- Karpenter: heterogeneous, fast-changing demand; provisions just-in-time instance
  shapes per pending pod, consolidates underused nodes, handles spot with graceful
  interruption. Karpenter on AWS cost-sensitive fleets; Cluster Autoscaler where
  simplicity or non-AWS providers dominate.
- Pair with HPA, plus KEDA for event-driven workloads; never drive nodes and pods
  off the same lagging metric without testing the feedback loop under load shedding.

### Sizing signals to re-run this design

Revisit the design when etcd DB passes 60 percent of quota, API server p99 LIST
latency passes 1 s, CoreDNS exceeds 70 percent CPU at peak, any pool sustains above
65 percent allocation, or team count doubles past the tenancy model.

## Related Skills

- `fundamentals`: baseline Kubernetes concepts this design assumes
- `kubernetes-patterns`: reusable HA and workload shapes referenced by topology choices
- `kubernetes-deployment`: executes the manifests, rollouts, and rollback this design specifies
- `cluster-security-audit`: verifies the built cluster against the promised posture
- `gitops-troubleshooting`: day-2 drift and reconciliation once GitOps-managed

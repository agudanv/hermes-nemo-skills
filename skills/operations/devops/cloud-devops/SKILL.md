---
name: cloud-devops
description: "Orchestrates cloud and DevOps engagements across AWS, Azure, and GCP: assesses a request, designs the target architecture, provisions infrastructure with Terraform, wires CI/CD, and hands off steady-state operations. Provides cloud authentication via environment variables, read-only discovery guardrails, IaC state hygiene rules, tagging standards, budget alerting, and a per-provider command cheat-sheet, then routes detailed work to specialized sibling skills. Use when working on cloud infrastructure, DevOps workflow design, AWS/Azure/GCP environments, Terraform provisioning, CI/CD pipelines, monitoring and observability rollout, or cloud-native development practices."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Cloud DevOps

Entry point for cloud and DevOps engagements. This skill assesses an incoming request, places it in the delivery lifecycle, applies the guardrails below, and routes deep work to the sibling skill that owns the detail. Prefer routing over re-deriving: if a sibling covers the concern, hand off with a crisp scope statement and the assess-phase findings.

## Operating Model

Move through five phases; start where the request actually is and pull in earlier phases only when a prerequisite is missing.

```text
assess -> design -> provision -> CI/CD -> operate
```

| Phase | Goal | Exit criteria |
| ------- | ------ | --------------- |
| assess | Understand current state and constraints | Inventory of accounts/subscriptions/projects, existing resources, drift risks, problem statement |
| design | Produce target architecture and delivery plan | Written topology, network/identity/data decisions, cost estimate, rollback strategy |
| provision | Create or change infrastructure declaratively | `terraform plan` reviewed and applied; state remote and locked; tags applied |
| CI/CD | Automate build, test, and release | Pipeline green from commit to environment; rollback path exercised once |
| operate | Run, observe, and improve the service | Dashboards and alerts live; runbooks written; incident path tested |

Phase essentials:

- assess: run read-only discovery first (cheat-sheet below); confirm target account/subscription/project before touching anything; identify state sources of truth (Terraform workspaces, Helm releases, GitOps repos, manual resources); record constraints such as data residency, compliance, and landing-zone policies.
- design: prefer managed services and federated identity (OIDC/workload identity) over static keys; plan CIDRs to avoid peer overlap; use private endpoints for data services; attach the budget alert at design time, not after the first surprise invoice.
- provision: every change through Terraform (or approved IaC); plan out to a file and apply exactly that file; second-reader review of plans on shared environments; console/CLI mutations are break-glass only, documented afterward.
- CI/CD: pipelines as code; secrets via the CI secret store or OIDC federation, never committed; each pipeline covers lint, test, build, scan, non-prod deploy, smoke test, gated promotion; rollback is a pipeline job, not a manual procedure.
- operate: golden signals (latency, traffic, errors, saturation) instrumented before production; alerts page on user impact, not raw resource metrics; runbooks for the top five failure modes; post-incident reviews feed back into design and provisioning.

## Phase-to-Skill Routing

| Concern | Route to |
| --------- | ---------- |
| Container image hardening, slimming, security, multi-stage optimization | `docker-expert` |
| Dockerfile basics, first container builds, container concepts | `docker` (container-fundamentals) |
| Local multi-container development, Compose topologies | `docker-patterns` |
| Kubernetes cluster and platform design, tenancy, networking decisions | `kubernetes-architect` |
| Kubernetes deploy workflows, manifests, Helm releases, rollouts | `kubernetes-deployment` |
| Release strategies: blue/green, canary, rolling, feature flags | `deployment-patterns` |
| Day-2 operational practices: branching, environments, code review, automation culture | `practices` |
| Structured ramp-up for engineers new to DevOps | `devops-learning-path` |
| GitOps drift, Argo CD sync failures, reconciliation loops | `gitops-troubleshooting` |
| Active incidents, triage, mitigation, post-incident follow-up | `incident-responder` |

If a request spans multiple rows, sequence handoffs in phase order (provision before CI/CD before operate) and keep this skill as the coordinating thread.

## Cloud Authentication

Authenticate through environment variables only. Never embed credentials in code, Terraform variable files, pipeline YAML, or skill output; reference variable names, never secret values.

| Provider | Variables | Notes |
| ---------- | ----------- | ------- |
| AWS | `AWS_PROFILE`, `AWS_REGION` | Prefer SSO (`aws sso login --profile "$AWS_PROFILE"`) or OIDC-assumed roles over static key pairs |
| Azure | `ARM_SUBSCRIPTION_ID`, plus `ARM_CLIENT_ID` / `ARM_TENANT_ID` / `ARM_CLIENT_SECRET` for Terraform service principals | Interactive: `az login`; CI: workload identity federation |
| GCP | `GOOGLE_APPLICATION_CREDENTIALS` (service-account key file), or ADC from `gcloud auth application-default login` | Prefer workload identity or attached service accounts on GCE/GKE |

Pre-flight identity check before any provider command:

```bash
aws sts get-caller-identity                       # AWS: identity + account
az account show --output table                    # Azure: active subscription
gcloud auth list --filter=status:ACTIVE           # GCP: active account
gcloud config get-value project                   # GCP: active project
```

If the identity does not match the engagement's target environment, stop and fix the environment selection before running anything else.

## Guardrails

### Read-only discovery first

- Open every engagement with read-only calls: `aws ... describe-*` / `list-*`, `az ... show` / `list`, `gcloud ... describe` / `list`. No create, update, or delete in the assess phase.
- Scope discovery with `--query` / `--filter` to the resources, groups, or tags in scope; avoid dumping entire accounts into context.

### Plan before apply

- Terraform changes follow `init -> fmt -> validate -> plan -> review -> apply`; save the plan (`terraform plan -out=tfplan`) and apply exactly that file, never a silently re-planned change.
- An agent may produce the plan; on shared environments a human approves it. `-target` is emergency-only, reconciled with a full plan immediately afterward.

### State file hygiene

- Remote state with locking from day one: S3 (+ DynamoDB or native lockfile), Azure Storage with blob lease locking, or GCS with object versioning.
- Never commit `terraform.tfstate`, `*.tfstate.backup`, or crash logs; keep them in `.gitignore`. Never hand-edit state; use `terraform state mv` / `rm` / `import` and record the operation in the change ticket.
- One state per environment per component; monolithic states make every plan slow and every apply high-blast-radius. Encrypt the backend and restrict access to the CI role plus break-glass admins; state can contain sensitive values.

### Budget alerts

- Create or verify a budget before provisioning new spend: AWS Budgets (actual + forecast), Azure Cost Management budgets, GCP Budgets.
- Standard thresholds: 50%, 80%, 100% of monthly budget, plus a forecasted-spend alert at 100%, routed to a monitored channel.

### Tagging standards

Apply to every taggable resource; enforce with policy (AWS SCP/tag policies, Azure Policy, GCP organization policy) where available:

| Tag | Example | Purpose |
| ----- | --------- | --------- |
| `environment` | `dev`, `staging`, `prod` | Blast radius and cost slicing |
| `owner` | team or distribution list | Accountability and orphan cleanup |
| `cost-center` | finance code | Chargeback |
| `managed-by` | `terraform`, `helm`, `manual` | Drift detection; manual resources get reconciled or imported |
| `application` | service name | Dependency mapping |

Untagged resources in shared accounts count as drift; report them during assess.

## Provider Cheat-Sheet (Read-Only)

### AWS

```bash
aws sts get-caller-identity
aws ec2 describe-regions --output table
aws ec2 describe-instances --filters Name=instance-state-name,Values=running
aws rds describe-db-instances
aws s3api list-buckets
aws iam list-roles --max-items 50
aws eks list-clusters
aws ce get-cost-and-usage --time-period Start=2026-08-01,End=2026-09-01 \
  --granularity MONTHLY --metrics UnblendedCost
aws cloudwatch describe-alarms --state-value ALARM
```

### Azure

```bash
az account show --output table
az account list-locations --output table
az vm list --output table
az aks list --output table
az network vnet list --output table
az role assignment list --all --output table
az consumption budget list
az monitor metrics alert list --output table
```

### GCP

```bash
gcloud auth list --filter=status:ACTIVE
gcloud config get-value project
gcloud compute regions list
gcloud compute instances list
gcloud container clusters list
gcloud sql instances list
gcloud projects get-iam-policy "$(gcloud config get-value project)"
gcloud billing budgets list --billing-account="$BILLING_ACCOUNT_ID"
gcloud logging read "severity>=ERROR" --limit=20 --freshness=1h
```

## Tooling Notes

Install tools with pinned versions only (`apt-get install -y terraform=<version>`, `pip install azure-cli==<version>`); never pipe remote install scripts into a shell. Verify tool versions before starting an engagement. All examples assume a Linux shell.

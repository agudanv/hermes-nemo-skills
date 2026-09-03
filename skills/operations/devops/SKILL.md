---
name: devops
description: "Category root for all DevOps skills in operations/. Load this file first for any Docker/containers, CI/CD (ArgoCD, GitHub Actions, GitLab CI), GitOps, deployment patterns, cloud DevOps, troubleshooting, DevOps learning, Kanban agent workflows, webhook automation, Hermes s6 container supervision, or dev-workflow question. Each subskill below is summarized with purpose, triggers, key patterns, and a pointer to its directory for full detail."
---

# DevOps — Category Skill

Single entry point for the `operations/devops/` skill tree. Read the section for the domain
you need, then load the referenced subskill `SKILL.md` for full detail.

---

## 1. Docker & containers (`docker*`)

- **`docker/container-fundamentals/docker/`** — Core Docker operations: Dockerfile best
  practices, Compose, image optimization (multi-stage builds, layer caching). Triggers:
  Docker, Dockerfile, container, image, docker-compose. Asset-backed (reference docs +
  scripts). Use as the default Docker skill.
- **`docker-expert/`** — Deep containerization expertise: optimization, security hardening,
  multi-stage builds, production practices (14 KB). Use when the question is about
  hardening/optimizing rather than basics.
- **`docker-patterns/`** — Docker and Docker Compose patterns for local development:
  container security, networking, volume strategies, multi-service orchestration.

Routing: basics → `container-fundamentals/docker/`; hardening/optimization → `docker-expert/`;
local multi-service setups → `docker-patterns/`.

---

## 2. CI/CD (`ci-cd/`)

### 2.1 ArgoCD

- **`ci-cd/argocd/`** — Complete ArgoCD CLI + REST API skill (15 KB, `devops-` hardened
  copy with SkillSpector verification): manage Applications (create, sync, delete,
  rollback), app-of-apps, sync waves/hooks, and REST endpoints via `scripts/argocd-api.sh`.
  `References/` holds 18 deep-dive docs (Application CRD fields, sync strategies, RBAC,
  notifications, etc.). Start here for any ArgoCD work.
- **`ci-cd/argocd-advanced/`** — Advanced ArgoCD beyond core CLI/API: multi-cluster
  ApplicationSet generators, automated image updates, new-cluster bootstrapping. Two
  bundled reference skills: `References/ArgocdClusterBootstrapping/` (root Applications,
  app-of-apps, sync-failure diagnosis, Kustomize) and `References/ArgocdImageUpdater/`
  (Image Updater config, drift resolution, ImageUpdater CRDs), plus
  `References/cluster-bootstrapping.md`.

### 2.2 Pipeline automation (`ci-cd/pipeline-automation/`)

| Skill | Use when |
| --- | --- |
| `deployment-pipeline-design` | Architecting multi-stage CI/CD pipelines with approval gates, security checks, deployment orchestration |
| `github-actions-templates` | Production-ready GitHub Actions workflows for build/test/deploy |
| `gitlab-ci-patterns` | GitLab CI/CD with multi-stage workflows, caching, distributed runners |
| `secrets-management` | Secure pipeline secrets with Vault, AWS Secrets Manager, or native platform solutions |

---

## 3. Standalone workflow skills (repo root, `devops/`)

- **`practices/`** — Team's operational practices: Kubernetes operations, container builds,
  CI/CD workflows, and local development environment management. SmartEM-specific
  instructions (repo path conventions, `dev-k8s.sh` usage, `smartem-decisions` namespace
  conventions). Load when working in this repo's own codebase.
- **`deployment-patterns/`** — Deployment workflows, CI/CD pipeline patterns, Docker
  containerization, health checks, rollback strategies, production readiness checklists
  for web applications.
- **`cloud-devops/`** — Cloud infrastructure and DevOps workflows: AWS, Azure, GCP,
  Kubernetes, Terraform, CI/CD, monitoring, cloud-native development.
- **`devops-troubleshooter/`** — Rapid incident response, advanced debugging, and modern
  observability for DevOps failures (CI/CD breaks, deploy failures, env drift).
- **`devops-learning-path/`** — Build a scoped, hands-on DevOps learning plan: safe Linux,
  cloud, Kubernetes, SRE, CI/CD, Git, and security labs. Use for "teach me / learning
  plan" requests, not task execution.
- **`hermes-s6-container-supervision/`** — Modify, debug, or extend the s6-overlay
  supervision tree inside the **Hermes Agent Docker image**: adding services, debugging
  profile gateways, understanding service dependencies. Hermes-stack-specific.
- **`kanban-orchestrator/`** — Decomposition playbook + anti-temptation rules for an
  orchestrator profile routing work through Kanban: the "don't do the work yourself" rule,
  task handoff, board hygiene.
- **`kanban-worker/`** — Pitfalls, examples, and edge cases for Hermes Kanban workers; the
  lifecycle itself is auto-injected as `KANBAN_GUIDANCE` into every worker.
- **`webhook-subscriptions/`** — Event-driven agent runs: subscribing agents to webhooks.

Kanban pair: `kanban-orchestrator/` governs the router; `kanban-worker/` governs the
execute side. Load the one matching the role being configured.

---

## 4. Automation micro-skills (`automation/`, 8 skills)

Focused 4–7 KB skills, mostly platform-agnostic engineering practices:

| Skill | Use when |
| --- | --- |
| `ci-cd-pipelines` | CI/CD pipeline patterns: GitHub Actions, GitLab CI, testing strategies, deployment automation |
| `devops-automation` | CI/CD pipeline design with GitHub Actions, Docker, Kubernetes, Helm, GitOps patterns |
| `kubernetes-operations` | K8s manifests, Helm charts, operators, troubleshooting, resource management |
| `microservices-design` | Service mesh, event-driven architecture, saga pattern, API gateway |
| `performance-optimization` | Web performance: bundle analysis, lazy loading, caching, Core Web Vitals |
| `python-best-practices` | Pythonic code: type hints, dataclasses, async, packaging, testing |
| `continuous-learning` | Auto-extract patterns from coding sessions, track corrections, confidence-scored knowledge |
| `manage-skills` | Discover, list, create, edit, toggle, copy, move, and delete AI agent skills across 11 tools (Cursor, Claude, Agents, Windsurf, Copilot, Codex, Cline, …) |

---

## 5. Foundations stubs (`foundations/`, 23 skills)

Auto-activating micro-skills (~2.2 KB each, `devops-<topic>`), one per routine task:
`bash-script-helper`, `branch-naming-helper`, `changelog-creator`,
`commit-message-formatter`, `docker-compose-creator`, `docker-container-basics`,
`dockerfile-generator`, `dotenv-manager`, `environment-variables-handler`,
`git-workflow-manager`, `github-actions-starter`, `gitignore-generator`,
`gitlab-ci-basics`, `jenkins-pipeline-intro`, `json-config-manager`,
`linux-commands-guide`, `makefile-generator`, `npm-scripts-optimizer`,
`package-json-manager`, `pre-commit-hook-setup`, `readme-generator`,
`release-notes-generator`, `ssh-key-manager`, `version-bumper`,
`yaml-config-validator`.

---

## 6. Technical documentation stubs (`technical-documentation/`, 23 skills)

Auto-activating micro-skills (~2.2 KB each, `docs-<topic>`), one per document type:
`adr-generator`, `api-reference-creator`, `architecture-doc-creator`,
`changelog-generator`, `code-documentation-analyzer`, `code-of-conduct-generator`,
`configuration-reference-generator`, `contributing-guide-creator`,
`deprecation-notice-generator`, `design-doc-template`, `docusaurus-config-setup`,
`faq-generator`, `incident-postmortem-template`, `installation-guide-creator`,
`jsdoc-comment-generator`, `migration-guide-creator`, `mkdocs-config-generator`,
`quickstart-guide-generator`, `readme-generator`, `release-notes-generator`,
`sdk-documentation-generator`, `troubleshooting-guide-creator`,
`tutorial-outline-creator`, `vitepress-config-creator`.

---

## Routing quick reference

| You need to... | Load |
| --- | --- |
| Write/optimize a Dockerfile | `docker/container-fundamentals/docker/`, then `docker-expert/` |
| Local multi-container dev environment | `docker-patterns/` |
| Manage ArgoCD apps | `ci-cd/argocd/` (CLI + REST + References) |
| Bootstrap a cluster with ArgoCD | `ci-cd/argocd-advanced/References/ArgocdClusterBootstrapping/` |
| ArgoCD image automation | `ci-cd/argocd-advanced/References/ArgocdImageUpdater/` |
| Design a CI/CD pipeline | `ci-cd/pipeline-automation/deployment-pipeline-design/` |
| GitHub Actions / GitLab CI workflows | `ci-cd/pipeline-automation/{github-actions-templates,gitlab-ci-patterns}/` |
| Pipeline secrets | `ci-cd/pipeline-automation/secrets-management/` |
| This repo's own workflow conventions | `practices/` |
| Deployment/rollback strategy | `deployment-patterns/` |
| Debug a broken pipeline/deploy | `devops-troubleshooter/` |
| Cloud infra (AWS/Azure/GCP + Terraform) | `cloud-devops/` |
| Hermes image s6 supervision | `hermes-s6-container-supervision/` |
| Configure Kanban routing/worker behavior | `kanban-orchestrator/` / `kanban-worker/` |
| Hook agents to events | `webhook-subscriptions/` |
| Routine chore (commit format, .gitignore, Makefile, …) | matching `foundations/` stub in §5 |
| Generate a doc (ADR, readme, postmortem, …) | matching `technical-documentation/` stub in §6 |

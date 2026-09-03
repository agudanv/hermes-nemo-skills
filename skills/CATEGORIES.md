# Skill Categories

The Hermes bundle uses four top-level groups:

| Directory | Use it for |
| --- | --- |
| `agent-platform/` | Hermes, agent collaboration, auto-heal, MCP, agent evaluation, and agent operations |
| `operations/` | Operator skill tree, split into three category roots: `infrastructure/` (Kubernetes, OpenShift including LLM/GPU model deployment, SRE, observability), `devops/` (Docker/containers, CI/CD including Argo CD, deployment patterns, cloud DevOps, Kanban agent workflows), and `misc/` (trusted-skill installation pipeline, Skillspector, shell tooling) |
| `integrations/` | Slack, Outlook, GitHub, data-source queries, and cross-source analysis |
| `workflows/` | Software development, productivity, creative work, social media, smart home, and gaming |

Each `operations/` category root contains a content-rich `SKILL.md` that maps the
category's subskills (purpose, triggers, key commands, and routing guidance), so an
agent can load one file to survey the whole category before drilling into a subskill.

The directory layout is for browsing. Hermes continues to discover skill commands
recursively, and all gateway authorization rules continue to apply.

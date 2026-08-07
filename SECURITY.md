<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Security Policy

## Scope of this bundle

`hermes-nemo-skills` is a distribution of agent skills: Markdown instructions plus
supporting scripts that an autonomous agent reads and executes. Installing a skill
grants the agent whatever capability that skill documents. Treat every skill
directory as code, not as documentation.

## Trust model

- **Skills carry no credentials.** No secret, token, key, or `.env` file belongs in
  this repository. Skills reference credentials only by environment-variable name
  (for example `GITHUB_TOKEN`, `SLACK_BOT_TOKEN`); the operator supplies the values
  out of band.
- **Skills are least-privilege by default.** A skill must request only the tools and
  scopes it documents. Scripts that spawn subprocesses forward an explicit
  environment allowlist rather than the full parent environment.
- **Destructive actions are gated.** Skills that can delete, force-push, or mutate
  production state must say so in their `SKILL.md` and must rely on the agent's
  approval prompt rather than suppressing it.
- **No remote code execution during install.** Skills must not instruct the agent to
  pipe a downloaded installer straight into a shell interpreter. Downloading,
  inspecting, and then running an installer is acceptable; so is a versioned
  package manager.
- **Third-party content is pinned.** Any `pip install git+…`, container image, or
  action reference in a skill must name a tag or commit SHA, never a moving branch.

## Automated review

Every change is scanned with [SkillSpector](https://github.com/NVIDIA/skillspector),
NVIDIA's agent-skill vulnerability scanner:

```bash
skillspector scan . --recursive --baseline .skillspector-baseline.yaml
```

CI runs the same command (`.github/workflows/skillspector.yml`) and fails the build
when a **new** finding appears. Reviewed false positives live in
`.skillspector-baseline.yaml`, each with a written justification. Suppressions are
scoped to Markdown documentation paths wherever possible — findings in executable
files (`.py`, `.sh`, `.ts`) are **not** blanket-suppressed and must be fixed or
individually justified.

To see what is currently suppressed:

```bash
skillspector scan . --recursive --baseline .skillspector-baseline.yaml --show-suppressed
```

## Contributing a skill safely

Before opening a PR:

1. Run `scripts/validate-skills.sh` to confirm skill metadata is present.
2. Run the SkillSpector command above and resolve any new finding.
3. If a finding is a false positive, add a scoped rule to
   `.skillspector-baseline.yaml` with a `reason:` explaining *why* it is benign.
   Do not add unscoped rules.
4. Record provenance for redistributed material in `SOURCE_NOTICES.md`.

## Reporting a vulnerability

Report suspected vulnerabilities in this bundle — a skill that leaks credentials,
escalates privilege, or carries hidden instructions — to the NVIDIA PSIRT process at
<https://www.nvidia.com/en-us/security/>. Please do not open a public issue for a
security report.

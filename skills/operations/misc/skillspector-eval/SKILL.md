---
name: skillspector-eval
description: Evaluates a skill package for safety, correctness, and policy compliance using the Skillspector engine. Accepts stdin JSON (skill_path, skill_name, policy_bundle, evaluation_mode) and emits a JSON report with severity-ranked findings and an approve/reject/conditional recommendation. Used by nemoclaw-skill-install as an install gate. Triggers on: skillspector, skill evaluation, skill safety scan, policy bundle compliance check.
---
# Skill: skillspector-eval

Evaluates a skill package for safety, correctness, and policy compliance using the Skillspector engine.

## Interface

### Input (via stdin JSON)
```json
{
  "skill_path": "/path/to/skill/directory",
  "skill_name": "skill-name",
  "policy_bundle": "/etc/openshell/policy/bundle.yaml",
  "evaluation_mode": "strict|permissive"
}
```

### Output (via stdout JSON)
```json
{
  "evaluation_id": "eval-<timestamp>-<hash>",
  "skill_name": "skill-name",
  "passed": true,
  "findings": [
    {
      "severity": "critical|high|medium|low|info",
      "category": "security|correctness|policy|performance|maintainability",
      "rule_id": "SPEC-XXXX",
      "message": "Description of finding",
      "file": "relative/path/to/file",
      "line": 42
    }
  ],
  "summary": {
    "critical": 0,
    "high": 0,
    "medium": 2,
    "low": 1,
    "info": 3
  },
  "recommendation": "approve|reject|conditional",
  "conditions": [
    "Condition description for conditional approval"
  ]
}
```

## Behavior

1. **Load skill**: Read SKILL.md, scripts, and assets from `skill_path`
2. **Load policy**: Read policy bundle from `policy_bundle` (YamlSigil format)
3. **Run evaluation**: Execute Skillspector checks:
   - Static analysis (AST patterns, secrets, dangerous patterns)
   - Policy verification (YamlSigil signature validation, PolicyBundle compliance)
   - Runtime behavior simulation (dry-run in sandbox)
   - Dependency scanning (supply chain, license, vulnerabilities)
4. **Emit report**: Output JSON to stdout
5. **Exit code**: 0 = evaluation complete (check `passed` field), non-zero = evaluation failed

## Evaluation Rules

### Critical (auto-reject)
- Unsigned or invalid PolicyBundle signature
- Hardcoded secrets, API keys, tokens
- `eval`/`exec`/`system` with user-controlled input
- Unbounded resource consumption (no limits on CPU/memory/disk)
- Cluster-admin or privileged escalation without justification

### High (conditional)
- Network egress to non-allowlisted domains
- Host filesystem access outside declared volumes
- Unpinned dependency versions in scripts
- Missing input validation on external data

### Medium (warning)
- Deprecated API usage
- Missing error handling on critical paths
- Insufficient logging/observability hooks

### Low (info)
- Style inconsistencies
- Missing documentation
- Optimization opportunities

## Configuration

Environment variables:
- `SPECTOR_POLICY_BUNDLE`: Path to policy bundle (default: `/etc/openshell/policy/bundle.yaml`)
- `SPECTOR_TIMEOUT`: Evaluation timeout seconds (default: 120)
- `SPECTOR_SANDBOX_IMAGE`: Sandbox container image (default: `ghcr.io/openshell/skillspector-sandbox:latest`)

## Example Usage

```bash
# Evaluate a skill directory
cat <<EOF | skillspector-eval
{
  "skill_path": "/chart-skills/docker-expert",
  "skill_name": "docker-expert",
  "evaluation_mode": "strict"
}
EOF
```

## Integration

Used by `nemoclaw-skill-install` as a gate before applying skill changes to Nemoclaw.
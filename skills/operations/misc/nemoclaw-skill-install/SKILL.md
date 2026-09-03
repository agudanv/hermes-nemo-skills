---
name: nemoclaw-skill-install
description: Use when installing, updating, or removing a skill in Nemoclaw. Runs Skillspector evaluation first, applies the skill to the Nemoclaw skills directory via rsync, triggers a ConfigMap-annotation reload, and verifies the rollout. Triggers on: nemoclaw skill install, nemoclaw skill update, nemoclaw skill remove, skillspector gate, skill reload, chart post-install skill seeding.
---
# Skill: nemoclaw-skill-install

Installs or updates a skill in Nemoclaw after passing Skillspector evaluation.

## Interface

### Input (via stdin JSON)
```json
{
  "skill_path": "/path/to/skill/directory",
  "skill_name": "skill-name",
  "operation": "install|update|remove",
  "policy_bundle": "/etc/openshell/policy/bundle.yaml",
  "evaluation_mode": "strict|permissive",
  "auto_confirm": false,
  "nemoclaw_namespace": "nemoclaw",
  "nemoclaw_release": "nemoclaw"
}
```

### Output (via stdout JSON)
```json
{
  "operation": "install|update|remove",
  "skill_name": "skill-name",
  "evaluation": {
    "evaluation_id": "eval-...",
    "passed": true,
    "recommendation": "approve|reject|conditional",
    "conditions": []
  },
  "confirmed": true,
  "applied": true,
  "reload_triggered": true,
  "message": "Skill installed and Nemoclaw reloaded"
}
```

## Behavior

1. **Evaluate**: Run `skillspector-eval` on the skill
2. **Check result**: 
   - If `recommendation: reject` → exit with error, do not proceed
   - If `recommendation: conditional` and `auto_confirm: false` → prompt for confirmation
   - If `recommendation: approve` or `auto_confirm: true` → proceed
3. **Apply**: Copy skill to Nemoclaw skills directory (`/var/lib/nemoclaw/skills/<skill-name>`)
4. **Reload**: Trigger Nemoclaw skill reload via ConfigMap annotation update
5. **Verify**: Confirm skill is loaded and healthy

## Steps

### 1. Evaluation Gate
```bash
cat <<EOF | skillspector-eval
{
  "skill_path": "/chart-skills/my-skill",
  "skill_name": "my-skill",
  "policy_bundle": "/etc/openshell/policy/bundle.yaml",
  "evaluation_mode": "strict"
}
EOF
```

### 2. Confirmation (if needed)
If evaluation returns `conditional` and `auto_confirm` is false:
- Display findings summary
- Ask user to confirm (via stdin or interactive prompt)
- Proceed only on explicit confirmation

### 3. Apply Skill
```bash
# Install/update
rsync -a --delete "/chart-skills/my-skill/" "/var/lib/nemoclaw/skills/my-skill/"

# Remove
rm -rf "/var/lib/nemoclaw/skills/my-skill"
```

### 4. Trigger Nemoclaw Reload
```bash
oc -n nemoclaw patch configmap nemoclaw-skills \
  -p '{"metadata":{"annotations":{"skills-reload":"'$(date +%s)'"}}}'
```

### 5. Verify Reload
```bash
# Wait for rollout
oc -n nemoclaw rollout status deployment/nemoclaw --timeout=60s

# Check skill loaded
oc -n nemoclaw exec deployment/nemoclaw -- nemoclaw-cli skills list | grep my-skill
```

## Error Handling

- Evaluation failure → exit 1, no changes applied
- Apply failure → rollback (restore previous skill version if update)
- Reload failure → alert, manual intervention required
- Verification failure → report, do not mark success

## Configuration

Environment variables:
- `NEMOCLAW_SKILLS_DIR`: Nemoclaw skills directory (default: `/var/lib/nemoclaw/skills`)
- `NEMOCLAW_NAMESPACE`: Kubernetes namespace (default: `nemoclaw`)
- `NEMOCLAW_RELEASE`: Helm release name (default: `nemoclaw`)
- `SKILLSPECTOR_POLICY_BUNDLE`: Policy bundle path (default: `/etc/openshell/policy/bundle.yaml`)

## Example Usage

```bash
# Install with auto-confirm (CI/CD)
cat <<EOF | nemoclaw-skill-install
{
  "skill_path": "/chart-skills/docker-expert",
  "skill_name": "docker-expert",
  "operation": "install",
  "auto_confirm": true
}
EOF

# Update with interactive confirmation
cat <<EOF | nemoclaw-skill-install
{
  "skill_path": "/chart-skills/docker-expert",
  "skill_name": "docker-expert",
  "operation": "update"
}
EOF
```

## Integration

Core skill in `hermes-webui-openshell` chart. Used by:
- Chart post-install hook for initial skill seeding
- Helm upgrade hooks for skill updates
- Manual skill management via Hermes WebUI
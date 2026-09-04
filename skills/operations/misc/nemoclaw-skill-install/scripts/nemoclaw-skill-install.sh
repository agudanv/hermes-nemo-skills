#!/bin/bash
# nemoclaw-skill-install — install/update/remove skill in Nemoclaw with Skillspector gate
# Reads JSON from stdin, writes JSON to stdout

set -euo pipefail

# Configuration
NEMOCLAW_SKILLS_DIR="${NEMOCLAW_SKILLS_DIR:-/var/lib/nemoclaw/skills}"
NEMOCLAW_NAMESPACE="${NEMOCLAW_NAMESPACE:-nemoclaw}"
NEMOCLAW_RELEASE="${NEMOCLAW_RELEASE:-nemoclaw}"
SKILLSPECTOR_POLICY_BUNDLE="${SKILLSPECTOR_POLICY_BUNDLE:-/etc/openshell/policy/bundle.yaml}"
SKILLSPECTOR_EVAL="${SKILLSPECTOR_EVAL:-/chart-bin/skillspector-eval}"

# Read input
input=$(cat)
skill_path=$(echo "$input" | jq -r '.skill_path // empty')
skill_name=$(echo "$input" | jq -r '.skill_name // empty')
operation=$(echo "$input" | jq -r '.operation // "install"')
policy_bundle=$(echo "$input" | jq -r '.policy_bundle // env.SKILLSPECTOR_POLICY_BUNDLE')
eval_mode=$(echo "$input" | jq -r '.evaluation_mode // "strict"')
auto_confirm=$(echo "$input" | jq -r '.auto_confirm // false')
nemoclaw_ns=$(echo "$input" | jq -r '.nemoclaw_namespace // env.NEMOCLAW_NAMESPACE')
nemoclaw_rel=$(echo "$input" | jq -r '.nemoclaw_release // env.NEMOCLAW_RELEASE')

# Validate input
if [ -z "$skill_path" ] || [ -z "$skill_name" ]; then
  jq -n --arg err "Missing required fields: skill_path, skill_name" '{error: $err, applied: false}'
  exit 1
fi

if [ ! -d "$skill_path" ]; then
  jq -n --arg err "Skill path not found: $skill_path" '{error: $err, applied: false}'
  exit 1
fi

if [ ! -f "$skill_path/SKILL.md" ]; then
  jq -n --arg err "SKILL.md not found in $skill_path" '{error: $err, applied: false}'
  exit 1
fi

case "$operation" in
  install|update|remove) ;;
  *) jq -n --arg err "Invalid operation: $operation" '{error: $err, applied: false}'; exit 1 ;;
esac

target_dir="$NEMOCLAW_SKILLS_DIR/$skill_name"
backup_dir=""

# 1. Run Skillspector evaluation
echo "Running Skillspector evaluation..." >&2
eval_input=$(jq -n \
  --arg sp "$skill_path" \
  --arg sn "$skill_name" \
  --arg pb "$policy_bundle" \
  --arg em "$eval_mode" \
  '{skill_path: $sp, skill_name: $sn, policy_bundle: $pb, evaluation_mode: $em}')

eval_output=$(echo "$eval_input" | "$SKILLSPECTOR_EVAL" 2>&1) || {
  jq -n --arg err "Skillspector evaluation failed" --arg out "$eval_output" '{error: $err, output: $out, applied: false}'
  exit 1
}

eval_passed=$(echo "$eval_output" | jq -r '.passed // false')
eval_recommendation=$(echo "$eval_output" | jq -r '.recommendation // "reject"')
eval_conditions=$(echo "$eval_output" | jq -c '.conditions // []')
eval_findings=$(echo "$eval_output" | jq -c '.findings // []')

# 2. Check evaluation result
if [ "$eval_recommendation" = "reject" ]; then
  jq -n \
    --arg op "$operation" \
    --arg sn "$skill_name" \
    --argjson eval "$eval_output" \
    --arg msg "Evaluation rejected skill installation" \
    '{operation: $op, skill_name: $sn, evaluation: $eval, confirmed: false, applied: false, message: $msg}'
  exit 1
fi

confirmed=false
if [ "$eval_recommendation" = "conditional" ] && [ "$auto_confirm" != "true" ]; then
  # Display findings and ask for confirmation
  echo "=== Skillspector Evaluation: CONDITIONAL ===" >&2
  echo "$eval_output" | jq -r '.findings[] | "[\(.severity|uppercase)] \(.category): \(.message) (\(.file):\(.line))"' >&2
  echo "" >&2
  echo "Conditions:" >&2
  echo "$eval_output" | jq -r '.conditions[] | "  - \(.)"' >&2
  echo "" >&2
  read -r -p "Proceed with $operation of skill '$skill_name'? [y/N] " confirm
  case "$confirm" in
    [yY]|[yY][eE][sS]) confirmed=true ;;
    *) confirmed=false ;;
  esac
else
  confirmed=true
fi

if [ "$confirmed" != "true" ]; then
  jq -n \
    --arg op "$operation" \
    --arg sn "$skill_name" \
    --argjson eval "$eval_output" \
    --arg msg "User declined conditional installation" \
    '{operation: $op, skill_name: $sn, evaluation: $eval, confirmed: false, applied: false, message: $msg}'
  exit 0
fi

# 3. Apply the operation
applied=false
reload_triggered=false
message=""

case "$operation" in
  install|update)
    # Backup existing skill if updating
    if [ "$operation" = "update" ] && [ -d "$target_dir" ]; then
      backup_dir="${target_dir}.backup.$(date +%s)"
      cp -a "$target_dir" "$backup_dir"
      echo "Backed up existing skill to $backup_dir" >&2
    fi

    # Apply skill
    mkdir -p "$target_dir"
    rsync -a --delete "$skill_path/" "$target_dir/"
    applied=true
    message="Skill $operation completed"
    ;;

  remove)
    if [ -d "$target_dir" ]; then
      backup_dir="${target_dir}.backup.$(date +%s)"
      mv "$target_dir" "$backup_dir"
      echo "Removed skill, backed up to $backup_dir" >&2
    else
      echo "Skill not found, nothing to remove" >&2
    fi
    applied=true
    message="Skill removed"
    ;;
esac

# 4. Trigger Nemoclaw reload
if [ "$applied" = "true" ] && command -v oc >/dev/null 2>&1; then
  echo "Triggering Nemoclaw skill reload..." >&2
  reload_annotation="skills-reload-$(date +%s)"
  if oc -n "$nemoclaw_ns" patch configmap "$nemoclaw_rel-skills" \
    -p "{\"metadata\":{\"annotations\":{\"skills-reload\":\"$reload_annotation\"}}}" 2>/dev/null; then
    reload_triggered=true
    echo "Reload triggered, waiting for rollout..." >&2

    # Wait for rollout
    if oc -n "$nemoclaw_ns" rollout status "deployment/$nemoclaw_rel" --timeout=120s >&2; then
      # Verify skill loaded
      if oc -n "$nemoclaw_ns" exec "deployment/$nemoclaw_rel" -- nemoclaw-cli skills list 2>/dev/null | grep -q "^$skill_name\s"; then
        message="$message, Nemoclaw reloaded and skill verified"
      else
        message="$message, Nemoclaw reloaded but skill not detected in list"
      fi
    else
      message="$message, Nemoclaw reload timed out"
      # Rollback on failure
      if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
        echo "Rolling back to backup..." >&2
        rm -rf "$target_dir"
        mv "$backup_dir" "$target_dir"
        oc -n "$nemoclaw_ns" patch configmap "$nemoclaw_rel-skills" \
          -p "{\"metadata\":{\"annotations\":{\"skills-reload\":\"rollback-$(date +%s)\"}}}" 2>/dev/null || true
        message="$message, rolled back"
        applied=false
      fi
    fi
  else
    message="$message, failed to trigger reload"
    # Rollback on failure
    if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
      rm -rf "$target_dir"
      mv "$backup_dir" "$target_dir"
      message="$message, rolled back"
      applied=false
    fi
  fi
else
  message="$message (Nemoclaw reload skipped: oc not available or not in cluster)"
fi

# 5. Output result
jq -n \
  --arg op "$operation" \
  --arg sn "$skill_name" \
  --argjson eval "$eval_output" \
  --argjson confirmed "$confirmed" \
  --argjson applied "$applied" \
  --argjson reload "$reload_triggered" \
  --arg msg "$message" \
  '{
    operation: $op,
    skill_name: $sn,
    evaluation: $eval,
    confirmed: $confirmed,
    applied: $applied,
    reload_triggered: $reload,
    message: $msg
  }'

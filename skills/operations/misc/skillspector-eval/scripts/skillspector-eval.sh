#!/bin/bash
# skillspector-eval — evaluate a skill for safety and policy compliance
# Reads JSON from stdin, writes JSON to stdout

set -euo pipefail

# Configuration
SPECTOR_POLICY_BUNDLE="${SPECTOR_POLICY_BUNDLE:-/etc/openshell/policy/bundle.yaml}"
SPECTOR_TIMEOUT="${SPECTOR_TIMEOUT:-120}"
SPECTOR_SANDBOX_IMAGE="${SPECTOR_SANDBOX_IMAGE:-ghcr.io/openshell/skillspector-sandbox:latest}"

# Read input
input=$(cat)
skill_path=$(echo "$input" | jq -r '.skill_path // empty')
skill_name=$(echo "$input" | jq -r '.skill_name // empty')
policy_bundle=$(echo "$input" | jq -r '.policy_bundle // env.SPECTOR_POLICY_BUNDLE')
eval_mode=$(echo "$input" | jq -r '.evaluation_mode // "strict"')

# Validate input
if [ -z "$skill_path" ] || [ -z "$skill_name" ]; then
  jq -n --arg err "Missing required fields: skill_path, skill_name" '{error: $err, passed: false}'
  exit 1
fi

if [ ! -d "$skill_path" ]; then
  jq -n --arg err "Skill path not found: $skill_path" '{error: $err, passed: false}'
  exit 1
fi

if [ ! -f "$skill_path/SKILL.md" ]; then
  jq -n --arg err "SKILL.md not found in $skill_path" '{error: $err, passed: false}'
  exit 1
fi

evaluation_id="eval-$(date +%s)-$(echo -n "$skill_name" | sha256sum | cut -c1-8)"
findings=()
critical=0
high=0
medium=0
low=0
info=0

add_finding() {
  local severity=$1 category=$2 rule_id=$3 message=$4 file=$5 line=$6
  findings+=("$(jq -n \
    --arg sev "$severity" \
    --arg cat "$category" \
    --arg rule "$rule_id" \
    --arg msg "$message" \
    --arg f "$file" \
    --argjson ln "$line" \
    '{severity: $sev, category: $cat, rule_id: $rule, message: $msg, file: $f, line: $ln}')")
  case $severity in
    critical) critical=$((critical + 1)) ;;
    high) high=$((high + 1)) ;;
    medium) medium=$((medium + 1)) ;;
    low) low=$((low + 1)) ;;
    info) info=$((info + 1)) ;;
  esac
}

# 1. Check SKILL.md structure
skill_md="$skill_path/SKILL.md"
if ! grep -q '^# Skill:' "$skill_md"; then
  add_finding "high" "correctness" "SPEC-001" "Missing '# Skill:' header in SKILL.md" "SKILL.md" 1
fi

if ! grep -q '^## Interface' "$skill_md"; then
  add_finding "medium" "maintainability" "SPEC-002" "Missing '## Interface' section in SKILL.md" "SKILL.md" 1
fi

if ! grep -q '^## Behavior' "$skill_md"; then
  add_finding "medium" "maintainability" "SPEC-003" "Missing '## Behavior' section in SKILL.md" "SKILL.md" 1
fi

# 2. Scan scripts for dangerous patterns
for script in "$skill_path"/scripts/**/* "$skill_path"/scripts/*; do
  [ -f "$script" ] || continue
  rel_script="${script#$skill_path/}"

  # Check for eval/exec with user input
  if grep -Eq '(eval|exec|system)\s*\(.*\$\{' "$script"; then
    line=$(grep -En '(eval|exec|system)\s*\(.*\$\{' "$script" | head -1 | cut -d: -f1)
    add_finding "critical" "security" "SPEC-101" "Dynamic code execution with user-controlled input" "$rel_script" "$line"
  fi

  # Check for hardcoded secrets
  if grep -Eiq '(api[_-]?key|secret|token|password)\s*[:=]\s*["'\''][^"'\'']{8,}' "$script"; then
    line=$(grep -Eni '(api[_-]?key|secret|token|password)\s*[:=]\s*["'\''][^"'\'']{8,}' "$script" | head -1 | cut -d: -f1)
    add_finding "critical" "security" "SPEC-102" "Hardcoded credential detected" "$rel_script" "$line"
  fi

  # Check for unbounded resource usage
  if grep -Eq 'docker run|kubectl run|oc run' "$script" && ! grep -Eq '(--cpus|--memory|--memory-swap|resources:|limits:)' "$script"; then
    add_finding "high" "correctness" "SPEC-103" "Container/workload launch without resource limits" "$rel_script" 1
  fi

  # Check for unpinned versions
  if grep -Eq '(docker pull|FROM)\s+[^:]+(:latest)?$' "$script"; then
    line=$(grep -En '(docker pull|FROM)\s+[^:]+(:latest)?$' "$script" | head -1 | cut -d: -f1)
    add_finding "high" "correctness" "SPEC-104" "Unpinned container image version (latest or no tag)" "$rel_script" "$line"
  fi

  # Check for missing input validation
  if grep -Eq '(curl|wget|oc apply|kubectl apply)\s.*\$\{' "$script" && ! grep -Eq 'validate|sanitize|jq.*-e' "$script"; then
    line=$(grep -En '(curl|wget|oc apply|kubectl apply)\s.*\$\{' "$script" | head -1 | cut -d: -f1)
    add_finding "high" "security" "SPEC-105" "External command with unvalidated variable input" "$rel_script" "$line"
  fi

  # Check for network egress
  if grep -Eq '(curl|wget|nc|netcat|telnet)\s+(http|https)://' "$script"; then
    line=$(grep -En '(curl|wget|nc|netcat|telnet)\s+(http|https)://' "$script" | head -1 | cut -d: -f1)
    add_finding "high" "security" "SPEC-106" "Outbound network call detected; verify allowlist compliance" "$rel_script" "$line"
  fi

  # Check for host filesystem access
  if grep -Eq '(/host|/proc|/sys|/var/run/docker\.sock)' "$script"; then
    line=$(grep -En '(/host|/proc|/sys|/var/run/docker\.sock)' "$script" | head -1 | cut -d: -f1)
    add_finding "high" "security" "SPEC-107" "Host filesystem/device access detected" "$rel_script" "$line"
  fi

  # Check for privileged escalation
  if grep -Eq '(privileged: true|--privileged|cap_add:|securityContext:.*privileged)' "$script"; then
    line=$(grep -En '(privileged: true|--privileged|cap_add:|securityContext:.*privileged)' "$script" | head -1 | cut -d: -f1)
    add_finding "critical" "security" "SPEC-108" "Privileged escalation without justification" "$rel_script" "$line"
  fi
done

# 3. Check for PolicyBundle and signature
policy_file=""
if [ -f "$skill_path/policy.yaml" ]; then
  policy_file="$skill_path/policy.yaml"
elif [ -f "$skill_path/policy.yml" ]; then
  policy_file="$skill_path/policy.yml"
fi

if [ -n "$policy_file" ]; then
  # Verify YamlSigil signature exists
  if ! grep -q 'signature:' "$policy_file"; then
    add_finding "critical" "policy" "SPEC-201" "PolicyBundle missing YamlSigil signature" "$(basename "$policy_file")" 1
  fi
  # Verify against central policy bundle if available
  if [ -f "$policy_bundle" ]; then
    # TODO: Implement YamlSigil verification against bundle
    add_finding "info" "policy" "SPEC-202" "PolicyBundle found; signature verification against central bundle not yet implemented" "$(basename "$policy_file")" 1
  fi
else
  add_finding "info" "policy" "SPEC-203" "No PolicyBundle in skill; using defaults" "SKILL.md" 1
fi

# 4. Dependency scanning (basic)
for script in "$skill_path"/scripts/**/* "$skill_path"/scripts/*; do
  [ -f "$script" ] || continue
  rel_script="${script#$skill_path/}"

  # Check for package installs without version pins
  if grep -Eq '(pip install|npm install|apk add|yum install|dnf install)\s+[^=<>~^]+\s*($|\s)' "$script"; then
    line=$(grep -En '(pip install|npm install|apk add|yum install|dnf install)\s+[^=<>~^]+\s*($|\s)' "$script" | head -1 | cut -d: -f1)
    add_finding "medium" "correctness" "SPEC-301" "Package install without version pin" "$rel_script" "$line"
  fi
done

# 5. Sandbox dry-run (if available)
if command -v skillspector-sandbox >/dev/null 2>&1; then
  # Run in sandbox with timeout
  timeout "$SPECTOR_TIMEOUT" skillspector-sandbox \
    --skill "$skill_path" \
    --policy "$policy_bundle" \
    --mode "$eval_mode" \
    --image "$SPECTOR_SANDBOX_IMAGE" \
    --output /tmp/sandbox-result.json 2>/dev/null || true

  if [ -f /tmp/sandbox-result.json ]; then
    sandbox_passed=$(jq -r '.passed // false' /tmp/sandbox-result.json)
    if [ "$sandbox_passed" != "true" ]; then
      add_finding "high" "correctness" "SPEC-401" "Sandbox dry-run failed or produced errors" "sandbox" 0
    fi
    # Merge sandbox findings
    sandbox_findings=$(jq -c '.findings[]?' /tmp/sandbox-result.json 2>/dev/null || true)
    while IFS= read -r f; do
      [ -n "$f" ] && findings+=("$f")
    done <<< "$sandbox_findings"
    rm -f /tmp/sandbox-result.json
  fi
else
  add_finding "info" "correctness" "SPEC-402" "Skillspector sandbox not available; static analysis only" "evaluation" 0
fi

# 6. Determine recommendation
recommendation="approve"
conditions=()

if [ "$critical" -gt 0 ]; then
  recommendation="reject"
elif [ "$high" -gt 0 ]; then
  if [ "$eval_mode" = "strict" ]; then
    recommendation="reject"
  else
    recommendation="conditional"
    conditions+=("Resolve all HIGH severity findings before production use")
  fi
elif [ "$medium" -gt 0 ]; then
  recommendation="conditional"
  conditions+=("Address MEDIUM findings for production readiness")
fi

# Build output
findings_json=$(printf '%s\n' "${findings[@]}" | jq -s '.')

jq -n \
  --arg eval_id "$evaluation_id" \
  --arg skill "$skill_name" \
  --argjson passed "$([ "$recommendation" = "approve" ] && echo true || echo false)" \
  --argjson findings "$findings_json" \
  --argjson summary "$(jq -n --argjson c "$critical" --argjson h "$high" --argjson m "$medium" --argjson l "$low" --argjson i "$info" '{critical: $c, high: $h, medium: $m, low: $l, info: $i}')" \
  --arg rec "$recommendation" \
  --argjson conditions "$(printf '%s\n' "${conditions[@]}" | jq -R . | jq -s .)" \
  '{
    evaluation_id: $eval_id,
    skill_name: $skill,
    passed: $passed,
    findings: $findings,
    summary: $summary,
    recommendation: $rec,
    conditions: $conditions
  }'
#!/bin/sh
# Verify an OpenAI-compatible model endpoint through a temporary in-cluster
# port-forward. A healthy simple completion is required; tool calling is
# exercised and reported separately because model support varies.
set -eu

# Hermes tool executions do not inherit the container's chart PATH.
export PATH="/chart-bin:/toolbox:${PATH:-/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin}"

usage() {
  cat >&2 <<'EOF'
usage: verify-openai-endpoint.sh --namespace NAME --service NAME [--model MODEL] [--timeout SECONDS]
EOF
  exit 64
}

namespace=
service=
requested_model=
timeout_seconds=300
pf_pid=

while [ "$#" -gt 0 ]; do
  case "$1" in
    --namespace) namespace=${2:-}; shift 2 ;;
    --service) service=${2:-}; shift 2 ;;
    --model) requested_model=${2:-}; shift 2 ;;
    --timeout) timeout_seconds=${2:-}; shift 2 ;;
    *) usage ;;
  esac
done

[ -n "$namespace" ] && [ -n "$service" ] || usage
case "$timeout_seconds" in ''|*[!0-9]*) usage ;; esac

workdir=$(mktemp -d "${TMPDIR:-/tmp}/hermes-llm-verify.XXXXXX") || exit 1
trap 'if [ -n "${pf_pid:-}" ]; then kill "$pf_pid" 2>/dev/null || true; wait "$pf_pid" 2>/dev/null || true; fi; rm -rf "$workdir"' EXIT HUP INT TERM
local_port=$((20000 + ($$ % 10000)))
endpoint="http://127.0.0.1:$local_port"
deadline=$(( $(date +%s) + timeout_seconds ))

start_port_forward() {
  if [ -n "${pf_pid:-}" ] && kill -0 "$pf_pid" 2>/dev/null; then
    return 0
  fi
  pf_pid=
  : >"$workdir/port-forward.log"
  oc -n "$namespace" port-forward "service/$service" "$local_port:8000" \
    >"$workdir/port-forward.log" 2>&1 &
  pf_pid=$!
  sleep 1
}

while [ "$(date +%s)" -lt "$deadline" ]; do
  start_port_forward
  if curl -fsS --connect-timeout 5 --max-time 10 "$endpoint/health" >"$workdir/health.json" 2>/dev/null && \
     curl -fsS --connect-timeout 5 --max-time 10 "$endpoint/v1/models" >"$workdir/models.json" 2>/dev/null; then
    break
  fi
  sleep 10
done

if [ ! -s "$workdir/models.json" ]; then
  reason=$(tail -n 3 "$workdir/port-forward.log" 2>/dev/null | tr '\n' ' ' | tr -s ' ')
  [ -n "$reason" ] || reason='service-health-or-model-list-not-ready'
  printf '%s\n' \
    'VERIFY_RESULT=pending' \
    "VERIFY_SERVICE=$service" \
    "VERIFY_REASON=$reason" \
    "VERIFY_WAITED_SECONDS=$timeout_seconds"
  exit 1
fi

served_model=$(python3 - "$workdir/models.json" "$requested_model" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
models = [item.get("id", "") for item in data.get("data", []) if item.get("id")]
requested = sys.argv[2]
if requested and requested in models:
    print(requested)
elif models:
    print(models[0])
PY
)

if [ -z "$served_model" ]; then
  printf '%s\n' \
    'VERIFY_RESULT=failed' \
    "VERIFY_SERVICE=$service" \
    'VERIFY_REASON=v1-models-returned-no-model-id'
  exit 2
fi

python3 - "$workdir/simple.json" "$served_model" <<'PY'
import json
import sys

json.dump(
    {
        "model": sys.argv[2],
        "messages": [{"role": "user", "content": "Reply with exactly: model endpoint ready"}],
        # Reasoning-capable models can consume a small response budget before
        # producing final content. This remains a bounded smoke test while
        # allowing their valid reasoning response to prove endpoint health.
        "max_tokens": 256,
        "temperature": 0,
    },
    open(sys.argv[1], "w", encoding="utf-8"),
)
PY
simple_code=$(curl -sS --connect-timeout 10 --max-time 90 \
  -o "$workdir/simple-response.json" -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary "@$workdir/simple.json" \
  "$endpoint/v1/chat/completions" || true)

if [ "$simple_code" != 200 ] || ! python3 - "$workdir/simple-response.json" <<'PY'
import json
import sys

try:
    payload = json.load(open(sys.argv[1], encoding="utf-8"))
    message = payload.get("choices", [{}])[0].get("message", {})
    assert message.get("content") is not None or message.get("reasoning_content") is not None or message.get("tool_calls")
except Exception:
    raise SystemExit(1)
PY
then
  detail=$(head -c 400 "$workdir/simple-response.json" 2>/dev/null | tr '\n' ' ' | tr -s ' ' | sed -E 's/hf_[A-Za-z0-9_-]+/[REDACTED_HF_TOKEN]/g')
  printf '%s\n' \
    'VERIFY_RESULT=failed' \
    "VERIFY_SERVICE=$service" \
    "VERIFY_MODEL=$served_model" \
    "VERIFY_REASON=chat-completions-http-$simple_code" \
    "VERIFY_RESPONSE=$detail"
  exit 2
fi

simple_finish_reason=$(python3 - "$workdir/simple-response.json" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
print(payload.get("choices", [{}])[0].get("finish_reason", "unknown"))
PY
)

python3 - "$workdir/tool.json" "$served_model" <<'PY'
import json
import sys

json.dump(
    {
        "model": sys.argv[2],
        "messages": [{"role": "user", "content": "Call the get_cluster_time tool now. Do not answer with prose."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_cluster_time",
                    "description": "Return the current UTC time.",
                    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
                },
            }
        ],
        "tool_choice": "required",
        "max_tokens": 256,
        "temperature": 0,
    },
    open(sys.argv[1], "w", encoding="utf-8"),
)
PY
tool_code=$(curl -sS --connect-timeout 10 --max-time 90 \
  -o "$workdir/tool-response.json" -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary "@$workdir/tool.json" \
  "$endpoint/v1/chat/completions" || true)

tool_result=not-observed
if [ "$tool_code" = 200 ] && python3 - "$workdir/tool-response.json" <<'PY'
import json
import sys

try:
    payload = json.load(open(sys.argv[1], encoding="utf-8"))
    message = payload.get("choices", [{}])[0].get("message", {})
    assert message.get("tool_calls") or message.get("function_call")
except Exception:
    raise SystemExit(1)
PY
then
  tool_result=passed
elif [ "$tool_code" != 200 ]; then
  tool_result=not-supported-or-rejected
fi

printf '%s\n' \
  'VERIFY_RESULT=ready' \
  "VERIFY_SERVICE=$service" \
  "VERIFY_MODEL=$served_model" \
  'VERIFY_SIMPLE_COMPLETION=passed' \
  "VERIFY_SIMPLE_FINISH_REASON=$simple_finish_reason" \
  "VERIFY_TOOL_CALL=$tool_result" \
  "VERIFY_TRANSPORT=port-forward-service/$service"

if [ -n "$requested_model" ] && [ "$requested_model" != "$served_model" ]; then
  printf '%s\n' "VERIFY_REQUESTED_MODEL_NOT_ADVERTISED=$requested_model"
fi

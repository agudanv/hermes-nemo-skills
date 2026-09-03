#!/bin/sh
# Execute a PromQL query against the cluster's built-in monitoring stack.
#
# Reaches the OpenShift Thanos Querier through a temporary in-cluster
# port-forward, which tunnels over the already-permitted Kubernetes API
# connection. End-to-end TLS is preserved: the Thanos serving certificate is
# verified against the service CA, so this never needs --insecure and never
# leaves the cluster through a Route.
set -eu

# Hermes tool executions do not inherit the container's chart PATH.
export PATH="/chart-bin:/toolbox:${PATH:-/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin}"

usage() {
  cat >&2 <<'EOF'
usage: query-metrics.sh --query PROMQL [--time RFC3339] [--timeout SECONDS]

Prints the raw Prometheus HTTP API JSON response on stdout.
EOF
  exit 64
}

query=
at_time=
timeout_seconds=30

while [ "$#" -gt 0 ]; do
  case "$1" in
    --query) query=${2:-}; shift 2 ;;
    --time) at_time=${2:-}; shift 2 ;;
    --timeout) timeout_seconds=${2:-}; shift 2 ;;
    *) usage ;;
  esac
done

[ -n "$query" ] || usage

monitoring_namespace=openshift-monitoring
service=thanos-querier
service_host=thanos-querier.openshift-monitoring.svc
service_port=9091

workdir=$(mktemp -d)
pf_pid=

cleanup() {
  [ -n "$pf_pid" ] && kill "$pf_pid" 2>/dev/null || true
  rm -rf "$workdir"
}
trap cleanup EXIT INT TERM

# The projected service-account token is the sandbox identity. Fall back to the
# active oc session so the script is also usable outside the sandbox.
sa_dir=/var/run/secrets/kubernetes.io/serviceaccount
if [ -r "$sa_dir/token" ]; then
  token=$(cat "$sa_dir/token")
else
  token=$(oc whoami -t 2>/dev/null || true)
fi

if [ -z "$token" ]; then
  echo 'query-metrics: no service-account token and no active oc session' >&2
  exit 77
fi

# Verify the Thanos serving certificate against the service CA rather than
# disabling verification.
ca_file="$sa_dir/service-ca.crt"
if [ ! -r "$ca_file" ]; then
  ca_file="$workdir/service-ca.crt"
  if ! oc get configmap openshift-service-ca.crt -n "$monitoring_namespace" \
      -o jsonpath='{.data.service-ca\.crt}' >"$ca_file" 2>/dev/null || [ ! -s "$ca_file" ]; then
    echo 'query-metrics: unable to obtain the service CA bundle' >&2
    exit 77
  fi
fi

# Find a free local port and confirm the tunnel is actually forwarding before
# issuing the query.
local_port=
port=19091
while [ "$port" -lt 19111 ]; do
  : >"$workdir/port-forward.log"
  oc -n "$monitoring_namespace" port-forward "service/$service" \
    "$port:$service_port" >"$workdir/port-forward.log" 2>&1 &
  candidate_pid=$!

  waited=0
  while [ "$waited" -lt 10 ]; do
    if grep -q 'Forwarding from' "$workdir/port-forward.log" 2>/dev/null; then
      local_port=$port
      pf_pid=$candidate_pid
      break
    fi
    kill -0 "$candidate_pid" 2>/dev/null || break
    sleep 1
    waited=$((waited + 1))
  done

  [ -n "$local_port" ] && break
  kill "$candidate_pid" 2>/dev/null || true
  port=$((port + 1))
done

if [ -z "$local_port" ]; then
  reason=$(tail -n 3 "$workdir/port-forward.log" 2>/dev/null | tr '\n' ' ' | tr -s ' ')
  [ -n "$reason" ] || reason='port-forward-to-thanos-querier-failed'
  echo "query-metrics: $reason" >&2
  exit 75
fi

set -- --data-urlencode "query=$query"
[ -n "$at_time" ] && set -- "$@" --data-urlencode "time=$at_time"

http_status=$(curl -sS --max-time "$timeout_seconds" \
  --resolve "$service_host:$local_port:127.0.0.1" \
  --cacert "$ca_file" \
  -H "Authorization: Bearer $token" \
  -o "$workdir/response.json" -w '%{http_code}' \
  "$@" "https://$service_host:$local_port/api/v1/query" 2>"$workdir/curl.err" || true)

case "$http_status" in
  200)
    cat "$workdir/response.json"
    ;;
  401|403)
    echo "query-metrics: Thanos rejected the token (HTTP $http_status). The service account needs the cluster-monitoring-view ClusterRole." >&2
    exit 77
    ;;
  '')
    reason=$(tr -s ' \n' ' ' <"$workdir/curl.err" 2>/dev/null)
    echo "query-metrics: query transport failed. ${reason:-no response from thanos-querier}" >&2
    exit 75
    ;;
  *)
    echo "query-metrics: unexpected HTTP $http_status from thanos-querier" >&2
    head -c 400 "$workdir/response.json" >&2 2>/dev/null || true
    exit 75
    ;;
esac

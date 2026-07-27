#!/bin/sh
# Inventory or remove only resources that are tied to one Hermes model release.
# Model-cache deletion is deliberately opt-in. The chart-managed HF token is
# deleted by the isolated downloader before serving starts, not by uninstall.
set -eu

# Hermes tool executions do not inherit the container's chart PATH.
export PATH="/chart-bin:/toolbox:${PATH:-/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin}"

usage() {
  cat >&2 <<'EOF'
usage: remove-model.sh --namespace NAME --release NAME --platform openshift|kubernetes \
  [--action inventory|delete] [--purge-storage] [--confirm]
EOF
  exit 64
}

namespace=
release=
platform=
action=inventory
purge_storage=false
confirmed=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --namespace) namespace=${2:-}; shift 2 ;;
    --release) release=${2:-}; shift 2 ;;
    --platform) platform=${2:-}; shift 2 ;;
    --action) action=${2:-}; shift 2 ;;
    --purge-storage) purge_storage=true; shift ;;
    --confirm) confirmed=true; shift ;;
    *) usage ;;
  esac
done

[ -n "$namespace" ] && [ -n "$release" ] && [ -n "$platform" ] || usage
case "$platform" in openshift|kubernetes) ;; *) usage ;; esac
case "$action" in inventory|delete) ;; *) usage ;; esac

label="app.kubernetes.io/instance=$release"
dynamo_scc_binding=$(printf '%s-dynamo-scc' "$release" | cut -c1-63 | sed 's/-$//')

has_resource() {
  oc api-resources -o name 2>/dev/null | grep -Eq "^$1(\\.|$)"
}

inventory() {
  printf '%s\n' \
    'REMOVE_INVENTORY=begin' \
    "REMOVE_NAMESPACE=$namespace" \
    "REMOVE_RELEASE=$release" \
    "REMOVE_STORAGE_ACTION=$( [ "$purge_storage" = true ] && printf purge-requested || printf retain )"
  if has_resource dynamographdeployments; then
    oc -n "$namespace" get dynamographdeployments.nvidia.com "$release" --ignore-not-found -o wide 2>&1 || true
  fi
  oc -n "$namespace" get deployment,statefulset,job,service,pvc -l "$label" -o wide 2>&1 || true
  if has_resource horizontalpodautoscalers; then
    oc -n "$namespace" get horizontalpodautoscalers -l "$label" -o wide 2>&1 || true
  fi
  if has_resource routes; then
    oc -n "$namespace" get routes -l "$label" -o wide 2>&1 || true
  fi
  if has_resource servicemonitors; then
    oc -n "$namespace" get servicemonitors -l "$label" -o wide 2>&1 || true
  fi
  if [ "$platform" = openshift ]; then
    oc -n "$namespace" get rolebinding "$dynamo_scc_binding" -o wide 2>&1 || true
  fi
  printf '%s\n' 'REMOVE_INVENTORY=end'
}

inventory

if [ "$action" = inventory ]; then
  printf '%s\n' 'REMOVE_RESULT=inventory-only'
  exit 0
fi

if [ "$confirmed" != true ]; then
  printf '%s\n' 'REMOVE_RESULT=confirmation-required'
  exit 64
fi

if has_resource dynamographdeployments; then
  oc -n "$namespace" delete dynamographdeployments.nvidia.com "$release" \
    --ignore-not-found=true --wait=false || true
fi
oc -n "$namespace" delete deployment,statefulset,job,service \
  -l "$label" --ignore-not-found=true --wait=false || true
if has_resource horizontalpodautoscalers; then
  oc -n "$namespace" delete horizontalpodautoscalers -l "$label" \
    --ignore-not-found=true --wait=false || true
fi
if has_resource routes; then
  oc -n "$namespace" delete routes -l "$label" \
    --ignore-not-found=true --wait=false || true
fi
if has_resource servicemonitors; then
  oc -n "$namespace" delete servicemonitors -l "$label" \
    --ignore-not-found=true --wait=false || true
fi
if [ "$platform" = openshift ]; then
  oc -n "$namespace" delete rolebinding "$dynamo_scc_binding" \
    --ignore-not-found=true --wait=false || true
fi

if [ "$purge_storage" = true ]; then
  oc -n "$namespace" delete persistentvolumeclaims -l "$label" \
    --ignore-not-found=true --wait=false || true
  storage_result=purge-started
else
  storage_result=retained
fi

printf '%s\n' \
  'REMOVE_RESULT=resources-removal-started' \
  "REMOVE_STORAGE=$storage_result" \
  'REMOVE_HF_TOKEN_SECRET=not-present-or-unmanaged'

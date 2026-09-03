#!/bin/sh
# Resolve an official NVIDIA Dynamo runtime image without deriving tags from
# model names. Exact model recipes may provide a complete image reference and
# the Dynamo runtime compatibility version packaged in that image.
set -eu

usage() {
  cat >&2 <<'EOF'
usage: resolve-dynamo-image.sh \
  --default-image IMAGE --default-runtime-version X.Y.Z \
  --backend vllm|trtllm [--model MODEL_ID] [--overrides-file FILE]
EOF
  exit 64
}

default_image=
default_runtime_version=
backend=
model_id=
overrides_file=

while [ "$#" -gt 0 ]; do
  case "$1" in
    --default-image) default_image=${2:-}; shift 2 ;;
    --default-runtime-version) default_runtime_version=${2:-}; shift 2 ;;
    --backend) backend=${2:-}; shift 2 ;;
    --model) model_id=${2:-}; shift 2 ;;
    --overrides-file) overrides_file=${2:-}; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

[ -n "$default_image" ] && [ -n "$default_runtime_version" ] && [ -n "$backend" ] || usage
case "$backend" in vllm|trtllm) ;; *) usage ;; esac
printf '%s\n' "$default_runtime_version" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || usage

emit_result() {
  image=$1
  runtime_version=$2
  source=$3
  reason=$4
  printf '%s\n' \
    "DYNAMO_IMAGE=$image" \
    "DYNAMO_RUNTIME_VERSION=$runtime_version" \
    "DYNAMO_IMAGE_SOURCE=$source" \
    "DYNAMO_IMAGE_REASON=$reason"
}

extract_model_recipe() {
  file=$1
  wanted_model=$2
  image_key=$3
  python3 - "$file" "$wanted_model" "$image_key" <<'PY'
from __future__ import annotations

import re
import sys


def indentation(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


path, wanted_model, image_key = sys.argv[1:]
try:
    lines = open(path, encoding="utf-8").read().splitlines()
except OSError:
    raise SystemExit(1)

overrides_indent = None
model_indent = None
recipe: dict[str, str] = {}
for raw_line in lines:
    stripped = raw_line.strip()
    if not stripped or stripped.startswith("#"):
        continue
    indent = indentation(raw_line)
    key, separator, value = stripped.partition(":")
    if not separator:
        continue
    key = key.strip().strip('"\'')
    if overrides_indent is None:
        if key == "modelRuntimeOverrides" and not value.strip():
            overrides_indent = indent
        continue
    if indent <= overrides_indent:
        break
    if model_indent is None:
        if key == wanted_model and not value.strip():
            model_indent = indent
        continue
    if indent <= model_indent:
        break
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    recipe[key] = value

image = recipe.get(image_key, "")
version = recipe.get("dynamoRuntimeVersionOverride", "")
if re.search(r"\s", image) or "/" not in image:
    raise SystemExit(1)
if "@sha256:" in image:
    if not re.search(r"@sha256:[0-9a-f]{64}$", image):
        raise SystemExit(1)
elif ":" not in image.rsplit("/", 1)[-1]:
    raise SystemExit(1)
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
    raise SystemExit(1)
print(image)
print(version)
PY
}

case "$backend" in
  vllm)
    override_key=dynamoVllmRuntimeImage
    official_repository=nvcr.io/nvidia/ai-dynamo/vllm-runtime
    ;;
  trtllm)
    override_key=dynamoTrtllmRuntimeImage
    official_repository=nvcr.io/nvidia/ai-dynamo/tensorrtllm-runtime
    ;;
esac

if [ -n "$model_id" ] && [ -n "$overrides_file" ] && [ -f "$overrides_file" ]; then
  model_recipe=$(extract_model_recipe "$overrides_file" "$model_id" "$override_key" 2>/dev/null || true)
  model_image=$(printf '%s\n' "$model_recipe" | sed -n '1p')
  model_runtime_version=$(printf '%s\n' "$model_recipe" | sed -n '2p')
  if [ -n "$model_image" ] && [ -n "$model_runtime_version" ]; then
    emit_result \
      "$model_image" \
      "$model_runtime_version" \
      model-override \
      exact-model-runtime-image-and-version
    exit 0
  fi
fi

workdir=$(mktemp -d "${TMPDIR:-/tmp}/hermes-dynamo-resolve.XXXXXX") || exit 1
trap 'rm -rf "$workdir"' EXIT HUP INT TERM
release_json="$workdir/release.json"

parse_stable_release_json() {
  python3 - "$1" <<'PY'
import json
import re
import sys

try:
    payload = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)

tag = payload.get("tag_name", "")
if payload.get("draft") or payload.get("prerelease"):
    raise SystemExit(1)
match = re.fullmatch(r"v([0-9]+\.[0-9]+\.[0-9]+)", tag if isinstance(tag, str) else "")
if not match:
    raise SystemExit(1)
print(match.group(1))
PY
}

resolve_nvcr_index_digest() {
  repository=$1
  version=$2
  token_json="$workdir/nvcr-token.json"
  manifest_json="$workdir/nvcr-manifest.json"
  manifest_headers="$workdir/nvcr-manifest.headers"
  curl_config="$workdir/nvcr-curl.config"
  auth_url="https://nvcr.io/proxy_auth?scope=repository:${repository}:pull&service=nvcr.io"
  manifest_url="https://nvcr.io/v2/${repository}/manifests/${version}"

  if ! curl --fail --silent --show-error --location --max-time 15 \
    --output "$token_json" "$auth_url" 2>/dev/null; then
    return 1
  fi
  token=$(python3 - "$token_json" <<'PY'
import json
import re
import sys

try:
    payload = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)
token = payload.get("token", "")
if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", token):
    raise SystemExit(1)
print(token)
PY
) || return 1

  umask 077
  printf '%s\n' \
    "header = \"Authorization: Bearer $token\"" \
    'header = "Accept: application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json"' \
    >"$curl_config"
  if ! curl --config "$curl_config" --fail --silent --show-error --location --max-time 20 \
    --dump-header "$manifest_headers" --output "$manifest_json" \
    "$manifest_url" 2>/dev/null; then
    return 1
  fi

  python3 - "$manifest_json" "$manifest_headers" <<'PY'
import hashlib
import json
import re
import sys

manifest_path, headers_path = sys.argv[1:]
try:
    raw_manifest = open(manifest_path, "rb").read()
    payload = json.loads(raw_manifest)
    headers = open(headers_path, encoding="utf-8", errors="replace").read()
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)

if payload.get("mediaType") not in {
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
}:
    raise SystemExit(1)
if not any(
    item.get("platform", {}).get("os") == "linux"
    and item.get("platform", {}).get("architecture") == "amd64"
    for item in payload.get("manifests", [])
    if isinstance(item, dict)
):
    raise SystemExit(1)

match = re.search(r"^docker-content-digest:\s*(sha256:[0-9a-f]{64})\s*$", headers, re.I | re.M)
if not match:
    raise SystemExit(1)
digest = match.group(1).lower()
if digest != "sha256:" + hashlib.sha256(raw_manifest).hexdigest():
    raise SystemExit(1)
print(digest)
PY
}

release_version=
if curl --fail --silent --show-error --location --max-time 15 \
  --output "$release_json" \
  'https://api.github.com/repos/ai-dynamo/dynamo/releases/latest' 2>/dev/null; then
  release_version=$(parse_stable_release_json "$release_json" 2>/dev/null || true)
fi

if [ -z "$release_version" ]; then
  release_url=$(curl --fail --silent --show-error --location --max-time 15 \
    --output /dev/null --write-out '%{url_effective}' \
    'https://github.com/ai-dynamo/dynamo/releases/latest' 2>/dev/null || true)
  release_version=$(printf '%s\n' "$release_url" | python3 -c '
import re
import sys

url = sys.stdin.read().strip()
match = re.fullmatch(r"https://github\.com/ai-dynamo/dynamo/releases/tag/v([0-9]+\.[0-9]+\.[0-9]+)", url)
if match:
    print(match.group(1))
' || true)
fi

if [ -n "$release_version" ]; then
  release_image="$official_repository:$release_version"
  case "$default_image" in
    "$release_image"@sha256:*)
      release_image=$default_image
      release_reason=stable-release-matches-digest-pinned-chart-default
      ;;
    *)
      repository=${official_repository#nvcr.io/}
      release_digest=$(resolve_nvcr_index_digest "$repository" "$release_version" 2>/dev/null || true)
      if [ -z "$release_digest" ]; then
        emit_result \
          "$default_image" \
          "$default_runtime_version" \
          chart-default \
          stable-release-ngc-artifact-or-linux-amd64-index-unavailable
        exit 0
      fi
      release_image="$release_image@$release_digest"
      release_reason=stable-release-ngc-linux-amd64-index-digest-verified
      ;;
  esac
  emit_result \
    "$release_image" \
    "$release_version" \
    github-latest-release \
    "$release_reason"
  exit 0
fi

emit_result \
  "$default_image" \
  "$default_runtime_version" \
  chart-default \
  stable-release-unavailable
exit 0

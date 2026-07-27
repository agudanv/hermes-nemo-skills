#!/bin/sh
# Resolve the latest stable vLLM release to its matching public Docker Hub tag.
# Never use the mutable latest tag. If the GitHub API rate limit is exhausted,
# use the public releases/latest redirect before falling back to the chart default.
set -eu

usage() {
  echo "usage: resolve-vllm-image.sh --default-image IMAGE" >&2
  exit 64
}

default_image=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --default-image) default_image=${2:-}; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

[ -n "$default_image" ] || usage

emit_default() {
  reason=$1
  printf '%s\n' \
    "VLLM_IMAGE=$default_image" \
    'VLLM_IMAGE_SOURCE=chart-default' \
    "VLLM_IMAGE_REASON=$reason"
}

workdir=$(mktemp -d "${TMPDIR:-/tmp}/hermes-vllm-release.XXXXXX") || exit 1
trap 'rm -rf "$workdir"' EXIT HUP INT TERM
release_json="$workdir/release.json"
tag_json="$workdir/tag.json"

release_tag=
if curl --fail --silent --show-error --location --max-time 15 \
  --output "$release_json" \
  'https://api.github.com/repos/vllm-project/vllm/releases/latest' 2>/dev/null; then
  release_tag=$(python3 - "$release_json" <<'PY'
import json
import re
import sys

try:
    payload = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)

tag = payload.get("tag_name", "")
if not isinstance(tag, str) or not re.fullmatch(r"v[0-9]+(?:\.[0-9]+){2}(?:[-.][0-9A-Za-z]+)*", tag):
    raise SystemExit(1)
print(tag)
PY
) || true
fi

if [ -z "$release_tag" ]; then
  release_url=$(curl --fail --silent --show-error --location --max-time 15 \
    --output /dev/null --write-out '%{url_effective}' \
    'https://github.com/vllm-project/vllm/releases/latest' 2>/dev/null || true)
  release_tag=$(printf '%s\n' "$release_url" | python3 -c '
import re
import sys

url = sys.stdin.read().strip()
match = re.fullmatch(r"https://github\.com/vllm-project/vllm/releases/tag/(v[0-9]+(?:\.[0-9]+){2}(?:[-.][0-9A-Za-z]+)*)", url)
if match:
    print(match.group(1))
' || true)
fi

if [ -z "$release_tag" ]; then
  emit_default 'github-latest-release-unavailable'
  exit 0
fi

if ! curl --fail --silent --show-error --location --max-time 15 \
  --output "$tag_json" \
  "https://hub.docker.com/v2/repositories/vllm/vllm-openai/tags/$release_tag" 2>/dev/null; then
  emit_default "docker-hub-tag-unavailable-$release_tag"
  exit 0
fi

if ! python3 - "$tag_json" "$release_tag" <<'PY'
import json
import sys

try:
    payload = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)
raise SystemExit(0 if payload.get("name") == sys.argv[2] else 1)
PY
then
  emit_default "docker-hub-tag-invalid-$release_tag"
  exit 0
fi

printf '%s\n' \
  "VLLM_IMAGE=docker.io/vllm/vllm-openai:$release_tag" \
  'VLLM_IMAGE_SOURCE=github-latest-release' \
  "VLLM_RELEASE_TAG=$release_tag"

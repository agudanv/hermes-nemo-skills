# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env bash
set -euo pipefail

root="${1:-skills}"
[[ -d "$root" ]] || { echo "Skill root not found: $root" >&2; exit 1; }

count=0
while IFS= read -r -d "" skill; do
  grep -qE "^(# |---$)" "$skill" || { echo "Missing Markdown title: $skill" >&2; exit 1; }
  count=$((count + 1))
done < <(find "$root" -type f -name SKILL.md -print0 | sort -z)

(( count > 0 )) || { echo "No SKILL.md files found under $root" >&2; exit 1; }
echo "Validated $count skill(s) under $root"

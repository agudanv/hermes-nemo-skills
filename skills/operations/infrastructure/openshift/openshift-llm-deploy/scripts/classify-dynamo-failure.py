#!/usr/bin/env python3
"""Classify Dynamo failure evidence for safe automatic vLLM fallback."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


FALLBACK_CONDITION = re.compile(
    r"(?:"
    r"model.*(?:unsupported|incompat|load.*fail)|"
    r"backend.*(?:unsupported|incompat)|"
    r"runtime.*(?:unsupported|incompat)|"
    r"engine.*(?:unsupported|incompat|build.*fail)|"
    r"unsupported.*(?:model|backend|runtime|quant)|"
    r"incompat.*(?:model|backend|runtime)"
    r")",
    re.IGNORECASE,
)
FALLBACK_LOG = re.compile(
    r"(?:"
    r"cannot import name ['\"]?increment_coord|"
    r"nvidia_cutlass_dsl|"
    r"vllm_flash_attn.*cutlass|"
    r"model type .* not supported|"
    r"unsupported quantization|"
    r"unknown quantization|"
    r"no kernel image is available for execution|"
    r"unsupported (?:gpu )?architecture|"
    r"does not support (?:this )?model"
    r")",
    re.IGNORECASE | re.DOTALL,
)
INFRASTRUCTURE_POD = re.compile(
    r"(?:"
    r"ImagePullBackOff|ErrImagePull|InvalidImageName|"
    r"CreateContainerConfigError|CreateContainerError|"
    r"ContainerCannotRun"
    r")"
)
TERMINAL_POD = re.compile(
    r"(?:"
    r"\tFailed\t|"
    r"RunContainerError|CrashLoopBackOff"
    r")"
)
TERMINAL_CONDITION = re.compile(r"(?:Failed|Error|Failure)=True:", re.IGNORECASE)


def read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def classify(conditions: str, pod_state: str, runtime_log: str) -> tuple[str, str]:
    if INFRASTRUCTURE_POD.search(pod_state):
        return "terminal", "pod-infrastructure-failure"
    if FALLBACK_CONDITION.search(conditions):
        return "fallback", "dgd-model-or-runtime-incompatible"
    if FALLBACK_LOG.search(runtime_log):
        return "fallback", "runtime-log-proves-model-or-backend-incompatibility"
    if TERMINAL_POD.search(pod_state):
        return "terminal", "pod-terminal-or-infrastructure-failure"
    if TERMINAL_CONDITION.search(conditions):
        return "terminal", "dgd-terminal-failure-not-proven-compatible-with-fallback"
    return "none", "no-terminal-failure-evidence"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dgd-conditions", default="")
    parser.add_argument("--pod-state-file", required=True)
    parser.add_argument("--runtime-log-file", required=True)
    arguments = parser.parse_args()
    failure_class, reason = classify(
        arguments.dgd_conditions,
        read_text(arguments.pod_state_file),
        read_text(arguments.runtime_log_file),
    )
    print(f"DYNAMO_FAILURE_CLASS={failure_class}")
    print(f"DYNAMO_FAILURE_REASON={reason}")


if __name__ == "__main__":
    main()

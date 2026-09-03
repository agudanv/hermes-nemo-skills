#!/usr/bin/env python3
"""Bounded AF_UNIX client for the Hermes managed-skill RPC."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import math
import os
import re
import socket
import stat
import sys
import unicodedata
from pathlib import Path
from typing import Any


SKILL_MANAGER_SOCKET_PATH = "/run/hermes-skill-manager/manager.sock"
RPC_REQUEST_DEFAULT_BYTES = 64 * 1024
RPC_REQUEST_SCHEMA_MAX_BYTES = 1024 * 1024
REPORT_DEFAULT_BYTES = 16 * 1024 * 1024
REPORT_SCHEMA_MIN_BYTES = 4096
REPORT_SCHEMA_MAX_BYTES = 64 * 1024 * 1024
SUCCESS_ENVELOPE_BYTES = 22
SCANNER_TIMEOUT_DEFAULT_SECONDS = 300.0
SCANNER_TIMEOUT_SCHEMA_MAX_SECONDS = 86400.0
SCAN_LOCAL_OVERHEAD_SECONDS = 60.0
SHORT_RPC_TIMEOUT_SECONDS = 30.0
APPROVAL_TOKEN_MAX_BYTES = 32768
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
BASE64URL_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
URL_SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


class ClientError(Exception):
    """A client-side failure safe to reduce to a generic message."""


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise ClientError("invalid command line")


def canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ClientError("invalid JSON value") from exc


def validate_digest(value: str) -> str:
    if not DIGEST_PATTERN.fullmatch(value):
        raise ClientError("invalid digest")
    return value


def validate_skill_name(value: str) -> str:
    if not SKILL_NAME_PATTERN.fullmatch(value):
        raise ClientError("invalid skill name")
    return value


def configured_limit(
    name: str,
    default: int,
    maximum: int,
    *,
    minimum: int = 1,
) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    if not re.fullmatch(r"[1-9][0-9]*", raw):
        raise ClientError("invalid configured limit")
    try:
        value = int(raw)
    except ValueError as exc:
        raise ClientError("invalid configured limit") from exc
    if value < minimum or value > maximum:
        raise ClientError("invalid configured limit")
    return value


def configured_timeout(name: str, default: float, maximum: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ClientError("invalid configured timeout") from exc
    if not math.isfinite(value) or value <= 0 or value > maximum:
        raise ClientError("invalid configured timeout")
    return value


def validate_relative_path(value: str) -> str:
    if (
        not value
        or value.startswith("/")
        or "\\" in value
        or URL_SCHEME_PATTERN.match(value)
    ):
        raise ClientError("invalid source path")
    components = value.split("/")
    if any(
        not component
        or component in {".", ".."}
        or any(
            unicodedata.category(character).startswith("C")
            for character in component
        )
        for component in components
    ):
        raise ClientError("invalid source path")
    return value


def _decode_base64url(value: str, maximum: int) -> bytes:
    if not value or len(value) > maximum or not BASE64URL_PATTERN.fullmatch(value):
        raise ClientError("invalid approval token")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, binascii.Error) as exc:
        raise ClientError("invalid approval token") from exc
    if base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != value:
        raise ClientError("invalid approval token")
    return decoded


def _validate_token_shape(token: str) -> str:
    if len(token.encode("ascii")) > APPROVAL_TOKEN_MAX_BYTES:
        raise ClientError("invalid approval token")
    parts = token.split(".")
    if len(parts) != 2:
        raise ClientError("invalid approval token")
    _decode_base64url(parts[0], 24576)
    signature = _decode_base64url(parts[1], 128)
    if len(signature) != 32:
        raise ClientError("invalid approval token")
    return token


def read_approval_token(path: Path) -> str:
    if not hasattr(os, "O_NOFOLLOW"):
        raise ClientError("secure token reads are unavailable")
    flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ClientError("approval token file rejected") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_uid != os.geteuid()
            or stat.S_IMODE(before.st_mode) & 0o077
            or before.st_size <= 0
            or before.st_size > APPROVAL_TOKEN_MAX_BYTES
        ):
            raise ClientError("approval token file rejected")
        chunks = bytearray()
        while len(chunks) <= APPROVAL_TOKEN_MAX_BYTES:
            chunk = os.read(
                descriptor,
                min(4096, APPROVAL_TOKEN_MAX_BYTES + 1 - len(chunks)),
            )
            if not chunk:
                break
            chunks.extend(chunk)
        after = os.fstat(descriptor)
        identity = lambda metadata: (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_mode,
            metadata.st_nlink,
            metadata.st_uid,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        )
        if len(chunks) > APPROVAL_TOKEN_MAX_BYTES or identity(before) != identity(after):
            raise ClientError("approval token file rejected")
    except OSError as exc:
        raise ClientError("approval token file rejected") from exc
    finally:
        os.close(descriptor)
    try:
        token = bytes(chunks).decode("ascii")
    except UnicodeDecodeError as exc:
        raise ClientError("approval token file rejected") from exc
    return _validate_token_shape(token)


def _parse_response(raw: bytes, approval_token: str | None) -> dict[str, Any]:
    if not raw.endswith(b"\n") or b"\n" in raw[:-1]:
        raise ClientError("invalid manager response")
    body = raw[:-1]
    if approval_token is not None and approval_token.encode("ascii") in body:
        raise ClientError("invalid manager response")
    duplicate = False

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        nonlocal duplicate
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                duplicate = True
            result[key] = value
        return result

    try:
        envelope = json.loads(body, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClientError("invalid manager response") from exc
    if duplicate or not isinstance(envelope, dict) or canonical_json(envelope) != body:
        raise ClientError("invalid manager response")
    ok = envelope.get("ok")
    if ok is True:
        if set(envelope) != {"ok", "result"} or not isinstance(envelope["result"], dict):
            raise ClientError("invalid manager response")
    elif ok is False:
        error = envelope.get("error")
        if set(envelope) != {"error", "ok"} or not isinstance(error, dict):
            raise ClientError("invalid manager response")
        if set(error) != {"code", "message"} or not all(
            isinstance(error[field], str) and error[field]
            for field in ("code", "message")
        ):
            raise ClientError("invalid manager response")
    else:
        raise ClientError("invalid manager response")
    return envelope


def call_manager(
    request: dict[str, Any],
    approval_token: str | None = None,
) -> tuple[dict[str, Any], bytes]:
    request_max_bytes = configured_limit(
        "SKILL_MANAGER_RPC_REQUEST_MAX_BYTES",
        RPC_REQUEST_DEFAULT_BYTES,
        RPC_REQUEST_SCHEMA_MAX_BYTES,
    )
    report_max_bytes = configured_limit(
        "SKILL_MANAGER_MAX_REPORT_BYTES",
        REPORT_DEFAULT_BYTES,
        REPORT_SCHEMA_MAX_BYTES,
        minimum=REPORT_SCHEMA_MIN_BYTES,
    )
    scanner_timeout_seconds = configured_timeout(
        "SKILL_MANAGER_SCANNER_TIMEOUT_SECONDS",
        SCANNER_TIMEOUT_DEFAULT_SECONDS,
        SCANNER_TIMEOUT_SCHEMA_MAX_SECONDS,
    )
    action = request.get("action")
    response_max_bytes = report_max_bytes + SUCCESS_ENVELOPE_BYTES
    response_timeout_seconds = SHORT_RPC_TIMEOUT_SECONDS
    if action == "scan":
        response_timeout_seconds = scanner_timeout_seconds + SCAN_LOCAL_OVERHEAD_SECONDS
    elif action == "activate":
        response_timeout_seconds = None
    encoded_request = canonical_json(request)
    if len(encoded_request) > request_max_bytes:
        raise ClientError("request exceeds manager limit")
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        connection.settimeout(SHORT_RPC_TIMEOUT_SECONDS)
        connection.connect(SKILL_MANAGER_SOCKET_PATH)
        if action == "activate":
            connection.settimeout(None)
        connection.sendall(encoded_request + b"\n")
        connection.shutdown(socket.SHUT_WR)
        connection.settimeout(response_timeout_seconds)
        response = bytearray()
        while True:
            chunk = connection.recv(
                min(4096, response_max_bytes + 1 - min(len(response), response_max_bytes))
            )
            if not chunk:
                break
            response.extend(chunk)
            if len(response) > response_max_bytes:
                raise ClientError("manager response exceeds limit")
    except (OSError, TimeoutError) as exc:
        raise ClientError("manager request failed") from exc
    finally:
        connection.close()
    raw = bytes(response)
    envelope = _parse_response(raw, approval_token)
    return envelope, raw


def argument_parser() -> SafeArgumentParser:
    parser = SafeArgumentParser(description="Hermes managed-skill RPC client")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("health", help="check manager health")
    actions.add_parser("status", help="show the active managed set")

    scan = actions.add_parser("scan", help="scan an already-staged quarantine skill")
    scan.add_argument("--skill-name", required=True)
    scan.add_argument("--relative-path", required=True)

    report = actions.add_parser("report", help="retrieve an exact report")
    report.add_argument("--report-digest", required=True)

    activate = actions.add_parser("activate", help="activate an approved report")
    activate.add_argument("--report-digest", required=True)
    activate.add_argument("--approval-token-file", type=Path, required=True)
    return parser


def build_request(arguments: argparse.Namespace) -> tuple[dict[str, Any], str | None]:
    if arguments.action in {"health", "status"}:
        return {"action": arguments.action}, None
    if arguments.action == "scan":
        return (
            {
                "action": "scan",
                "relative_path": validate_relative_path(arguments.relative_path),
                "skill_name": validate_skill_name(arguments.skill_name),
                "source_id": "quarantine",
            },
            None,
        )
    report_digest = validate_digest(arguments.report_digest)
    if arguments.action == "report":
        return {"action": "report", "report_digest": report_digest}, None
    approval_token = read_approval_token(arguments.approval_token_file)
    return (
        {
            "action": "activate",
            "approval_token": approval_token,
            "report_digest": report_digest,
        },
        approval_token,
    )


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if any(
        argument == "--approval-token" or argument.startswith("--approval-token=")
        for argument in arguments
    ):
        sys.stderr.write("managed-skill-client: token text options are forbidden\n")
        return 2
    try:
        parsed = argument_parser().parse_args(arguments)
        request, approval_token = build_request(parsed)
        envelope, raw = call_manager(request, approval_token)
    except ClientError:
        sys.stderr.write("managed-skill-client: request rejected\n")
        return 2
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()
    return 0 if envelope["ok"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())

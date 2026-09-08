---
name: docker-expert
description: "Advanced Docker containerization: image optimization (multi-stage builds, layer-cache ordering, BuildKit cache and secret mounts, base-image tradeoffs, .dockerignore hygiene, size audits with dive), security hardening (non-root user, read-only rootfs, capability dropping, no-new-privileges, pinned base digests, SBOM and provenance attestations, trivy and grype scanning), production runtime (HEALTHCHECK, STOPSIGNAL and graceful shutdown, tmpfs, resource limits, logging drivers), and debugging (inspect, nsenter, ephemeral debug containers, failure signatures). Use when asked to optimize a Dockerfile, harden a container, diagnose why an image is too large, design a multi-stage build, or review container security."
license: Apache-2.0
---

<!-- SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Docker Expert

Expert-level Docker for production: Engine 24+, BuildKit, Linux. Basics: `docker` (container-fundamentals), `docker-patterns`; cluster admission: `cluster-security-audit`.

## Image Optimization

### Multi-stage builds

Compile in a toolchain stage; ship only artifacts - the final stage carries no compiler, headers, package cache, or VCS metadata.

```dockerfile
# syntax=docker/dockerfile:1.7
FROM golang:1.23-bookworm@sha256:REPLACE_WITH_INDEX_DIGEST AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/app ./cmd/app

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/app /app
USER nonroot
EXPOSE 8080
ENTRYPOINT ["/app"]
```

Rules:

- `COPY --from=<stage>` only what the runtime needs; the toolchain never ships.
- Same distro family across stages when linking shared libraries, or build fully static (`CGO_ENABLED=0`) for `scratch`/`distroless/static`. Strip binaries (`ldflags "-s -w"`).
- Interpreted stacks: `pip wheel -w /wheels -r requirements.txt` in the builder, `pip install --no-index --no-cache-dir --find-links=/wheels` in the runtime.

### Layer ordering for cache hits

A layer rebuilds when its instruction or copied inputs change, and every later layer rebuilds too. Order least-to-most volatile: base image and OS packages; dependency manifests (`go.mod`, `requirements.txt`) copied alone; dependency install; application source (`COPY . .`); volatile metadata last. Never `COPY . .` before installing dependencies: every source edit busts the dependency layer.

### BuildKit cache and secret mounts

Cache mounts persist toolchain caches across builds without inflating layers:

| Toolchain | Mount target | Notes |
| --- | --- | --- |
| apt | `/var/cache/apt`, `/var/lib/apt` | `sharing=locked`; remove `/etc/apt/apt.conf.d/docker-clean` |
| pip | `/root/.cache/pip` | skip when using `--no-cache-dir` |
| npm | `/root/.npm` | pair with `npm ci` |
| Go | `/go/pkg/mod`, `/root/.cache/go-build` | module and build cache |

Secrets must use secret mounts - `ARG MY_TOKEN` leaks into `docker history`: `RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci` with `docker buildx build --secret id=npmrc,src="$HOME/.npmrc" ...`.

### Base image selection

| Base | Approx size | libc | Shell / pkg mgr | Best for |
| --- | --- | --- | --- | --- |
| `scratch` | 0 | none | none | fully static Go/Rust binaries |
| `gcr.io/distroless/static` | ~2 MB | none | none | static binaries, minimal CVE surface |
| `gcr.io/distroless/base` | ~20 MB | glibc | none | glibc-linked binaries, no shell needed |
| `alpine:3.20` | ~8 MB | musl | busybox sh / apk | small apps tolerant of musl |
| `debian:12-slim` | ~75 MB | glibc | dash / apt | default for Python/Node/Java |

Tradeoffs that bite in production:

- alpine/musl: glibc-linked binaries fail with a misleading "no such file or directory"; resolver differences (no NSS, DNS-over-TCP truncation history) cause intermittent DNS failures under Kubernetes `ndots:5`.
- distroless: no shell (`docker exec` fails - use ephemeral containers, see Debugging); `:nonroot` is uid 65532; ships CA certs, tzdata, `/etc/passwd` - `scratch` ships none, so copy CA certs and set `SSL_CERT_FILE` or TLS fails with x509 errors.
- Default to `debian:*-slim`; alpine's 60 MB saving rarely covers the musl compatibility cost.

### .dockerignore

Exclude from build context (cache invalidation of `COPY . .`; `.env`/`.git` exclusion prevents secret leaks):

```text
.git
.dockerignore
Dockerfile
node_modules/
.env
.env.*
```

### Size audit workflow

1. Per-layer breakdown: `docker history --no-trunc --format '{{.Size}}\t{{.CreatedBy}}' myapp:1.4.2`.
1. Interactive audit with `dive myapp:1.4.2` (pinned release binary):

```bash
curl -fsSL "https://github.com/wagoodman/dive/releases/download/v0.12.0/dive_0.12.0_linux_amd64.tar.gz" | tar -xz dive && install -m0755 dive /usr/local/bin/
```

1. Enforce in CI with `.dive-ci` at repo root and `CI=true dive myapp:1.4.2`:

```yaml
rules:
  lowestEfficiency: 0.95
  highestWastedBytes: 20MB
  highestUserWastedPercent: 0.20
```

Common waste: files deleted in a later layer still occupy space (clean in the same `RUN`, e.g. `&& rm -rf /var/lib/apt/lists/*`); toolchain in the final image (use a builder stage).

## Security Hardening

### Non-root user

Numeric UID so Kubernetes `runAsNonRoot` can verify it; own the files the app writes:

```dockerfile
RUN groupadd -r app -g 10001 && useradd -r -u 10001 -g app app
COPY --chown=10001:10001 . /app
USER 10001:10001
```

Ports below 1024 fail as non-root; expose a high port or add back `NET_BIND_SERVICE` (below).

### Read-only rootfs and tmpfs

```bash
docker run --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  --tmpfs /run:rw,noexec,nosuid,nodev,size=16m \
  myapp:1.4.2
```

Tmpfs every path the app legitimately writes; rogue writes then fail loudly. Mount config/secrets read-only (`-v /etc/app/config:/config:ro`).

### Capabilities

The default set (`CHOWN`, `DAC_OVERRIDE`, `NET_RAW`, `SETUID`, `NET_BIND_SERVICE`, and more) exceeds what most apps need. Drop everything, add back only what breaks:

```bash
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE myapp:1.4.2
```

Add-backs: `NET_BIND_SERVICE` (ports <1024), `SYS_TIME` (ntpd), `NET_RAW` (`ping`). `CHOWN`/`DAC_OVERRIDE` "needs" usually mean missing `COPY --chown` at build time.

### no-new-privileges and MAC

```bash
docker run --security-opt no-new-privileges:true --security-opt seccomp=/etc/docker/seccomp/app.json myapp:1.4.2
```

`no-new-privileges` blocks setuid/file-capability escalation. The default seccomp profile blocks dangerous syscalls; custom profile only for a denied syscall the app needs (`dmesg` shows `SECCOMP` audit lines). Never `--privileged` in production.

### Pinned base digests

Tags are mutable; digests are not. Pin the manifest-list digest:

```dockerfile
FROM python:3.12-slim@sha256:REPLACE_WITH_INDEX_DIGEST
```

Resolve: `docker buildx imagetools inspect python:3.12-slim` (manifest-list `Digest:`, not a per-arch child) or `docker inspect --format '{{index .RepoDigests 0}}' myapp:1.4.2` post-push. Automate digest bumps (Renovate/Dependabot) - pinning must not mean fossilizing.

### SBOM and provenance attestations

```bash
docker buildx build --sbom=true --provenance=mode=max \
  --push -t registry.example.com/team/myapp:1.4.2 .
```

Attestations live as OCI artifacts beside the image; inspect via `docker buildx imagetools inspect <ref> --format '{{ json .SBOM }}'`. SBOM without a rebuild: `syft myapp:1.4.2 -o spdx-json`.

### Vulnerability scanning

Scan from a container (no host install, works in CI pods):

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:0.55.1 image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 myapp:1.4.2
```

Binary install: same pinned-release pattern (`trivy_0.55.1_Linux-64bit.tar.gz`, aquasecurity/trivy). Discipline:

- Fail the pipeline on fixable HIGH/CRITICAL (`--exit-code 1`, `--ignore-unfixed`); add `grype myapp:1.4.2 --fail-on high` as a second opinion (pinned binary from anchore/grype) - different vulnerability database.
- Scan the build tree too: `trivy fs --scanners vuln,secret,misconfig .` catches secrets and IaC misconfigurations pre-build. Wire gates into `ci-cd` pipelines.
- `.trivyignore` entries need justification + expiry; rescan pushed images on a schedule - clean images age into vulnerability.

## Production Runtime

### HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD ["/app", "healthcheck"]
```

- Exec form only - distroless has no shell/curl/wget; bake a `healthcheck` subcommand or copy static busybox into `/bin`.
- `--start-period` covers slow warmups; failures during it do not count toward `--retries`. Status: `docker inspect --format '{{.State.Health.Status}}' myapp`.
- Kubernetes ignores HEALTHCHECK - use liveness/readiness probes (see `kubernetes-deployment`).

### STOPSIGNAL and graceful shutdown

`docker stop` sends STOPSIGNAL (default SIGTERM), waits the grace period (default 10s; `docker stop -t 30`, Compose `stop_grace_period`), then SIGKILLs.

- Run the app as PID 1 (exec-form ENTRYPOINT) or use an init (`docker run --init`, Compose `init: true`) - shell-form entrypoints swallow signals and leak zombies.
- On SIGTERM: stop accepting work, drain in-flight requests, flush telemetry, exit 0 before the grace period ends. Daemons differ - nginx drains on SIGQUIT: `STOPSIGNAL SIGQUIT`.
- Test: `docker run -d --name t myapp:1.4.2 && time docker stop -t 30 t` - expect seconds and exit 0/143, never a routine-stop 137.

### Resource limits

```bash
docker run --memory 512m --memory-reservation 384m --memory-swap 512m \
  --cpus 1.5 --pids-limit 256 --ulimit nofile=8192:8192 myapp:1.4.2
```

- `--memory` is a hard limit: exceeding it triggers the OOM killer (exit 137, `OOMKilled=true`). `--memory-swap` sets memory+swap total; equal values disable swap.
- `--cpus` is quota throttling - latency spikes at idle-looking utilization; check `cpu.stat` throttle counters. `--pids-limit` contains fork bombs.
- Compose v2 and Swarm honor `deploy.resources`; Kubernetes equivalents are requests/limits (see `kubernetes-deployment`).

### Logging drivers

The default `json-file` driver rotates nothing and will fill the disk. Always set rotation, or use `local`:

```bash
docker run --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 myapp:1.4.2
```

- `local` rotates and compresses by default - the better host default.
- Centralized (`fluentd`, `gelf`, `syslog`, `journald`): add `--log-opt mode=non-blocking --log-opt max-buffer-size=4m` so a slow endpoint cannot stall the app.
- `docker logs` works only with `json-file`, `local`, `journald`. On Kubernetes log to stdout/stderr; aggregation via `observability` (loki).

## Debugging

### Triage commands

```bash
docker logs --tail 200 --timestamps myapp
docker inspect --format '{{.State.Status}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} restarts={{.RestartCount}} err={{.State.Error}}' myapp
docker exec -it myapp sh
docker diff myapp
```

`docker diff` shows filesystem drift - what to tmpfs under a read-only rootfs.

### nsenter

No shell in the image (distroless, scratch)? Enter its namespaces from the host as root:

```bash
PID=$(docker inspect -f '{{.State.Pid}}' myapp)
nsenter -t "$PID" -m -u -i -n -p sh
nsenter -t "$PID" -n ss -ltnp
```

### Ephemeral debug containers

Attach a fully tooled container to the target's namespaces:

```bash
docker run --rm -it --pid container:myapp --net container:myapp \
  --cap-add SYS_PTRACE nicolaka/netshoot:v0.13
```

On Kubernetes use ephemeral containers (stable since 1.25); the target's filesystem is reachable via `/proc/<pid>/root`:

```bash
kubectl debug -it pod/mypod --image=nicolaka/netshoot:v0.13 --target=myapp
ls -l /proc/1/root
```

### Failure signatures

| Signature | Meaning | First action |
| --- | --- | --- |
| exit 137 + `OOMKilled=true` | cgroup memory limit hit | raise `--memory` or fix the leak |
| exit 126 / 127 | not executable / not found | ENTRYPOINT +x, `noexec` mounts; bad CMD path |
| "no such file or directory" at exec | CRLF shebang, or glibc binary on musl/scratch | `sed -i 's/\r$//'`; rebuild static or switch base |
| "exec format error" | wrong CPU architecture | `docker buildx build --platform linux/amd64,linux/arm64` |
| x509 certificate errors | no CA bundle in scratch/distroless | copy CA certs, set `SSL_CERT_FILE` |

For pod-level manifestations (CrashLoopBackOff, ImagePullBackOff) continue in `kubernetes-troubleshooting`.

## Compose Production Patterns

Compose basics belong to `docker-patterns`; this is the production hardening overlay:

```yaml
services:
  app:
    image: registry.example.com/team/myapp:1.4.2
    restart: unless-stopped
    read_only: true
    tmpfs: ["/tmp:rw,noexec,nosuid,nodev,size=64m"]
    cap_drop: ["ALL"]
    cap_add: ["NET_BIND_SERVICE"]
    security_opt: ["no-new-privileges:true"]
    healthcheck:
      test: ["CMD", "/app", "healthcheck"]
      interval: 30s
      timeout: 3s
      start_period: 15s
      retries: 3
    deploy:
      resources:
        limits: { cpus: "1.5", memory: 512M }
    logging:
      driver: json-file
      options: { max-size: 10m, max-file: "3" }
    depends_on:
      db: { condition: service_healthy }
```

- Pin `image:` by tag plus digest; never `latest`. `depends_on.condition: service_healthy` requires a healthcheck on the dependency.
- `restart: unless-stopped` survives host reboots; add `init: true`, `stop_grace_period: 30s` per STOPSIGNAL.
- Validate with `docker compose config`; deploy with `docker compose up -d --wait` to block until healthy.

Beyond the container (alerting, backup, rollout strategy): `production-readiness`.

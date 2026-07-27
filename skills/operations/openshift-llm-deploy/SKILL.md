---
name: openshift-llm-deploy
description: REQUIRED for questions about currently deployed LLMs, model Routes or NodePorts, GPU usage or capacity, node capacity, as well as deploy, verify, inventory, or remove a Hugging Face model on the Kubernetes cluster hosting this Hermes sandbox. Use direct standard vLLM when requested, otherwise prefer DynamoGraphDeployment and automatically fall back to standard vLLM only after an explicit Dynamo failure. Resolve the newest stable vLLM release to a matching Docker Hub tag and retain the chart default when that tag is unavailable.
---

# Local Cluster LLM Deployment

Use this skill for model-serving work on the cluster that hosts this Hermes
Sandbox. `oc` and `kubectl` are wrappers around the projected local
service-account token. Do not request an external login command, kubeconfig,
or user credentials for this local-cluster path.

The wrappers are already installed at `/chart-bin/oc` and
`/chart-bin/kubectl` and are on `PATH`. Never download, install, or use a
package manager for Kubernetes clients. Before reporting a cluster-access
blocker, run:

```sh
/chart-bin/oc whoami
/chart-bin/oc auth can-i create deployments --all-namespaces
```

They preserve end-to-end Kubernetes API TLS through OpenShell. Never add
`--insecure-skip-tls-verify` or try to bypass the sandbox proxy.

This skill is intentionally conservative: it requests Hugging Face access only
through a Kubernetes Secret, validates scheduling and storage first, asks for
one explicit confirmation before cluster changes, and reports a verified Route
or NodePort endpoint after deployment.

## Guardrails

- Never ask the user to paste an HF token into normal chat, save it to a
  workspace file, place it in a ConfigMap, or include it in a command
  transcript. The agent has no Secret-read permission and must never attempt
  to inspect a credential value.
- Read `${HERMES_HOME}/skills/operations/openshift-llm-deploy/hf-token-intake.yaml` before
  handling a Hugging Face model. When `enabled: true` and
  `requireTokenForHuggingFaceModels: true` (the chart default), invoke the
  `clarify` tool as the first assistant action before any text response,
  Hugging Face metadata request, cluster capability check, manifest rendering,
  or deployment confirmation. Use this exact question and no choices:

  ```text
  [[HERMES_HF_TOKEN_SECRET]] This Hugging Face deployment needs an access token. Paste it into the masked field. It is stored directly as a Kubernetes Secret and is never added to this conversation. A one-time download Job deletes the token from that Secret after its terminal download result; the serving model never receives the token.
  ```

  The WebUI replaces that clarification with a password-style field. Its only
  valid response is `HF_SECRET_READY:<secret-name>`. Accept the response only
  when `<secret-name>` exactly matches `secretName` in `hf-token-intake.yaml`.
  Treat any other response as an incomplete secure-token flow and ask the user
  to retry the masked prompt. The raw token must never enter the model context,
  session transcript, terminal, or workspace. Do not offer a normal-chat
  token alternative, a manual Secret command, or an alternative token-creation
  workflow. A WebUI-originated deployment request may include the valid
  `HF_SECRET_READY:<secret-name>` prefix together with the original request;
  treat that as a completed masked-token response and continue with the
  remaining request without re-prompting.
- When `requireTokenForHuggingFaceModels: false`, use the masked flow only for
  a gated/private model. For a public model, an anonymous download is allowed.
  When the chart has `hf-token-intake.enabled: false`, ask only for the name
  of an existing namespace-local Secret with the configured `secretKey`.
- Default the target namespace to the namespace returned by
  `/chart-bin/oc project -q`. It contains the chart-provisioned `llm-runner`
  ServiceAccount used by the one-time downloader and standard vLLM fallback.
  While the chart-managed masked token flow is enabled, this is the only valid
  target namespace: the writer and the downloader's Secret-delete permission
  are deliberately namespace-local. An explicitly requested namespace is
  supported only when the chart token flow is disabled and that namespace has
  its own compatible `llm-runner` ServiceAccount and Secret management.
- First use Dynamo only when `DynamoGraphDeployment` is served at
  `nvidia.com/v1beta1` and the local service account can create it. Never
  install or upgrade Dynamo from this skill.
- The Dynamo vLLM runtime is the default Dynamo backend because it has the
  broadest model coverage. Select TensorRT-LLM only when the exact model has a
  known compatible upstream engine configuration and the full
  `--extra-engine-args <path>` value is available. Do not guess an engine
  configuration from a Hugging Face name or tags.
- Use the chart-rendered, version-pinned Dynamo runtime images from
  `dynamo-defaults.yaml`. Do not use `latest`. Prefer a digest when one is
  supplied by the target registry. The expected defaults are:

  ```text
  docker.io/anguda/ai-dynamo:v1.3.0-rc1-vllm-nvfp4@sha256:190d9e5055bde66f6031bd32aec12184faaf31390ebfd7a3a32c12154e8eb849
  docker.io/anguda/ai-dynamo:v1.3.0-rc1@sha256:26ca4e7a8e3860441078bfa7d308854aefb401abf7bb9992ff84a7d83d74f18b
  docker.io/vllm/vllm-openai:v0.20.0-cu130-ubuntu2404@sha256:aff65d7198dd284c37dd0a18a606544cc5e92bfb0d5eb608b77e8b8f1c6b8b0d
  ```

- For every direct standard-vLLM deployment and Dynamo fallback, run the
  chart-provided resolver. It reads the latest stable release from
  `api.github.com/repos/vllm-project/vllm/releases/latest`; if that shared
  unauthenticated API quota is exhausted, it follows GitHub's public
  `/vllm-project/vllm/releases/latest` redirect instead. It verifies that the
  exact `vllm/vllm-openai:<release-tag>` exists on Docker Hub, then uses that
  tag. Do not use `latest` or construct a tag manually. If the release cannot
  be resolved or Docker Hub does not yet publish the tag, use the configured
  `standardVllmImage` unchanged and report `VLLM_IMAGE_REASON`.
- Use the existing `vllm-deployment.yaml` template for an explicitly requested
  direct standard-vLLM deployment, when Dynamo is unavailable, or after an
  explicit Dynamo failure. Do not silently move a pending model download to
  the standard-vLLM path.
- The standard vLLM fallback template is immutable after rendering. Its
  `VLLM_ARGS` value may contain only YAML vLLM argument-list entries. Never add
  `command:`, shell code, `set`, `pipefail`, image substitutions, offline-mode
  environment flags, or a hand-written model-download loop. The launcher
  rejects those changes before `oc apply`.
- Ask for an explicit confirmation immediately before `oc apply`, `oc delete`,
  or namespace creation. The confirmation must cover the Dynamo attempt and,
  when selected, automatic cleanup of the failed DGD followed by a standard
  vLLM fallback while retaining the model-cache PVC.
- Do not deploy a model during chart installation. This skill runs only in
  response to a user request.
- Never report a generic terminal failure for a model deployment. Run the
  bounded diagnostic helper and report its `DIAGNOSIS_CAUSE`, affected
  resource, and `DIAGNOSIS_ACTION`. The launcher performs at most one safe
  retry for a transient Kubernetes API apply error. Do not repeat an apply
  after a manifest, scheduling, storage, image-pull, or runtime failure until
  the reported cause has changed.

## Status-Only Workflow

When the user asks only for deployed models, model Routes or NodePorts, cluster
status, GPU availability, node capacity, or workload placement, this skill is
mandatory. As the first action, load this skill and execute the following
command before answering. Make no cluster changes and do not ask for an HF
token or deployment confirmation:

```sh
SKILL_ROOT="${HERMES_HOME}/skills/operations/openshift-llm-deploy"
"$SKILL_ROOT/scripts/cluster-status.sh"
```

Use `--namespace "$NAMESPACE"` only when the user explicitly asks to narrow
the model inventory to one namespace. The default command queries every
namespace. Report the `GPU_NODES` and
`GPU_WORKLOADS` tables as scheduled **GPU request** capacity, not GPU-memory
telemetry. The inventory covers direct DynamoGraphDeployments and vLLM/Hermes
Deployments, then reports GPU model-server candidates discovered from running
pods and a model argument or environment hint when the pod exposes one. It
also reports only model-serving `MODEL_ROUTE` and `MODEL_NODEPORT` exposure;
do not present the Hermes WebUI Route as a model endpoint. Do not claim a model
is healthy from this status view alone; health is verified only through the
endpoint workflow below.

## Dynamo-First Deploy Workflow

Use the assets below; they avoid long, repetitive tool loops:

```text
${HERMES_HOME}/skills/operations/openshift-llm-deploy/dynamo-defaults.yaml
${HERMES_HOME}/skills/operations/openshift-llm-deploy/templates/dynamo-vllm-graph-deployment.yaml
${HERMES_HOME}/skills/operations/openshift-llm-deploy/templates/dynamo-tensorrtllm-graph-deployment.yaml
${HERMES_HOME}/skills/operations/openshift-llm-deploy/scripts/render-template.py
${HERMES_HOME}/skills/operations/openshift-llm-deploy/scripts/list-storage-classes.sh
${HERMES_HOME}/skills/operations/openshift-llm-deploy/scripts/dynamo-first-deploy.sh
${HERMES_HOME}/skills/operations/openshift-llm-deploy/scripts/resolve-vllm-image.sh
${HERMES_HOME}/skills/operations/openshift-llm-deploy/scripts/deploy-model.sh
${HERMES_HOME}/skills/operations/openshift-llm-deploy/scripts/diagnose-deployment.sh
${HERMES_HOME}/skills/operations/openshift-llm-deploy/scripts/verify-openai-endpoint.sh
${HERMES_HOME}/skills/operations/openshift-llm-deploy/scripts/remove-model.sh
```

### 1. Establish the target and Dynamo capability

```sh
NAMESPACE=$(/chart-bin/oc project -q)
SKILL_ROOT="${HERMES_HOME}/skills/operations/openshift-llm-deploy"
OBSERVATION_TIMEOUT_SECONDS=$(awk -F ': ' '/^observationTimeoutSeconds:/ {print $2; exit}' "$SKILL_ROOT/dynamo-defaults.yaml")
VERIFICATION_TIMEOUT_SECONDS=$(awk -F ': ' '/^verificationTimeoutSeconds:/ {print $2; exit}' "$SKILL_ROOT/dynamo-defaults.yaml")
/chart-bin/oc api-resources --api-group=nvidia.com -o wide
/chart-bin/oc auth can-i create dynamographdeployments.nvidia.com -n "$NAMESPACE"
"$SKILL_ROOT/scripts/check-gpus.sh"
"$SKILL_ROOT/scripts/list-storage-classes.sh"
```

Treat Dynamo as available only when the API discovery output shows
`dynamographdeployments` with API version `v1beta1` and `can-i` returns `yes`.
If either check fails, state that Dynamo cannot be used on this cluster and
prepare the standard vLLM path instead. Do not attempt a legacy v1alpha1 DGD:
its schema differs from these templates.

Select one GPU node with enough allocatable GPUs and keep both the Dynamo
frontend and worker on that node. This avoids an RWO model-cache PVC attaching
to different nodes. Do not guess a storage class or a node name.

Set `STORAGE_CLASS` only from the inventory helper output. It returns every
class as `STORAGE_CLASS_OPTION`, marks the cluster default with
`DEFAULT=true`, and reports it separately as `STORAGE_CLASS_DEFAULT`.

When `STORAGE_CLASS_COUNT` is greater than one, do not select a class
automatically. Ask the user which listed storage class to use before showing a
deployment plan or asking for deployment confirmation. Present the reported
cluster default as the first option, explicitly labeled **cluster default**.
If there is exactly one reported default, the user may reply `default`; resolve
that reply to its class name and still pass the class explicitly to the
wrapper. If the inventory reports no default or multiple defaults, state that
clearly and require a class-name choice. Do not treat a past deployment's class
or a general storage recommendation as the user's choice.

When exactly one storage class exists, select that class and state it in the
plan. Always pass the chosen class explicitly; never omit
`--storage-class` and rely on implicit provisioning.

After the user chooses a class, validate it against the chosen node. For
example, `lvms-nvme` uses the `topolvm.io` node-local provisioner and
`WaitForFirstConsumer`, so it requires enough advertised
`CSIStorageCapacity` for the requested PVC size. A class with RWX semantics
must be chosen only when the workload needs shared filesystem access.

Before asking for deployment confirmation, inspect the proposed GPU node and
storage placement:

```sh
/chart-bin/oc get node "$NODE_NAME" \
  -o jsonpath='{range .spec.taints[*]}{.key}{"="}{.value}{":"}{.effect}{"\n"}{end}'
/chart-bin/oc get csistoragecapacity -A \
  -o custom-columns=NAMESPACE:.metadata.namespace,SC:.storageClassName,CAPACITY:.capacity,NODE:.nodeTopology.matchLabels.topology\.topolvm\.io/node
```

Never schedule model workloads on a node tainted
`node.ocs.openshift.io/storage=true:NoSchedule`; this chart deliberately does
not add that toleration. If the chosen node-local class has no capacity object
for the selected node, return to storage-class and node selection rather than
substituting another class without the user's approval. The deployment wrapper
enforces these checks again before it creates a PVC or downloader Job.

### 2. Secure Hugging Face access, inspect the model, and choose a backend

If the secure-token gate is enabled, complete it first. Then inspect permitted
Hugging Face metadata, model configuration, checkpoint size,
precision, and minimum GPU count. Explain the selected node, GPU count, PVC
size, expected context window, runtime image, and exposure before applying.

Use this selection order:

1. If the user explicitly requests a non-Dynamo or direct vLLM deployment,
   choose `standard-vllm`. The wrapper resolves the latest stable GitHub vLLM
   release and uses `docker.io/vllm/vllm-openai:<release-tag>` only if Docker
   Hub confirms that exact tag. Otherwise it uses the chart default and emits
   the fallback reason.
2. If Dynamo is available and the model has no known TensorRT-LLM engine
   configuration, choose the Dynamo vLLM template. Resolve an exact
   `modelRuntimeOverrides.<model-id>.dynamoVllmRuntimeImage` first, then use
   `vllmRuntimeImage` from `dynamo-defaults.yaml`.
3. Choose the Dynamo TensorRT-LLM template only when an upstream, matching
   `--extra-engine-args` path is known. That path must be present in the exact
   override or default `tensorrtllmRuntimeImage`. Include it exactly as
   `TRTLLM_ENGINE_ARGS`.
4. When Dynamo is unavailable or returns an explicit DGD/pod/endpoint failure,
   automatically use standard vLLM with the resolver-selected image. A
   `pending` result means the model is still downloading or initializing; do
   not call it a failure.

Read `dynamo-defaults.yaml` for the chart-selected Dynamo runtime images,
standard-vLLM default image, and short observation timeout. Do not replace
these pins with `latest`. The resolver may replace only the standard-vLLM image
with a verified release tag; if no matching tag is published, it
leaves the configured default image in place. A model-specific Dynamo image may
be selected only when it is an exact `modelRuntimeOverrides` match or after
verifying compatibility against the upstream image tag. If an image pull
credential is required, ask for the name of an existing namespace-local
image-pull Secret, not its value. Do not create registry credentials in chat
or a workspace file.
Render `DYNAMO_IMAGE_PULL_SECRETS` as `[]` when no pull Secret is required, or
as `[ {"name": "<existing-pull-secret>"} ]` when one is approved.

On OpenShift, the launcher creates a per-release RoleBinding for the Dynamo
operator service account `${RELEASE}-k8s-service-discovery` to use
`system:openshift:scc:anyuid` before applying the DGD. This is the scoped,
declarative equivalent of:

```sh
oc adm policy add-scc-to-user anyuid -z "${RELEASE}-k8s-service-discovery" -n "$NAMESPACE"
```

Do not run that `oc adm` command directly: it would require the agent to edit a
cluster-wide SCC object. The RoleBinding grants the same SCC to only this
release's generated service account and is removed on Dynamo fallback or model
uninstall.

### 3. Download once, then delete the secure token Secret

For every Hugging Face model when the chart default is enabled, use the masked
token flow described in **Guardrails**. It returns the chart-owned
namespace-local Secret name, not a token. The wrapper renders a node-pinned
model-download Job that is the **only** workload with an `HF_TOKEN` Secret
reference. It writes the checkpoint under `/models/model` on the release PVC,
then removes the `HF_TOKEN` key from the fixed chart-owned Secret with a
resource-name-scoped Role. The empty placeholder remains so the masked writer
can safely patch only that fixed object for a later deployment.
The Dynamo and standard-vLLM serving manifests receive only `/models/model`,
never an HF token or Secret reference.

The Job removes the token value after a successful download and also from its
terminal-failure path. If it is still running when the bounded observation
window ends, report the Job as pending and do not start a serving workload; the
Job will perform its own deletion on completion or failure. Do not use `oc get
secret`, `oc extract`, `--from-literal`, or `envFrom` for credentials.

### 4. Use the chart-managed deployment wrapper

Do not construct YAML, invoke `render-template.py`, or call `oc apply` from
the model run. `deploy-model.sh` does all rendering, validation, immutable
image selection, secure Secret reference construction, SCC handling, endpoint
verification, and cleanup from its fixed implementation. It is the only
allowed deploy command.

The wrapper defaults to Dynamo vLLM. Use `--deployment-mode standard-vllm` for
an explicit direct standard-vLLM request; otherwise use
`--deployment-mode dynamo`. It uses a model-specific Dynamo runtime override
from `dynamo-defaults.yaml` when present. Select `--dynamo-backend trtllm`
only with a known `--trtllm-engine-args` value. A conservative default
`--max-model-len` is `32768`.

The chart's Dynamo frontend receives only the served model name. Both Dynamo
workers and standard vLLM use the local `/models/model` path only after the
isolated authenticated download has completed and removed the token value.

### 5. Confirm one controlled deployment attempt

Before changing the cluster, show a concise summary that includes:

- target namespace and selected node;
- user-selected storage class (and whether it was the cluster-default option)
  and, for node-local storage, the verified
  `CSIStorageCapacity` on that node;
- deployment mode, Dynamo backend when applicable, and the exact selected
  standard-vLLM image plus `VLLM_IMAGE_SOURCE`/`VLLM_RELEASE_TAG` or
  `VLLM_IMAGE_REASON`;
- GPU, memory, cache-PVC, and context-window values;
- whether a gated-model Secret is referenced by name;
- whether an external Route/NodePort will be created; and
- that a confirmed explicit Dynamo failure will delete only the DGD and its
  operator-owned components, retain the PVC, and apply the standard vLLM
  fallback automatically.

Require confirmation. On confirmation, run this wrapper exactly once. Add
`--expose` only when the user approved an external endpoint:

```sh
sh "$SKILL_ROOT/scripts/deploy-model.sh" \
  --namespace "$NAMESPACE" \
  --release "$RELEASE" \
  --model "$MODEL_ID" \
  --platform "$PLATFORM" \
  --node "$NODE_NAME" \
  --gpus "$GPU_COUNT" \
  --storage-class "$STORAGE_CLASS" \
  --pvc-size "$PVC_SIZE" \
  --memory-request "$MEMORY_REQUEST" \
  --memory-limit "$MEMORY_LIMIT" \
  --hf-secret "$HF_SECRET_NAME" \
  --max-model-len "$MAX_MODEL_LEN" \
  --deployment-mode "$DEPLOYMENT_MODE" \
  --allow-fallback \
  --expose
```

Never call `./scripts/deploy.sh`, `/scripts/deploy.sh`, a guessed wrapper
path, `render-template.py`, `dynamo-first-deploy.sh`, or `oc apply` after this
command. If the output lacks `DEPLOYMENT_RESULT`, run exactly one read-only
diagnosis:

```sh
sh "$SKILL_ROOT/scripts/diagnose-deployment.sh" \
  --namespace "$NAMESPACE" --release "$RELEASE"
```

Then report the diagnosis and stop. Do not retry or claim deployment progress.

The launcher deliberately observes for a short, chart-configured period so a
large model download cannot exhaust the terminal tool budget. It reports one
of these markers:

```text
DYNAMO_RESULT=ready
DYNAMO_RESULT=pending
DYNAMO_RESULT=failed
FALLBACK_RESULT=ready
FALLBACK_RESULT=pending
FALLBACK_RESULT=failed
STANDARD_VLLM_RESULT=ready|pending|failed
VLLM_IMAGE=docker.io/vllm/vllm-openai:<release-tag>|<chart-default>
VLLM_IMAGE_SOURCE=github-latest-release|chart-default
VLLM_RELEASE_TAG=vX.Y.Z
VLLM_IMAGE_REASON=...
DEPLOYMENT_RETRY=one-safe-api-retry-after-transient-apply-error
DIAGNOSIS_CAUSE=...
DIAGNOSIS_ACTION=...
VERIFY_SIMPLE_COMPLETION=passed
VERIFY_TOOL_CALL=passed|not-observed|not-supported-or-rejected
ENDPOINT=https://...
SERVICE_ENDPOINT=http://...svc.cluster.local:8000
DEPLOYMENT_PHASE=...
DEPLOYMENT_OBSERVATION=...
MODEL_DOWNLOAD_RESULT=ready|pending|failed
HF_TOKEN_SECRET=cleared-after-model-download|retained-only-while-download-is-running
DEPLOYMENT_RESULT=ready|pending|failed
```

If it returns `pending`, report the live resource names and continue with a
single later status observation. Do not create a second DGD, deploy vLLM, or
claim that Dynamo failed merely because it was not immediately ready.
If `DYNAMO_RESULT=failed`, `FALLBACK_RESULT=failed`, or
`STANDARD_VLLM_RESULT=failed`, report the bounded diagnosis before proposing
another change. A Dynamo request automatically applies standard vLLM only
after an unavailable Dynamo CRD or explicit DGD/pod/endpoint failure. It is
never used to hide an RBAC, manifest, storage, or registry-credential error.

## Interactive Deployment Result Contract

Do not narrate internal edits, claim background progress, or issue extra
`oc apply`/patch commands after confirmation. `deploy-model.sh` is the only
deployment command. It emits bounded phase and observation markers while it
works, then returns exactly one final `DEPLOYMENT_RESULT`.

Translate that result into one clear response:

- **Ready:** backend, selected node, verified completion/tool-call outcome, and
  Route or NodePort URL.
- **Pending:** current resource observation, why it is pending, and one later
  read-only status check. Do not redeploy.
- **Failed:** backend, affected resource, `DIAGNOSIS_CAUSE`, and
  `DIAGNOSIS_ACTION`. Do not attempt a new manifest or runtime image without a
  new user confirmation.

### 6. Verify and report the endpoint

The launcher uses a temporary port-forward and waits up to the configured
verification window after readiness. It checks `/health`, `/v1/models`, an
OpenAI-compatible sample completion, and a forced tool-call request before it
emits `DYNAMO_RESULT=ready`, `FALLBACK_RESULT=ready`, or
`STANDARD_VLLM_RESULT=ready`. A model may not support
tool calling; report `VERIFY_TOOL_CALL=not-observed` or
`VERIFY_TOOL_CALL=not-supported-or-rejected` without calling an otherwise
healthy endpoint failed. On OpenShift, report the live Route in
`ENDPOINT`. On Kubernetes, report the NodePort only after the service patch and
a schedulable node address are both present. Include the selected backend,
advertised model ID, completion result, tool-call result, and endpoint in the
final report.

## Remove Workflow

For delete or uninstall requests, inventory both possible serving paths before
asking for confirmation:

```sh
SKILL_ROOT="${HERMES_HOME}/skills/operations/openshift-llm-deploy"
"$SKILL_ROOT/scripts/remove-model.sh" \
  --namespace "$NAMESPACE" \
  --release "$RELEASE" \
  --platform "$PLATFORM" \
  --action inventory
```

State exactly what the inventory found. The removal scope is the named
DynamoGraphDeployment, its operator-owned components, and only resources with
`app.kubernetes.io/instance=$RELEASE`: standard Deployment, StatefulSet, Job,
Service, Route, HPA, ServiceMonitor, and optional model-cache PVC. The
chart-managed HF token Secret is normally already gone before the serving
workload starts; removal never attempts to recreate, read, or retain it.

Require a final confirmation. For cache removal, require a separate explicit
confirmation that the model weights may be permanently removed. Then execute:

```sh
"$SKILL_ROOT/scripts/remove-model.sh" \
  --namespace "$NAMESPACE" \
  --release "$RELEASE" \
  --platform "$PLATFORM" \
  --action delete \
  --confirm
```

Add `--purge-storage` only after the user explicitly approved PVC deletion.
Report `REMOVE_RESULT`, `REMOVE_STORAGE`, and
`REMOVE_HF_TOKEN_SECRET=not-present-or-unmanaged`.
Never remove an entire namespace unless the user explicitly confirms namespace
deletion.

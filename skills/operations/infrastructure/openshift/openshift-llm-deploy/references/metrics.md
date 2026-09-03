# Cluster metrics reference

PromQL recipes and label semantics for the cluster's built-in monitoring stack.
Read this before composing a query that `gpu-metrics.sh` does not already
answer. Run queries with:

```sh
"$SKILL_ROOT/scripts/query-metrics.sh" --query 'PROMQL'
```

## Label semantics (read first)

DCGM metrics carry two independent sets of workload labels:

| Label set | Identifies |
| --- | --- |
| `namespace`, `pod`, `container` | the DCGM exporter pod itself, always in the GPU operator namespace |
| `exported_namespace`, `exported_pod`, `exported_container` | the workload actually consuming the GPU |

Selecting on `namespace` therefore returns an empty result for any workload
namespace. Always use `exported_namespace`.

A GPU with no consumer has empty `exported_*` labels. Filter those out with
`exported_namespace!=""` when reporting attributed usage, or keep them to show
idle hardware.

Other useful DCGM labels: `gpu` (index on the node), `Hostname` (node),
`modelName` (for example `NVIDIA B200`), `UUID`.

Dynamo and vLLM metrics come from user-workload monitoring, so they use the
normal `namespace` and `pod` labels, plus `model`, `model_name`, `worker_id`,
`dynamo_component`, and `dp_rank`.

## GPU telemetry (DCGM, available with no setup)

| Metric | Unit | Meaning |
| --- | --- | --- |
| `DCGM_FI_DEV_GPU_UTIL` | percent | SM utilization |
| `DCGM_FI_DEV_MEM_COPY_UTIL` | percent | memory bandwidth utilization |
| `DCGM_FI_DEV_FB_USED` / `DCGM_FI_DEV_FB_FREE` | MiB | framebuffer memory used / free |
| `DCGM_FI_DEV_POWER_USAGE` | watts | board power draw |
| `DCGM_FI_DEV_GPU_TEMP` / `DCGM_FI_DEV_MEMORY_TEMP` | celsius | die / memory temperature |
| `DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL` | bytes | NVLink traffic |
| `DCGM_FI_DEV_CORRECTABLE_REMAPPED_ROWS` | count | memory health, non-zero warrants attention |

Utilization for every GPU used by one namespace:

```promql
DCGM_FI_DEV_GPU_UTIL{exported_namespace="runai-inference"}
```

Mean utilization per pod:

```promql
avg by (exported_pod) (DCGM_FI_DEV_GPU_UTIL{exported_namespace="runai-inference"})
```

GPU memory used per pod, in GiB:

```promql
sum by (exported_pod) (DCGM_FI_DEV_FB_USED{exported_namespace="runai-inference"}) / 1024
```

Idle-but-allocated GPUs, the usual source of wasted capacity:

```promql
DCGM_FI_DEV_GPU_UTIL{exported_namespace!=""} == 0
```

Peak utilization over the last hour, to judge whether a model is really busy:

```promql
max_over_time(DCGM_FI_DEV_GPU_UTIL{exported_namespace="runai-inference"}[1h])
```

Power draw per node:

```promql
sum by (Hostname) (DCGM_FI_DEV_POWER_USAGE)
```

## Serving telemetry (Dynamo, requires the PodMonitor)

Exposed on the worker `system` port and the frontend `http` port. These return
nothing until `templates/dynamo-podmonitor.yaml` is applied to the model
namespace.

| Metric | Meaning |
| --- | --- |
| `dynamo_component_inflight_requests` | requests currently executing |
| `dynamo_request_queue`, `dynamo_work_handler_queue_depth` | queued work, sustained non-zero means saturation |
| `dynamo_component_gpu_cache_usage_percent` | KV-cache occupancy |
| `dynamo_component_total_blocks` | KV-cache blocks allocated |
| `dynamo_work_handler_time_to_first_response_seconds_*` | time to first token histogram |
| `dynamo_component_router_inter_token_latency_seconds_*` | inter-token latency histogram (frontend) |
| `dynamo_component_request_duration_seconds_*` | end-to-end request duration histogram |
| `dynamo_component_uptime_seconds` | worker uptime, resets reveal restarts |
| `vllm:generation_tokens_total` | cumulative generated tokens |
| `vllm:prompt_tokens_total` | cumulative prompt tokens |
| `vllm:e2e_request_latency_seconds_*` | engine-side latency histogram |
| `vllm:external_prefix_cache_hits_total` / `_queries_total` | prefix cache effectiveness |

Output tokens per second per model:

```promql
sum by (model) (rate(vllm:generation_tokens_total[5m]))
```

Median and p99 time to first token:

```promql
histogram_quantile(0.5, sum by (le, model) (rate(dynamo_work_handler_time_to_first_response_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le, model) (rate(dynamo_work_handler_time_to_first_response_seconds_bucket[5m])))
```

Prefix cache hit rate:

```promql
sum(rate(vllm:external_prefix_cache_hits_total[5m])) / sum(rate(vllm:external_prefix_cache_queries_total[5m]))
```

Saturation check — queued work while GPUs are busy:

```promql
sum by (pod) (dynamo_request_queue) > 0
```

## Interpretation notes

- Near-100% `DCGM_FI_DEV_FB_USED` is normal and expected for a model server.
  Inference engines preallocate the KV cache at startup, so high GPU memory
  says nothing about load. Use `dynamo_component_gpu_cache_usage_percent` for
  actual KV-cache pressure and `DCGM_FI_DEV_GPU_UTIL` for compute load.
- `DCGM_FI_DEV_GPU_UTIL` measures whether any kernel was resident, not how
  efficiently the GPU is used. An idle-but-loaded model still shows brief
  spikes.
- Instantaneous utilization on an idle model is normally 0. Prefer
  `max_over_time(...[1h])` before concluding a deployment is unused.
- Counters (`_total`) must be wrapped in `rate()` or `increase()`; a raw
  counter value is meaningless.

## Failure modes

| Symptom | Cause |
| --- | --- |
| Empty result for a namespace that clearly has GPU pods | selected on `namespace` instead of `exported_namespace` |
| HTTP 401/403 from the query script | the service account lacks `cluster-monitoring-view` (`rbac.metricsReader.enabled`) |
| GPU metrics present, serving metrics empty | the PodMonitor is missing, or user-workload monitoring is disabled cluster-wide |
| Serving metrics empty right after applying the PodMonitor | scrape interval is 30s; wait one or two intervals |
| Pod appears in `cluster-status.sh` but not here | the pod requests GPUs but is not yet running, or is not scheduled on a DCGM-monitored node |

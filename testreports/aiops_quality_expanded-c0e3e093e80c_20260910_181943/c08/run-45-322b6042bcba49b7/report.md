## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 异常状态: `CrashLoopBackOff`; 容器 `app` 最后一次终止原因: `OOMKilled`; 退出码: `137` (fact-8063057e72b4, fact-d358236d6bf5, fact-caaccbff8557) | 确立直接故障现象：进程因超出资源限制被系统终止。 |
| 2 | K8s Config | Kubernetes | 容器 `app` 硬内存限制 (`resource_limit.memory`): `64Mi` (fact-2560bd7fbbae) | 确立 OOM 触发的阈值边界。 |
| 3 | Logging | Elasticsearch | 8 条同模日志 (fact-14115bed0d4c 等): 在 2026-09-11 00:04:19 至 00:10:10 期间，日志字段 `allocated_mib` 从 `38` 降至 `28` (min: 8.0, max: 38.0)；HTTP 状态码 `200`。 | 揭示应用逻辑：服务在处理请求时存在显著的内存分配行为，且存在内存波动特征。 |
| 4 | Tracing | Deepflow | 9 次等效 L7 Flow (fact-a86dfb432a20 等): 针对 `GET /work` 端点，响应码 `200`；包含 trace_id `30373b937cd191bff8b812aa25074a6b` 等。 | 确认触发上述日志记录的具体流量路径为 `/work` 接口。 |
| 5 | K8s State | Kubernetes | 容器 `app` 重启计数 (restart_count): `26` (fact-f296e558cdc2) | 确认故障处于高频循环状态。 |
| 6 | Metric | Prometheus | `container_memory_working_set_bytes` 当前值: `66453504` bytes (~63.36 MiB) (fact-0b1e121d889b); `kube_pod_container_status_last_terminated_reason` 显示 `OOMKilled` (fact-622d2633b49d) | 提供崩溃前的最新资源快照，确认使用量已逼近 64Mi 硬限制。 |

**证据关联说明**：
证据 1、2、6 从 Kubernetes 和 Metrics 维度确认了“内存占用达到 64Mi 限制”与“被 OOMKilled”之间的因果关系。证据 3、4 进一步定位到 `GET /work` 接口是触发该内存分配行为的代码路径（日志中出现内存分配记录，Tracing 确认该接口调用存在且成功），证实应用逻辑是 OOM 的直接诱因。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑主动分配内存 (GET /work 请求) → 内存使用量突破 64 MiB 硬限制 → 触发 OOMKilled (Exit Code 137) → Pod 进入 CrashLoopBackOff 频繁重启
```

### 根因结论

**已确认根因**：
应用代码中存在针对 `GET /work` 端点的内存分配逻辑，其分配的内存空间最大可达 **38 MiB**（结合上下文及当前 Working Set 63.36 MiB，加上基础开销极易突破 **64 MiB** 的容器内存硬限制）。当内存使用超过该限制时，Linux OOM Killer 强制终止了进程（证据 1, 2, 3, 4, 6）。

**支持证据**：
- **内存越界**：容器配置的硬限制为 `64Mi` (证据 2)；崩溃前 Working Set 已高达 `~63.36 MiB` (证据 6)；OOMKilled 状态明确 (证据 1)。
- **代码行为**：日志显示应用在处理 `/work` 请求时执行了 `allocated_mib` 操作 (证据 3)；Deepflow 流量证实大量 `GET /work` 请求返回 200，说明这些请求成功触发了上述逻辑 (证据 4)。

**未知/需补充**：
- 首次 OOMKilled 的具体触发时间点缺失（证据 1 仅显示状态）。
- 缺乏历史数据以判断是否存在内存泄漏趋势，当前现象表现为单次请求或短时间内分配的内存累积导致的越界。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 28.7s
├─ 并发证据采集: 132.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 132.5s (Evidence 124.0s, RCA 8.3s)
└─ 汇总总结: 15.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime, pod-oomkilled

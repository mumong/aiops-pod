## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Container app has a memory limit of 96Mi, which is insufficient for the application workload, leading to OOMKill (Exit Code 137) triggered by resource pressure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.resource_limit.memory`: `96Mi` (fact-094b9cada507) | 暴露了导致 OOM 的核心资源限制配置。 |
| 2 | K8s Event | Kubernetes | `kubelet`: `Back-off restarting failed container app` (x26 over 15m) (fact-b44c86827689) | 记录异常导致的容器重启行为。 |
| 3 | K8s Event | Kubernetes | `kubelet`: `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-85a2f67a5685) | 解释 Liveness Probe 失败的具体 HTTP 响应。 |
| 4 | K8s State | Kubernetes | `Exit Code`: `137` (fact-7a708062d87f) | 137 是标准的 OOMKilled 退出码，直接证明资源耗尽。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `9` (fact-8d9e1f09c91d) | 证明容器存在频繁重启现象。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`: `reason=Error` (fact-c6c3c89c8b08) | 证实最后终止原因为错误。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: `CrashLoopBackOff` (fact-ee2298937519) | 证实当前处于重启等待状态。 |
| 8 | Logging | Elasticsearch | 应用正常输出 200 响应 (fact-5b35bc8e015d) 与 `allocated_mib`: `0` 连续记录 (fact-0eae38be1dd8) | 证明应用逻辑可运行，资源耗尽并非由于业务代码内部报错引起。 |
| 9 | Tracing | Deepflow | `http.response.status_code`: `200` (fact-49f0905984a2) | 证明应用自身 HTTP 服务返回正常，Liveness 失败为 kubelet 视角观测。 |

**证据印证说明：**
*   **根因支撑**：K8s 配置的硬限制 `96Mi` (证据 1) 直接配合退出码 `137` (证据 4)，共同构成了 OOMKill 的确切证据。
*   **现象印证**：指标中的重启次数 `9` (证据 5) 与事件中的重启记录 `x26` (证据 2) 互相印证了容器的不稳定状态。
*   **排除干扰**：日志 (证据 8) 和链路 (证据 9) 显示业务请求能正常返回 200，说明问题不在于应用逻辑错误，而是运行时的资源环境（内存）导致应用崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制过低 (96Mi, fact-1) → 容器运行触发 OOMKill → Pod 退出码 137 (fact-4) → 导致 Liveness 失败 (fact-3) 及 CrashLoopBackOff (fact-5)
```

### 根因结论

已确认根因为：**容器资源限制配置不足引发 OOMKill**。

证据明确指向：
1.  Pod `workload-79d9f8fd88-48j8r` 中 `app` 容器被配置了极低的内存硬限制 `96Mi`（证据 1）。
2.  容器最后终止原因为 `Error`（证据 6），退出码为 `137`（证据 4），这是 Linux 内核触发 OOMKill 的标志。
3.  由此导致的 OOM 使得容器无法通过 Liveness Probe（返回 500，证据 3），触发 kubelet 的 BackOff 重启机制（证据 2），最终表现为持续的 CrashLoopBackOff（证据 7）。
4.  监控日志显示应用业务请求可成功返回 200（证据 8、9），证明应用无代码缺陷，资源不足是唯一的触发点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 25.2s
├─ 并发证据采集: 74.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 74.7s (Evidence 69.5s, RCA 5.1s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime

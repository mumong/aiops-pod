## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc (aiops-case-09) 持续返回 NotReady，Ready 状态为 False |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy 4m1s (x1558 over 78m) kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` | 直接证明就绪探针因返回 503 失败，是导致 Pod 未就绪的直接事件 |
| 2 | K8s State | Kubernetes | `Pod status: Running`, `Ready: False (ContainersNotReady: app)`, `Restart count: 0` | 确认容器进程处于运行状态但未通过就绪检查，且未发生重启 |
| 3 | K8s Event | Kubernetes | `Annotations: cni.projectcalico.org/podIP: 172.16.104.16/32` | 确认网络连通性配置正常，排除 CNI 插件导致的网络不可达 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` (sample_count=1) | 量化证明容器实例在观测窗口内稳定存活，排除了因 CrashLoopBackOff 导致的频繁重启 |
| 5 | Logging | Elasticsearch | `event=error, message="dependency unavailable", http_status=503, path="/work"` (Occurrence: 8) | 提供应用内部视角的错误原因（依赖不可用），证明应用代码逻辑主动返回了 503 |
| 6 | Tracing | Deepflow/Tempo | `http.response.status_code: 503` (`GET /work`, `service: aiops-lab-workload`), `trace_id: 3cfa8efe6e08de7a7e38cde3bae0f417` | 从链路追踪层面独立观测到相同的路由端点返回 503，与日志错误原文相互印证 |

证据互证说明：
- 证据 1（事件）与证据 6（追踪）共同锁定了故障点：Pod 内的 `GET /work` 请求因内部业务逻辑返回了 503，导致 kubelet 的健康检查探针（Readiness Probe）判定为失败。
- 证据 5（日志）揭示了具体的应用层原因（"dependency unavailable"），解释了探针返回 503 的根因。
- 证据 2、4、3 排除了其他常见原因：进程未崩溃（Restart=0）、网络已分配（IP 正常），确认为应用逻辑层面的持续失败。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖不可用 → 应用标记内部状态为 readiness_fail → 应用代码对探针端点返回 HTTP 503 → kubelet 判定 Probe Failed → Pod 持续 NotReady
```

### 根因结论

**已确认根因：应用代码逻辑主动将自身标记为 'readiness_fail' 状态。**

该根因由以下事实链支撑（引用自输入中的 `formal_rca` 及上述证据）：
1. **触发条件**：应用依赖的下游服务不可用或响应失败（由日志事实 `fact-386b2f1c4fcd` 中的 `"dependency unavailable"` 证实）。
2. **故障机制**：应用代码内部状态机根据下游状态将其标记为 `readiness_fail`。
3. **直接表现**：就绪探针（Readiness Probe）对 `/work` 端点发起 HTTP 请求时，收到了应用的 `HTTP 503` 响应（由追踪事实 `fact-1268c99df0a8`、`fact-0ad8c440336d` 及事件事实 `fact-c493c315fa67` 证实）。
4. **最终现象**：Kubelet 因探针持续返回 503，判定容器不健康（ContainersNotReady），从而导致 Pod 处于 `NotReady` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 4.0m
├─ 问题定位: 13.1s
├─ 并发证据采集: 214.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 214.3s (Evidence 206.2s, RCA 7.8s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed

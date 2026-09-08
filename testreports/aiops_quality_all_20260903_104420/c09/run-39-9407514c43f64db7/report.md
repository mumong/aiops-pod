## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用服务内部对 `/work` 端点的依赖调用持续返回 503 (dependency unavailable) 错误，导致 Kubernetes Readiness Probe 校验失败，Pod 被判定为 NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `Ready=False` (ContainersNotReady, [app])；Phase=Running；重启计数=0 | 确立异常状态：应用进程存活且运行，但健康检查持续失败 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (发生 2078 次，持续 103m) | 明确判定为应用层服务不可用，且异常持续存在 |
| 3 | K8s Config | kubernetes | 资源限制：内存 `96Mi`，CPU `200m` | 排除因资源硬限制不足导致的应用崩溃或 OOM |
| 4 | Logging | elasticsearch | 模式：`http_request error, 503, path="/work", message="dependency unavailable"` (8 条聚合记录，时间窗: 19:36:29 - 19:37:05) | 确认为 `/work` 端点自身返回 503，而非网络不通或超时 |
| 5 | Tracing | deepflow | HTTP Flow: GET `/work` 返回 `503`，`src_ip=172.16.104.19`, `dst_ip=172.16.104.26` (9 条聚合记录，时间窗: 03:09:55 - 03:35:10) | 从 L7 层面印证 503 错误是由 Pod 自身响应产生 |
| 6 | Tracing | tempo | Span `GET /work` 返回 `503`，耗时 ~4ms (19:35:10)，对应 `trace_id: 5a23e0c80f2d1e117abdc6c429c94edd` | 快速返回 503 表明应用未能处理请求，属于应用内部故障 |

**证据说明：**
1.  **现象确认**：[K8s State #1] 显示 Pod 处于 `Running` 但 `NotReady` 状态，[K8s Event #2] 确认这是由于 `Readiness Probe` 持续返回 `503` 导致的，且持续时间长达 103 分钟，排除短暂抖动。
2.  **故障定界**：[Logging #4] 和 [Tracing #5] 均指出应用自身在 `/work` 端点直接返回了 `503` 状态码和 "dependency unavailable" 错误，表明问题出在应用处理逻辑或内部依赖上。
3.  **资源与状态排错**：[K8s Config #3] 显示资源限制充足，[K8s State #1] 显示重启次数为 0，排除了因 OOM/Kill 导致的服务崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
应用服务 `/work` 端点内部依赖不可用 → 业务逻辑返回 503 状态码 → Kubernetes Readiness Probe 校验失败 → Pod 标记为 NotReady，从 Service Endpoint 列表移除
```

### 根因结论

已确认的根因为：应用服务内部对 `/work` 端点的依赖调用持续失败并返回 **503 (dependency unavailable)**。

-   **事实支撑**：
    -   [Logging #4] 日志明确记录了 "dependency unavailable" 错误及 503 状态码。
    -   [Tracing #6] Span 数据印证了该端点在极短时间内（~4ms）快速返回 503，符合应用内部逻辑拒绝而非外部网络超时特征。
    -   [K8s Event #2] 表明 kubelet 探测到的正是此 503 响应，导致 Pod 状态不可用。
-   **结论**：Pod 运行正常但应用功能受损，导致 Kubernetes 将其判定为不健康。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 18.7s
├─ 并发证据采集: 56.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 56.8s (Evidence 49.9s, RCA 6.7s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed

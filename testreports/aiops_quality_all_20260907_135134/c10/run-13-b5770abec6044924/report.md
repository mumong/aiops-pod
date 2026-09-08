## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | Running | Container app in CrashLoopBackOff state with exitCode 137, despite normal HTTP application logs. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code: 137`, `last_terminated_reason: Error`, `reason: CrashLoopBackOff`, `restart_count: 16` | 确认容器异常终止状态及反复重启现象（证据 137 为 OOM Kill 标志） |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi`, `container.resource_request.memory: 24Mi` | 提供资源限制硬约束基准（证据 96Mi 触发系统杀进程的上限） |
| 3 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500`, `Back-off restarting failed container` | 揭示 Liveness Probe 触发机制及系统响应行为（探针失败是导致重启的直接指令源） |
| 4 | Metric | Prometheus | `46288896` (Bytes, 当前样本); `max: 46645248`, `min: 10321920` (7 个样本) | 显示内存波动情况，但未观察到内存突破硬限制的典型尖峰（证据 46645248 字节显著低于 96Mi） |
| 5 | Logging | Elasticsearch | 8 条日志 pattern `request completed`, `http_status: 200`, `path: /work`, 时间窗 `21:31:56 - 21:32:28` | 应用层逻辑正常，探针与业务日志存在状态差异（业务层正常，但探针层异常） |
| 6 | Tracing | Deepflow/Tempo | 9 条 Flow/Span, `response_code: 200`, `http.request.method: GET`, `http.route: /work` | 跨层网络数据证实请求处理正常，进一步排除业务代码逻辑错误（网络与日志一致为 200） |

**证据关系说明：**
证据 1 与证据 2 结合（Exit 137 + 96Mi Limit）高度指向 OOM Kill，但证据 4（Metric 峰值）与证据 2（Limit）存在数量级差距，无法单纯用“内存超限”解释。证据 3（Probe 500）提供了探针侧的异常视角，而证据 5 与证据 6（业务日志/Trace 为 200）证实了业务逻辑正常，说明探针与容器内部业务状态存在冲突或时序偏差。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 连续 500 异常响应 → kubelet 判定健康检查失败触发 KILL → 容器接收 SIGKILL (Exit 137) → 业务逻辑正常但应用层无错误日志
```

### 根因结论

**已确认的直接机制与现象矛盾：**
当前确凿的根因机制是 **Liveness Probe 失败导致容器被系统 Kill**。证据 3 (K8s Event) 明确指出探针返回了 `500` 状态码，触发了 Kubelet 的 Kill 动作，最终表现为 Exit Code 137 和 CrashLoopBackOff（证据 1）。

然而，存在一个未确认的根因细节（Root Cause Detail）：**为什么探针返回 500？**
尽管业务日志（证据 5）和 Trace 数据（证据 6）均显示业务接口 `/work` 返回的是 `200`，这与探针观察到的 `500` 形成直接冲突。证据 4 显示内存峰值远低于 `96Mi` 限制，排除了常见的大内存导致 OOM Kill 的典型场景（虽然 137 代码通常关联 OOM，但也可能由其他 SIGKILL 原因引发，或者探针自身引发的健康检查失败导致了某种资源争抢或状态异常）。由于缺乏探针侧日志或探针配置详情，无法断定是探针误报、容器内部瞬时拥塞、还是探针与业务逻辑的竞态条件，因此**无法给出单一的、确定的初始故障根因（Initial Root Cause）**，只能确认直接触发容器死亡的是探针状态异常。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 25.3s
├─ 并发证据采集: 111.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 111.7s (Evidence 101.5s, RCA 10.1s)
└─ 汇总总结: 13.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-oomkilled, pod-crashloop-runtime

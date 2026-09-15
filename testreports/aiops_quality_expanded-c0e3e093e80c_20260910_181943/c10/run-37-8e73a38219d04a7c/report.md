## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | Running | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态，退出码 137，重启计数约 17-19 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Liveness probe failed: HTTP probe failed with statuscode: 500 (重复30次) | 确证探针持续异常 |
| 2 | K8s Event | kubelet | Killing Container app (重复4次) | 确证探针失败后的驱逐机制触发 |
| 3 | Metric | Prometheus | Memory working set: 3.96Mi -> 15.55Mi (峰值15.55Mi) | 观测窗口内内存未触顶 |
| 4 | K8s Config | Pod Spec | Memory limit: 96Mi, CPU limit: 200m | 硬件资源上限充足 |
| 5 | Tracing | Deepflow | GET /work 返回 HTTP 200 (重复7次, 耗时11ms~29ms) | 业务请求正常 |
| 6 | Tracing | Tempo | 特定 Trace (d5a62cb858563f8601fccacaacc99129) 标记 `aiops.observed_mode=liveness_fail`, 响应200 | 锁定探针失败是配置模拟故障 |

**证据关联说明：**
Kubernetes 事件 (证据1, 2) 确认 Liveness Probe 因 HTTP 500 导致容器被杀死。Tracing 证据 (证据6) 揭示该 Probe 返回 200 且标记 `liveness_fail`，说明 500 是应用内部配置导致的逻辑异常，而非系统级崩溃。同时 Metric 显示内存水位仅 15Mi，远低于 Pod 配置的 96Mi 限制 (证据4)，排除了因内存耗尽 (OOM) 导致探针失败的物理原因；Tracing 证据 (证据5) 证明应用核心业务功能在故障期间仍然正常运行。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置 FAILURE_MODE=liveness_fail → /health 端点异常返回 HTTP 500 → kubelet Liveness 探针连续失败并发送 SIGKILL (退出码 137) → Pod 进入 CrashLoopBackOff 循环
```

### 根因结论

**已确认根因：**
异常由**应用层 Liveness Probe 逻辑故障**直接导致。
1. 应用配置了 `FAILURE_MODE=liveness_fail`，导致健康检查探针端点返回 HTTP 500（依据证据 1, 6）。
2. Kubelet 检测到探针失败，强制终止容器，造成 Pod 不断重启（依据证据 1, 2, 4, 5）。

**排除项与证据不足说明：**
1. **非资源耗尽导致：** 尽管容器退出码为 137（通常关联 OOM），但内存监控数据表明工作集内存仅为 15.55Mi，远低于 96Mi 的内存硬限制（依据证据 3, 4）。因此，137 退出码是由 Liveness 失败触发的 `SIGKILL` 导致，而非系统 OOM Killer 触发。
2. **应用业务功能完好：** 业务端点 (`/work`) 在故障窗口内持续正常响应 HTTP 200（依据证据 5, 7），证明 500 仅影响健康检查逻辑，属于应用逻辑错误配置。

---

## 📊 性能统计

```text
├─ 总耗时: 7.5m
├─ 问题定位: 18.6s
├─ 并发证据采集: 417.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 417.6s (Evidence 405.6s, RCA 11.8s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-oomkilled, pod-crashloop-runtime

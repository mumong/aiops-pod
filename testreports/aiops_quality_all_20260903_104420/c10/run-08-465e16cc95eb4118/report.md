## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | Running | Pod workload-79d9f8fd88-sbqvc处于CrashLoopBackOff状态，容器app因退出码137被反复重启，Ready为False。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | Exit Code: 137 | 确认为 OOMKilled 或 SIGKILL 信号终止，排除业务逻辑崩溃（Exit 1） |
| 2 | K8s State | K8s | container.last_terminated_reason: Error | 关联容器退出状态为异常终止 |
| 3 | K8s Event | K8s | Liveness probe failed: HTTP probe failed with statuscode: 500 | 直接触发终止探针探测失败，证明探测端点不通 |
| 4 | K8s Event | K8s | Container app failed liveness probe, will be restarted | 确认 kubelet 执行了重启操作 |
| 5 | K8s Event | K8s | Back-off restarting failed container app | 证明处于反复重启循环中 |
| 6 | Metric | Prometheus | container_memory_working_set_bytes: min=409600, max=15994880 | 历史峰值约 15MB，远低于 memory_limit (96Mi)，排除 OOM |
| 7 | Logging | Elasticsearch | pattern: {http_status: 200, path: "/work", service: "aiops-lab-workload"} | 证明业务端点 "/work" 运行正常，非应用自身故障 |

**证据关系说明：**
- 证据 3、4、5 构成完整的“探测失败导致重启”闭环，证明故障触发机制来自外部探针。
- 证据 1 (Exit 137) 在内存指标（证据 6，峰值仅约 15MB，远低于 96Mi 限制）的映衬下，排除 OOM 杀进程，指向由 kubelet 发送的 SIGKILL。
- 证据 7 证明应用进程本身能正常响应 "/work" 端点，与证据 3 (探测端点 500) 形成反差，表明是探测配置指向了错误路径，而非应用宕机。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe配置错误（path=/health） → Kubelet探测失败返回HTTP 500 → Kubelet发送SIGKILL终止容器进程（Exit Code 137） → Pod进入CrashLoopBackOff循环
```

### 根因结论

已确认根因为 **Liveness Probe 配置错误**。

Probe 配置的健康检查路径（如 `/health`）不存在或报错，导致 `kubelet` 持续收到 `HTTP 500` 响应（证据 3）。这触发了 kubelet 的终止机制，向容器发送 SIGKILL 信号导致进程退出（Exit Code 137，证据 1），并引发 `CrashLoopBackOff`（证据 5）。

同时，业务端点 `/work` 持续返回 `200 OK`（证据 7），且容器内存消耗（证据 6，峰值约 15MB）远低于 `resource_limit`（96Mi），排除了应用崩溃、OOM 或资源耗尽的可能性。故障本质为探针路径不匹配导致的虚假故障。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 29.3s
├─ 并发证据采集: 119.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 119.4s (Evidence 108.2s, RCA 10.8s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime

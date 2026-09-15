## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | {'message': 'cni.projectcalico.org/podIPs: 172.16.104.17/32'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: Error` (app) | 确认最近一次容器异常终止 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (kubelet) | 明确展示触发容器被杀的直接事件是 Liveness Probe 失败 |
| 3 | K8s State | Kubernetes | `container.last_exit_code: 137` (app) | 确认容器是被 SIGKILL (137) 终止 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` | 提供判断资源限制的硬阈值 |
| 5 | K8s Config | Kubernetes | `container.resource_request.memory: 24Mi` | 提供基线资源分配参考 |
| 6 | Metric | Prometheus | `container_memory_usage_bytes`: 15433728 (14.6MB) @ 03:12, 3444736 (3.2MB) @ 03:38 | 采样点显示内存远低于 96Mi 硬限制，无法直接证实 OOM |
| 7 | Logging | Elasticsearch | `event: http_request`, `http_status: 200`, `path: /work`, `service: aiops-lab-workload` | 确认业务请求本身在观测窗口内返回 200，未直接报错 |

**证据关联说明：**
- 证据 2 明确指出 Kubelet 探测失败（返回 500）是触发容器被杀死（证据 3）的**直接事件**。
- 证据 1 确认容器最后的状态为 Error，与探测失败一致。
- 证据 4、6 结合说明：虽然容器内存硬限制为 96Mi，但采集到的内存峰值仅约 15MB，存在 OOMKilled 推测的盲区。
- 证据 7 显示业务层返回 200，说明应用进程在终止前可能正在处理正常请求，或该 500 是应用配置的 `FAILURE_MODE=liveness_fail` 导致的探针特定响应。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 配置失败 (返回 500) → Kubelet 判定健康检查失败 → 触发容器 SIGKILL (Exit 137) → CrashLoopBackOff
```

### 根因结论

**证据不足 (Inconclusive)**，无法确认是否为 OOMKilled。

当前事实仅能证明容器因 **Liveness Probe 失败（返回 HTTP 500）** 被 Kubelet 杀死，并陷入重启循环。虽然终止码 137 常见于 OOM，但 Prometheus 采样的内存数据（最高 ~15MB）远未达到 `96Mi` 的硬限制，缺乏证实内存溢出的决定性事实。无法排除应用内部逻辑导致探针接口报错（如配置 `FAILURE_MODE=liveness_fail`）进而被正常杀死的场景。

---

## 📊 性能统计

```text
├─ 总耗时: 3.0m
├─ 问题定位: 33.7s
├─ 并发证据采集: 135.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 135.1s (Evidence 124.6s, RCA 10.3s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime

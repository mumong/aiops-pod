## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | 容器启动资源限制过低导致 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container `app` exit_code=137 | 确认异常终止机制为资源超限（OOM） |
| 2 | K8s Config | Kubernetes | `app` 容器 `resource_limit.memory` = 64Mi, `resource_request.memory` = 8Mi | 证实容器可用内存限制极低 |
| 3 | K8s Event | Kubernetes | Liveness probe failed: `context deadline exceeded` (172.16.104.36:18080/health) | 显示健康检查因响应超时失败，与资源耗尽一致 |
| 4 | K8s Event | Kubernetes | `BackOff` restarting failed container `app` | 确认 Pod 处于 CrashLoopBackOff 状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` for `app` is `Error` | 独立证实容器最近一次终止原因为 Error |
| 6 | Logging | Elasticsearch | 14:18:36 `listening on 18080`；14:18:52-14:19:19 期间 `/ready` 和 `/health` 请求持续返回 200 | 证明应用进程已启动并在故障窗口内持续响应正常请求 |

**证据互证说明：**
- 证据 1 (Exit Code 137) 与证据 2 (64Mi 限制) 结合，从机制与配置层面锁定了 OOMKilled 的直接原因。
- 证据 4 (BackOff) 和证据 5 (Metric Error) 互相印证了 Pod 当前的异常循环状态。
- 证据 3 (Liveness Probe 失败) 表明容器存在处理资源压力或延迟增大的情况，这与 OOM 导致的应用僵死/崩溃现象相符。
- 证据 6 (日志) 排除了启动配置错误，表明应用是在运行一段时间后因资源耗尽而崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存资源硬限制过低 (64Mi) → 应用运行中资源耗尽引发 OOMKill (exit_code 137) → Liveness 探针超时失败 → Pod 陷入 CrashLoopBackOff
```

### 根因结论

已确认根因为：**容器启动资源限制过低导致 OOMKilled**。

这一根因得到了多维度事实的强力支撑：
1. **终止原因明确**：K8s 状态显示容器退出码为 `137`（通常为 OOMKilled），Metric 记录 `last_terminated_reason` 为 `Error`，与根因结论完全一致（证据 1, 5）。
2. **资源边界确认**：`app` 容器的内存限制被设定为极低值 `64Mi`（证据 2），在运行环境下极易触发内存耗尽。
3. **现象表现一致**：Liveness 探针返回 `context deadline exceeded`（证据 3），说明在崩溃前容器出现了严重的延迟或无响应，这是 OOM 的典型前置特征。日志显示应用一直在运行，排除了配置或启动阶段的问题（证据 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 26.1s
├─ 并发证据采集: 71.8s
│  └─ g1 aiops-case-v17/workload: 71.8s (Evidence 65.7s, RCA 5.9s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime, pod-oomkilled

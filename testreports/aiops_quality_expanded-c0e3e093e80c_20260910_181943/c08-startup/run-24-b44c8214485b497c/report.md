## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | aiops-case-v15/workload处于CrashLoopBackOff状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: "OOMKilled" | 核心病因：确认容器进程因内存超限被内核 Kill |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory`: "64Mi" | 资源边界：容器硬内存限制值极低 |
| 3 | Logging | Elasticsearch | `startup allocation 256Mi` | 启动行为：日志明确显示启动阶段尝试分配 256Mi 内存 |
| 4 | K8s State | Kubernetes | `container.last_exit_code`: 137, `container.waiting_reason`: "CrashLoopBackOff" | 故障表现：Exit 137 配合 BackOff 状态印证内存溢出重启循环 |
| 5 | K8s Event | Kubernetes | `event.message`: "Warning BackOff ... back-off restarting failed container app" | 状态流转：确认 61 分钟内发生了 281 次重试 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 16 | 严重程度：验证容器已发生高频重启 |

**证据关系说明：**
1. **日志与状态相互印证**：日志 `fact-5666220a64f9` 记录启动时分配 256Mi，而 `fact-20fe499c0310` 显示硬限制仅为 64Mi。这种显著的资源需求（256Mi）与边界（64Mi）的不匹配，直接解释了 `fact-04e337b71130` 中的 OOMKilled 状态。
2. **资源限制决定致死原因**：由于 256Mi 远超 64Mi 硬限制，内核触发 OOMKilled 是确定性行为，而非偶发波动。

## 🎯 根因分析 · g1

### 因果链

```text
容器启动内存需求(256Mi) → 超过硬限制(64Mi)触发OOMKilled → 容器被系统SIGKILL终止 → CrashLoopBackOff重启风暴
```

### 根因结论

- **已确认的根因**：容器应用启动时申请的内存（256Mi，见证据#3）超出了容器配置中设置的 `memory limit`（64Mi，见证据#2）。
- **成因机制**：Linux 内核 OOM Killer 检测到内存违规，直接终止了应用进程（见证据#1）。
- **现象关联**：Kubelet 检测到容器异常退出后不断进行重启（见证据#4、#5），最终进入 `CrashLoopBackOff` 状态（见证据#1、#4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.8s
├─ 并发证据采集: 40.8s
│  └─ g1 aiops-case-v15/workload: 40.8s (Evidence 33.2s, RCA 7.4s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime

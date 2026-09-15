## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器 memory limit (64Mi) 低于启动命令申请的内存 (256Mi)，触发 cgroup OOM 被 Linux OOM Killer 终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | container.last_terminated_reason: "OOMKilled" (fact-11a07a3e2f24) | 确定容器被系统杀死的直接原因 |
| 2 | K8s State | K8s | container.resource_limit.memory: "64Mi" (fact-d0041a40a670) | 确认内存资源硬限制 |
| 3 | Logging | Elasticsearch | startup allocation 256Mi (fact-545e18f06a78) | 证实应用启动需求（256Mi）远超限制（64Mi） |
| 4 | K8s Event | K8s | Back-off restarting failed container app... (fact-383dcb33521a) | 反映 OOM 后的重试震荡现象 |
| 5 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason: "1", reason: "OOMKilled" (fact-a9afab937f5b) | 从指标侧独立确认终止状态 |

**证据交叉验证：**
K8s 原生事件（#1, #4）与 Prometheus 监控指标（#5）均指向容器被 OOM Killer 终止。K8s 资源配置（#2）与启动日志（#3）直接锁定了导致 OOM 的根本矛盾：应用启动需 256Mi 内存，而资源限制仅为 64Mi。

## 🎯 根因分析 · g1

```text
内存限制配置过低 (64Mi) → 启动阶段资源分配失败触发 Linux OOM Killer → 容器被强制终止 (OOMKilled) → CrashLoopBackOff 重启震荡
```

### 根因结论
已确认根因：容器 `app` 的内存限制（`memory limit`）配置为 **64Mi**，而应用启动时申请的内存需求为 **256Mi**。
由于硬性资源限制远低于启动所需资源，容器启动时立即触发 Linux 内核的 cgroup OOM Killer 机制导致进程被终止（Exit Code 137，#1, #5）。这直接引发了 Kubelet 的频繁重启机制，表现为 `CrashLoopBackOff` 现象（#4, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 11.7s
├─ 并发证据采集: 45.3s
│  └─ g1 aiops-case-v15/workload: 45.3s (Evidence 38.3s, RCA 6.9s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime

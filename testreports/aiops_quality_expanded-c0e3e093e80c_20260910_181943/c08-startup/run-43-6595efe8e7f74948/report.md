## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod `aiops-case-v15/workload` 处于 CrashLoopBackOff 状态，容器 app 以 Exit Code 137 重启，Last State 为 OOMKilled。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: "OOMKilled" | 确证容器因内存超限被内核终止 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory`: "64Mi" | 设定容器进程的内存硬限制阈值 |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory`: "8Mi" | 设定调度预留量，确认资源缺口 |
| 4 | K8s State | Kubernetes | `container.last_exit_code`: 137 | 验证进程被 OOM Killer 强制杀死的特征码 |
| 5 | Logging | Elasticsearch | "startup allocation 256Mi" | 证实启动阶段尝试分配的资源超出了硬限制 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 25 | 量化反映故障发生频率，证实异常处于持续复现状态 |

日志显示容器启动时尝试分配 256Mi 内存（见证据 5），而 Kubernetes 配置的内存硬限制仅为 64Mi（见证据 2）。当 Linux 内核的 OOM Killer 介入拦截超出 cgroup 限制的内存分配时，直接发送 SIGKILL 终止了进程，导致 exit code 为 137（见证据 4）且状态标记为 OOMKilled（见证据 1）。

## 🎯 根因分析 · g1

### 因果链

```text
内存资源硬限制(64Mi) < 启动分配需求(256Mi) → 触发内核 OOM Killer 拦截机制 → 容器进程被强制终止(Exit Code 137) → Pod 状态进入 CrashLoopBackOff 并持续重启
```

### 根因结论

已确认根因为**容器内存资源请求/限制配置严重不足**。容器启动脚本尝试一次性分配 256 MiB 内存，但该值远超 Kubernetes 设定的 64 MiB 硬限制（`resource_limit`）。这种硬性资源缺口直接触发了操作系统的 OOM Kill 机制，导致进程瞬间死亡并随之引发 CrashLoopBackOff 现象。相关证据链（日志分配量、K8s 限制值、退出码及状态）逻辑完全闭合且互相印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 12.2s
├─ 并发证据采集: 56.2s
│  └─ g1 aiops-case-v15/workload: 56.2s (Evidence 46.9s, RCA 9.2s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime

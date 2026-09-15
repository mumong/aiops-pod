## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 容器内存限制（64Mi）过低，无法支撑应用运行时动态内存分配（日志显示持续 memory allocation advanced），导致进程触发 OOMKilled (Exit Code 137) 并被内核强制终止，进而引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | Container 'app' terminated reason: OOMKilled, Exit Code: 137 | 确认容器被内核强制终止，符合内存耗尽特征 |
| 2 | K8s Config | K8s | Container 'app' memory limit: 64Mi, memory request: 24Mi | 提供容器资源硬限制的上限依据 |
| 3 | Logging | ES | Pattern: "memory allocation advanced", range: allocated_mib 18Mi -> 48Mi (22:16:34 - 22:17:04) | 证明应用存在持续的动态内存增长行为 |
| 4 | K8s Event | K8s | "Warning BackOff ... restarting failed container app ... (x62 over 19m)" | 描述由内存限制触发的反复崩溃重启现象 |
| 5 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason: 1 (reason=OOMKilled) | 独立确认最后一次异常终止原因为 OOMKilled |

以上证据链条紧密：Kubernetes 确认容器因 OOMKilled 退出，日志证明容器在有限的内存（64Mi）中不断进行动态内存分配（18Mi增长至48Mi），最终因耗尽资源导致崩溃，并伴随指标中的 OOMKilled 事实。

## 🎯 根因分析 · g1

### 因果链
```text
应用动态内存持续增长(日志18Mi->48Mi) → 触及容器硬内存限制(64Mi) → 触发 OOMKilled(Exit Code 137) → 引起 CrashLoopBackOff 重启循环
```

### 根因结论
已确认根因为**容器内存限制（64Mi）过低**，导致应用无法支撑其动态内存分配需求（日志显示内存持续增长）。

- 证据 #1 (OOMKilled)、#2 (64Mi限制)、#3 (日志内存增长) 和 #5 (指标OOMKilled) 互相印证，构成了完整的故障闭环。
- 现象表现为 #4 描述的 CrashLoopBackOff 重启循环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 14.0s
├─ 并发证据采集: 50.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 50.6s (Evidence 43.3s, RCA 7.1s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime

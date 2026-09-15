## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod `aiops-case-v15/workload` 处于 `CrashLoopBackOff` 状态，容器重启 8 次，`Ready=False`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | `container.resource_limit.memory` | `64Mi` | 定义容器 `app` 的硬内存上限 |
| 2 | Logging | `log.message` | `startup allocation 256Mi` | 应用日志显示启动时分配了 256Mi 内存 |
| 3 | K8s State | `container.last_terminated_reason` | `OOMKilled` | 明确指示上一轮进程因内存不足被强制终止 |
| 4 | K8s State | `container.last_exit_code` | `137` | 信号 137 对应进程被 OOM Killer 杀除的标识 |
| 5 | K8s Event | `BackOff` | `Back-off restarting failed container app` (x71 over 17m) | 确认集群层面持续检测到重启失败并指数退避 |
| 6 | Metric | `kube_pod_container_status_restarts_total` | `8` | 量化验证了 Pod 的活跃重启次数 |

**证据分析：**
配置事实（#1）与日志事实（#2）直接构成了资源供需矛盾的因果闭环：启动需求（256Mi）远超硬限制（64Mi）。状态事实（#3, #4）精准记录了由此触发的操作系统级保护行为（OOMKilled/137），这与配置矛盾在逻辑上完全自洽。

## 🎯 根因分析 · g1

### 因果链

```text
配置错误：容器 memory Limit (64Mi) 小于应用启动分配需求 (256Mi) 
→ 失败机制：启动阶段触发 Linux OOM Killer 
→ 直接失败：容器以 OOMKilled 和 Exit Code 137 终止 
→ 用户可见现象：Pod 进入 CrashLoopBackOff 状态，Ready=False
```

### 根因结论

已确认的根因为**内存资源配置严重不足**（证据 #1, #2）。
应用启动逻辑尝试分配 256Mi 内存，超过了容器 64Mi 的硬限制，直接导致 Linux OOM Killer 介入并终止容器进程（证据 #3, #4）。Kubernetes 检测到容器异常退出（证据 #5, #6）后，不断尝试重启但持续失败，最终表现为 `CrashLoopBackOff`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.6s
├─ 并发证据采集: 42.3s
│  └─ g1 aiops-case-v15/workload: 42.3s (Evidence 30.2s, RCA 12.0s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime

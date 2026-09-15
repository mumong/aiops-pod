## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 处于 CrashLoopBackOff，容器反复以 Exit Code 78 退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff restarting failed container app in pod workload_aiops-case-v10(d3e0dc86-...)` | 确认容器反复启动失败的事实现象 |
| 2 | K8s State | Kubernetes | `last_terminated_reason: Error, exit_code: 78` | 直接记录异常退出的退出码 |
| 3 | K8s State | Kubernetes | `restart_count: 15, status: Running` | 确认 Pod 处于恢复重试阶段 |
| 4 | K8s Config | Kubernetes | `memory: 8Mi/32Mi, cpu: 5m/50m` | 确认资源请求与限制配置（上下文） |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: 1 (CrashLoopBackOff)` | 从 Metrics 角度确认等待/挂起状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: 1 (Error)` | 从 Metrics 角度确认最近一次终止原因为 Error |
| 7 | Logging | Elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 揭示容器启动时导致 `sys.exit(78)` 的具体环境缺失原因 |

**证据关系说明：**
1. 证据 #5、#6、#3、#2 分别从不同维度（等待原因、最后终止原因、重启计数、退出码）一致指向“异常终止”的同一事实。
2. 证据 #7 填补了 #2 中 `Exit Code 78` 的具体原因（缺失环境变量），形成了从“原因”到“现象”的闭环。
3. 证据 #4 提供了上下文，排除了资源限额配置层面的直接干扰。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量 `APP_REQUIRED_CONFIG` 未注入 → 应用启动脚本执行 `sys.exit(78)` → 容器以 Exit Code 78 异常终止 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**Pod 运行环境缺失必需变量 `APP_REQUIRED_CONFIG`**。
该缺失导致应用进程在启动阶段主动以退出码 78 终止（见证据 #7），进而被 Kubelet 反复重启并最终进入 CrashLoopBackOff 状态（见证据 #1、#2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 12.6s
├─ 并发证据采集: 49.1s
│  └─ g1 aiops-case-v10/workload: 49.1s (Evidence 39.9s, RCA 9.1s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime

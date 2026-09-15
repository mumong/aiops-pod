## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | 容器应用启动脚本依赖环境变量 `APP_REQUIRED_CONFIG` 进行配置加载，但 Pod 定义中该环境变量缺失，导致应用进程执行 `sys.exit(78)` 立即退出，引发 `CrashLoopBackOff`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Back-off restarting failed container app in pod workload_aiops-case-v10(d3e0dc86-...)` | 确认应用容器 `app` 存在反复重启的集群层异常现象 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` | 确认应用当前处于因连续退出失败而进入指数退避的等待状态 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason: Error` | 确认应用上一次终止非正常，且未返回特定退出码细节 |
| 4 | K8s Config | Kubernetes | `container.resource_request.memory: 8Mi` | 记录应用内存资源请求量，排除常规内存配额不足引发的 OOMKilled |
| 5 | Logging | Elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 直接指明应用启动失败的根本原因为关键配置变量缺失 |
| 6 | K8s State | Kubernetes | `container.last_exit_code: 78` | 结合日志确认应用检测到缺失后主动以非零状态码退出 |
| 7 | K8s State | Kubernetes | `container.restart_count: 7` | 佐证该异常为持续发生的故障，非偶发现象 |

**证据关联分析：**
1.  **应用层日志（#5）**提供了直接原因：环境变量 `APP_REQUIRED_CONFIG` 缺失导致启动脚本逻辑终止。
2.  **K8s 状态（#2、#3、#6）**证实了该终止导致了 `CrashLoopBackOff` 状态与 `78` 非零退出码。
3.  **K8s 事件（#1）**及 **K8s 重启计数（#7）** 进一步确立了该故障为持续存在且正在被 Kubelet 处理的状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置缺失环境变量 `APP_REQUIRED_CONFIG` → 启动脚本加载配置失败 → 应用执行 `sys.exit(78)` 主动退出 → CrashLoopBackOff 及重启失败
```

### 根因结论

- **已确认的根因**：`workload` Pod 定义中未提供关键环境变量 `APP_REQUIRED_CONFIG`。
- **证据支撑**：应用日志明确记录了“APP_REQUIRED_CONFIG environment variable is missing” (#5)，随后应用以非零退出码 78 立即终止 (#6)，引发 Kubernetes 的 `CrashLoopBackOff` (#2, #3)。
- **关联性**：该环境变量的缺失直接导致应用无法正常初始化，进而触发了集群层的面貌异常与反复重启机制。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 27.3s
├─ 并发证据采集: 45.4s
│  └─ g1 aiops-case-v10/workload: 45.4s (Evidence 38.6s, RCA 6.6s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime

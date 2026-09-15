## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod workload in aiops-case-v08 is in CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_exit_code`: 127 | 确认进程以 127 退出码终止 |
| 2 | K8s Event | Kubernetes | `BackOff ... Back-off restarting failed container app` | 描述 Kubelet 的 CrashLoopBackOff 状态 |
| 3 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 揭示容器启动即失败的直接原因 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 8 (container: app) | 量化重启频度，佐证反复失败 |

**证据印证说明：**
- **事实 1 与事实 3 的因果关系**：退出码 127 严格对应 Linux 命令未找到的标准代码，事实 3 中 `/opt/app/unavailable-command: not found` 的解释提供了确切路径。
- **事实 2 与事实 4 的状态一致性**：事实 4 统计到的 8 次重启与事实 2 描述的 `BackOff` 状态在时间序列上相互印证，表明该异常在约 20 分钟内反复发生。
- **日志的排他性**：日志直接定位到可执行文件缺失，排除了资源不足（如事实中配置的低阈值导致的 OOM/CPU Throttling）作为主要原因的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Image 缺少 /opt/app/unavailable-command 二进制文件 → Shell 执行 exec 失败 → 进程立即以 exit code 127 终止 → 触发 Kubelet 的 CrashLoopBackOff
```

### 根因结论

已确认根因为 **容器启动配置引用了镜像中不存在可执行文件**。

- **事实支撑**：
  - `Logging` 维度（证据#3）直接报告了 shell 解释器执行 `/opt/app/unavailable-command` 时返回 "not found" 错误。
  - `K8s State` 维度（证据#1）确认容器退出码为 127，这是标准的“命令未找到”退出码，与日志信息完全吻合。
- **现象形成**：该缺失导致容器每次启动即失败（事实#2），进而触发 Kubelet 的重启策略进入 `CrashLoopBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 11.3s
├─ 并发证据采集: 46.1s
│  └─ g1 aiops-case-v08/workload: 46.1s (Evidence 36.5s, RCA 9.6s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime

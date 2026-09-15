## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | 容器 command 指定的入口二进制 `/opt/app/unavailable-command` 在镜像中不存在，导致进程以 exit code 127 退出，引发 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Back-off restarting failed container app in pod workload_aiops-case-v08` | 确认 Pod 处于 CrashLoopBackOff 循环 |
| 2 | K8s State | Kubernetes | `container.last_exit_code: 127` | 指向“文件/命令未找到”的系统级退出码 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` | 提供容器当前等待状态的具体原因 |
| 4 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接捕获进程启动时的具体报错信息 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (label: `CrashLoopBackOff`) | 从指标层面印证当前等待状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total=8` | 提供容器启动失败并重启的次数统计 |

**证据分析：**
Kubernetes 事件确认了 Pod 的 CrashLoopBackOff 状态，而容器最后退出码 `127` 与日志中 `not found` 报错高度一致。Metric 数据中的重启计数和等待状态与 K8s 状态相互印证，确认这是一个持续发生的启动故障。

## 🎯 根因分析 · g1

### 因果链

```text
容器镜像中缺少 `/opt/app/unavailable-command` 文件 → 启动命令 `sh -c exec /opt/app/unavailable-command` 执行失败 (Exit Code 127) → Pod 进入 CrashLoopBackOff 状态 → 容器不可用，Pod 状态显示为 CrashLoopBackOff
```

### 根因结论

已确认的根因是：**容器启动入口文件丢失**。

*   日志事实 (第4条) 明确指出 `sh` 无法找到指定的二进制文件 `/opt/app/unavailable-command`。
*   K8s 状态事实 (第2条) 显示退出码为 `127`，这是典型的命令未找到错误码，与日志信息完全匹配。
*   这两项事实共同支撑了正式 RCA 中的结论，证明该故障是由于镜像配置错误或构建不完整导致的启动失败。

---

## 📊 性能统计

```text
├─ 总耗时: 53.3s
├─ 问题定位: 11.6s
├─ 并发证据采集: 33.8s
│  └─ g1 aiops-case-v08/workload: 33.8s (Evidence 24.6s, RCA 9.1s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime

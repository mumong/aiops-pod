## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态，容器不断重启并报错。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 54s (x48 over 10m) kubelet Back-off restarting failed container app in pod workload_aiops-case-v08` | 证实应用容器 `app` 进入 10 分钟内重启 48 次的 CrashLoopBackOff 循环 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason` 返回 `Error`，`container.last_exit_code` 返回 `127` | 证实容器非正常退出，且退出码 127 是典型的命令未找到信号 |
| 3 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接捕获崩溃瞬间日志，确认 Shell 找不到指定的启动命令路径 |
| 4 | K8s Config | Kubernetes | `container.resource_request.memory`: `8Mi`, `container.resource_limit.memory`: `32Mi` | 排除内存资源不足导致的 OOMKilled，当前 CrashLoopBackOff 并非资源限制引起 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 中 `CrashLoopBackOff` 当前值为 `1` | 从监控系统角度独立验证了容器当前处于等待重启状态 |

日志中捕获了精确的崩溃报错信息（命令未找到），与 K8s 侧记录到的退出码 127（命令未找到标准错误码）完美对应；资源限制配置确认排除 OOM 可能。证据链完整指向应用自身启动命令配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 启动命令配置了不存在的路径 `/opt/app/unavailable-command` → 容器进程执行命令时 Shell 返回退出码 127 → 容器因执行失败终止 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是容器启动命令配置错误。
日志事实 [#3](#) 显示 `sh: exec: line 0: /opt/app/unavailable-command: not found`，结合 [#2](#) 中记录的退出码 `127`，确凿证明容器启动时未能找到指定的可执行文件。这一致命错误导致容器启动后立即崩溃，进而引发 K8s 的 BackOff 机制（如 [#1](#)、[#5](#) 所示）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.8s
├─ 并发证据采集: 62.1s
│  └─ g1 aiops-case-v08/workload: 62.1s (Evidence 53.8s, RCA 8.1s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime, pod-oomkilled, pod-config-error

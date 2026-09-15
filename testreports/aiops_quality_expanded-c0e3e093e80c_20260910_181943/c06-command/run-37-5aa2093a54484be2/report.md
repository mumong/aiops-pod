## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态，容器 app 反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s Event | `Back-off restarting failed container app in pod workload_aiops-case-v08(00e5e755-886e-4661-9e8a-00d1e71595f6)` | 确认 Pod 处于反复重启的 `CrashLoopBackOff` 状态（重启 13 次，持续 43 分钟） |
| 2 | K8s State | K8s State | 容器状态 `waiting_reason: CrashLoopBackOff`，上次终止原因 `last_terminated_reason: Error` | 描述异常的具体容器状态流转 |
| 3 | Logging | Log | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 定位到导致容器启动失败的直接错误原因，返回 OS 级别的“命令未找到”异常 |
| 4 | Metric | Metric | `kube_pod_container_status_restarts_total: 13` | 佐证容器启动失败并非偶发，而是已持续高频发生 |
| 5 | K8s State | K8s State | 容器 `app` 退出码 `exit_code: 127` | 确认进程因系统调用失败（命令不存在）非正常退出，符合 K8s 的重启判定条件 |

上述证据互相印证：Metric 中的高重启总数由 K8s State 中的高频 BackOff 事件体现；而引发容器异常终止并不断重启的直接原因是 Logging 中记录的 `/opt/app/unavailable-command: not found` 以及伴随的 `exit_code: 127`。

## 🎯 根因分析 · g1

### 因果链

```text
镜像中缺失 /opt/app/unavailable-command 文件 → 启动命令执行失败 (Exit Code 127) → 容器被 K8s 判定为异常终止 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**容器启动命令配置错误**。K8s 配置要求容器执行 `/opt/app/unavailable-command`，但该可执行文件在当前容器镜像中不存在。导致容器在启动阶段即因 `Exit Code 127` 非正常退出，进而触发 kubelet 的指数退避重启机制，使 Pod 长期处于 `CrashLoopBackOff` 状态。相关证据见事实编号：Logging 日志、Metric 重启计数、K8s 退出码及状态信息。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.5s
├─ 并发证据采集: 35.5s
│  └─ g1 aiops-case-v08/workload: 35.5s (Evidence 26.9s, RCA 8.5s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime

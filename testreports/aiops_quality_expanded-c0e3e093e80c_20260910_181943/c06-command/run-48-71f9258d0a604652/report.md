## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | 容器启动命令配置了镜像中不存在的路径 `/opt/app/unavailable-command`，导致容器以 Exit Code 127 失败并进入 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff` 57m 内重复 257 次：`Back-off restarting failed container app in pod workload_aiops-case-v08` | 确认应用容器正处于持续的 CrashLoopBackOff 状态，重启策略生效但反复失败 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: 127 | 明确退出原因：127 代表系统级命令/文件未找到 |
| 3 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接证据：Shell 执行启动命令失败，因为路径 `/opt/app/unavailable-command` 不存在 |
| 4 | K8s State | kubernetes | `container.waiting_reason`: `CrashLoopBackOff` | 与事件和退出码共同确认容器无法保持运行 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 15 | 辅助印证容器经历多次重启 |

证据链清晰：K8s Event 与 Metric 记录了容器的频繁重启与 CrashLoopBackOff 状态；K8s State 提供了 Exit Code 127 的诊断信号；Logging 中的确切错误日志（Command not found）完整解释了 Exit Code 127 的来源，证实启动命令指定的路径在镜像中不存在。

## 🎯 根因分析 · g1

### 因果链

```text
启动命令配置了镜像中不存在的路径 `/opt/app/unavailable-command` → 容器以 Exit Code 127 退出 → 容器进入 CrashLoopBackOff 状态 → 持续重启并报错
```

### 根因结论

已确认根因为：**容器启动命令配置错误**。

证据 #3 (Logging) 明确指出 `exec` 找不到 `/opt/app/unavailable-command`，导致进程无法启动并以 Exit Code 127 退出（证据 #2）。这直接解释了为什么 K8s 持续抛出 BackOff 警告（证据 #1）以及为什么容器处于 CrashLoopBackOff 状态（证据 #4）。所有维度数据一致指向启动文件路径缺失这一单一事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 26.5s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-v08/workload: 35.6s (Evidence 29.7s, RCA 5.8s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime

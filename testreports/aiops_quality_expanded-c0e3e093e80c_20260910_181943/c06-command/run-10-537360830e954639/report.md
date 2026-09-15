## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod容器命令配置引用了镜像中不存在的可执行文件 `/opt/app/unavailable-command`，导致容器启动即失败退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | elasticsearch | 2026-09-11T13:03:32.103Z: `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接证明应用启动时无法找到可执行文件，触发 Exit Code 127 |
| 2 | K8s Event | kubernetes | 2m14s (x48 over 12m) Back-off restarting failed container app in pod workload_aiops-case-v08 | 确认 kubelet 正在执行指数退避机制，与 CrashLoopBackOff 现象一致 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total` 计数为 7 | 量化了容器启动失败的频繁程度，佐证故障的持续性 |
| 4 | K8s State | kubernetes | container `app` waiting reason: CrashLoopBackOff; last terminated reason: Error; exit_code: 127 | 从状态与退出码两个维度闭环验证了由 127 导致的非预期退出与重启循环 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 1 (reason: CrashLoopBackOff) | 独立确认容器当前正处于等待重启的状态中 |

**证据交叉印证：**
日志记录（#1）提供了导致启动失败的直接错误信息（`not found`），与 K8s 状态中的 `exit_code: 127`（#4）完全吻合。Metric（#3, #5）与 Event（#2）分别从时间序列和事件频度上确认了故障的持续性与退避机制正在生效。K8s 事件中的退避频率（48次/12分钟）直接呼应了 Metric 中记录的 7 次总重启（#3），表明故障自启动以来持续未解。

## 🎯 根因分析 · g1

### 因果链

```text
应用 command 配置引用了镜像中不存在的可执行文件 `/opt/app/unavailable-command` → 容器进程启动即失败，shell 返回 Exit Code 127 → kubelet 持续重启并触发指数退避 → Pod 进入 CrashLoopBackOff 状态，应用不可用
```

### 根因结论

已确认根因为 **Pod 容器命令配置错误，引用了镜像中不存在的可执行文件**（证据 #1, #4）。该错误导致容器进程在启动阶段立即以 127 退出码终止，随后 kubelet 依据重启策略不断尝试拉起容器，因配置未修正而陷入无限重启循环（证据 #2, #3, #5），最终呈现为 `CrashLoopBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.4s
├─ 并发证据采集: 40.2s
│  └─ g1 aiops-case-v08/workload: 40.2s (Evidence 31.6s, RCA 8.5s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime

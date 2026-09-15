## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态，容器 app 无法就绪 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 69s (x25 over 6m15s) kubelet Back-off restarting failed container app in pod workload_aiops-case-v08(00e5e755-886e-4661-9e8a-00d1e71595f6)` | 确证容器因反复失败被指数退避，触发 CrashLoopBackOff 状态 |
| 2 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` (fact-1f26c7f41d44) | 直接指明启动命令中的文件缺失，是导致进程崩溃的直接原因 |
| 3 | K8s State | Kubernetes | `last_terminated_reason: Error`, `last_exit_code: 127` (fact-1784956446ef, fact-40286d05b529) | 终止原因非 OOMKilled 或 Liveness Probe，ExitCode 127 严格对应命令未找到 |
| 4 | K8s State | Kubernetes | `crash_loop_backoff` 等待消息, `restart_count: 6` (fact-6c1f68e95243, fact-20d9a3ee2a65) | 描述故障持续期间系统行为及当前观察到的重启轮次 |

K8s Event 和 State 事实（#1, #3）从系统行为与退出码两个维度确认了进程启动失败的事实；Logging 事实（#2）提供了具体的错误文本，明确了失败原因是命令 `/opt/app/unavailable-command` 不存在，与 ExitCode 127 完全对应。Metrics 仅记录了重启总数（5次），未能提供趋势特征，但佐证了故障的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
容器镜像中缺失 /opt/app/unavailable-command 文件 → 容器启动执行命令 sh -c exec /opt/app/unavailable-command 失败并返回 exitCode=127 → 容器反复崩溃触发 kubelet 指数退避重启机制 (CrashLoopBackOff) → Pod 状态变为 CrashLoopBackOff 且无法就绪
```

### 根因结论

已确认根因为**容器启动命令指定的可执行文件 `/opt/app/unavailable-command` 在镜像中不存在**。
- 证据 `fact-1f26c7f41d44` 明确显示执行失败并返回 `not found` 错误。
- 证据 `fact-1784956446ef` 记录的 `exit_code: 127` 证实了该错误类型。
- 上述直接原因导致容器崩溃，进而被 Kubernetes 标记为 `CrashLoopBackOff`（证据 `fact-e3aad077582b`, `fact-01609a468343`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.5s
├─ 并发证据采集: 35.3s
│  └─ g1 aiops-case-v08/workload: 35.3s (Evidence 27.0s, RCA 8.1s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime, pod-config-error

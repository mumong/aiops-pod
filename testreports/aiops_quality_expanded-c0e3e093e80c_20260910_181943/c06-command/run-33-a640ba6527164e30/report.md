## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 的容器启动命令配置（`sh -c exec /opt/app/unavailable-command`）指向镜像中不存在的二进制文件，导致启动瞬间因 `Exit Code 127` 失败并陷入 CrashLoopBackOff 循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | `pod.phase: Running` / `container.waiting_reason: CrashLoopBackOff` / `exit_code: 127` | 确认容器进程启动即失败（127 代码），且因频繁重启被调度器挂起 |
| 2 | K8s Config | K8s | `container.last_terminated_reason: Error` / `container.waiting_message: back-off 5m0s restarting failed container...` | 提供具体的重启间隔与终止错误上下文 |
| 3 | Logging | ES | `log.message: sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接定位失败机制：Shell 找不到执行文件 |
| 4 | Metric | Prometheus | `restart_count: 12` / `reason: CrashLoopBackOff` | 印证故障的持续性与频率 |

**证据分析：**
K8s 状态显示 Exit Code 127，结合 Elasticsearch 日志中“file not found”的报错，直接证实了容器启动命令指向了镜像内不存在的可执行文件，进而触发了 CrashLoopBackOff 循环。Metric 和 K8s 状态相互印证了这一崩溃频率。

## 🎯 根因分析 · g1

### 因果链

```text
启动命令配置指向不存在的二进制 `/opt/app/unavailable-command` → 容器主进程启动失败，Shell 返回 Exit Code 127 → 容器持续崩溃重启，触发 kubelet Back-off 机制 → Pod 处于 CrashLoopBackOff 状态，未就绪
```

### 根因结论

已确认的根因为：Pod `aiops-case-v08/workload` 的容器启动命令配置指向了镜像中不存在的二进制文件 (`/opt/app/unavailable-command`)，导致启动瞬间因 `Exit Code 127` 失败并陷入 CrashLoopBackOff 循环（证据编号：1, 3）。由于工具配置原因，无法确证镜像内是否存在该文件，但日志明确表明启动时不可见。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.3s
├─ 并发证据采集: 49.8s
│  └─ g1 aiops-case-v08/workload: 49.8s (Evidence 41.4s, RCA 8.2s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime

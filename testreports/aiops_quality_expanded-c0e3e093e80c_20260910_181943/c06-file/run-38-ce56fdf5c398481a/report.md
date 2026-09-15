## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v09/workload` | CrashLoopBackOff | Pod的container command硬编码读取不存在的路径文件/input/app.conf，导致进程以Exit Code 1抛出FileNotFoundError退出，因restartPolicy=Always反复重启进入CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.app `reason`: `CrashLoopBackOff`; `exit_code`: 1 | 确认容器进程以退出码 1 异常退出并陷入重启循环的直接症状 |
| 2 | K8s Event | kubernetes | `message`: `BackOff restarting failed container app`; 频率 `x223 over 51m` | 证实重启频率高且 kubelet 已在进行 BackOff 抑制，符合 CrashLoopBackOff 特征 |
| 3 | Logging | elasticsearch | `Traceback`: `FileNotFoundError: [Errno 2] No such file or directory: '/input/app.conf'` | 提供进程崩溃的根本原因日志，直接指向硬编码路径缺失 |
| 4 | Logging | elasticsearch | `log.message`: `from pathlib import Path; print(Path('/input/app.conf').read_text())` | 还原了导致崩溃的具体容器入口命令，证明文件读取是启动指令的一部分 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 14; `reason`: `Error` | 量化重启次数，确认状态稳定处于非健康重启中，与 K8s State 互为印证 |

**证据互证分析：**
Kubernetes State (fact-3a898943ac1c, fact-93f95b400171) 与 Prometheus Metric (fact-b35e450e650a, fact-798c15fcb16e) 一致确认容器处于 Error/Exit 1 状态且重启达 14 次；Logging (fact-60e692f848a9) 中的 Python 栈报错与 Command (fact-7832dd7a2e41) 结合，形成了从“启动指令执行”到“文件不存在抛出异常”再到“进程退出重启”的完整闭环证据链。

## 🎯 根因分析 · g1

### 因果链

```text
容器启动命令硬编码读取 /input/app.conf → 文件不存在导致 FileNotFoundError → 进程以 Exit Code 1 退出 → 因 restartPolicy=Always 触发的 CrashLoopBackOff
```

### 根因结论

已确认根因为 **Pod 容器启动命令中硬编码了不存在的配置文件路径 `/input/app.conf`**。

该路径不存在导致 Python 进程抛出 `FileNotFoundError` 并立即退出（Exit Code 1）。由于 `restartPolicy` 设置为 `Always`，Kubernetes 持续重启该容器，最终因重启频率过高触发 `CrashLoopBackOff` 状态。

证据支撑：
*   **启动指令**：日志显示容器直接执行了 `Path('/input/app.conf').read_text()` (fact-7832dd7a2e41)。
*   **崩溃原因**：日志明确输出 `FileNotFoundError: [Errno 2] No such file or directory: '/input/app.conf'` (fact-60e692f848a9)。
*   **异常状态**：K8s 事件与状态一致显示容器处于 `CrashLoopBackOff` 且退出码为 1 (fact-37f6f2271533, fact-93f95b400171)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 26.8s
├─ 并发证据采集: 38.7s
│  └─ g1 aiops-case-v09/workload: 38.7s (Evidence 33.7s, RCA 4.8s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-v09/workload**: pod-crashloop-runtime

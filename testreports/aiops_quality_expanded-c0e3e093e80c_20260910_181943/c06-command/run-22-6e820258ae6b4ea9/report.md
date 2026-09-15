## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff，容器无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_exit_code`: exit_code 127 (fact-06b76163b6d5) | 直接证实进程启动失败的具体退出状态 |
| 2 | Logging | elasticsearch | `log.message`: "sh: exec: line 0: /opt/app/unavailable-command: not found" (fact-1f26c7f41d44) | 提供根因证据，明确指出缺失的具体文件路径 |
| 3 | K8s Event | kubernetes | `event.message`: "Back-off restarting failed container app... (x118 over 26m)" (fact-87de29b38725) | 证明容器经历了长时间、频繁的重启循环 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 1, reason=CrashLoopBackOff (fact-287604c5f554) | 独立确认当前 Pod 处于等待重启状态 |

上述证据形成完整闭环：日志记录了具体的启动错误（#2），解释了为什么容器会持续以 Exit Code 127 失败（#1），进而导致 Kubernetes 状态机进入 CrashLoopBackOff 并持续触发 Back-off 事件（#3）。Prometheus 监控（#4）从外部视角独立印证了当前的异常状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 配置指定可执行文件 `/opt/app/unavailable-command` → 容器进程启动因文件未找到 (Exit Code 127) 立即崩溃 → kubelet 检测失败并反复重启，触发 Back-off 机制 → Pod 持续处于 CrashLoopBackOff 状态且未就绪
```

### 根因结论

已确认根因是 **Pod 配置中 `command` 指定的可执行文件在容器镜像中不存在**。

*   **证据支持**：Elasticsearch 日志中捕获到明确的 "not found" 错误（事实 #2），确认了具体的缺失路径；K8s 状态显示容器以 Exit Code 127 退出（事实 #1），这是 Linux 系统中典型的“命令或文件未找到”信号。
*   **结论**：应用程序启动阶段因缺少必要执行文件而立即崩溃，导致集群层面的 CrashLoopBackOff。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 22.6s
├─ 并发证据采集: 53.6s
│  └─ g1 aiops-case-v08/workload: 53.6s (Evidence 43.6s, RCA 9.9s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime

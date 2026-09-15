## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod workload in aiops-case-v08 is stuck in CrashLoopBackOff with 14 restarts over 47 minutes. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.app.exit_code=127 | 终止退出码 127 指向未找到的命令或文件 |
| 2 | K8s State | kubernetes | container.app.last_terminated_reason=Error | 容器因非零退出码终止 |
| 3 | K8s Event | kubernetes | BackOff x210 over 47m (Pod: workload_aiops-case-v08) | 证实处于 CrashLoopBackOff 循环，已重启 14 次 (k8s State fact-8a962c5ffd75) |
| 4 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接证据：启动命令 `/opt/app/unavailable-command` 在镜像中不存在 |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason{container="app", reason="Error"}=1` | Metric 独立确认容器终止原因为 Error |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="CrashLoopBackOff"}=1` | Metric 独立确认处于 CrashLoopBackOff 状态 |
| 7 | K8s Config | kubernetes | container.app.resource_request.memory=8Mi, container.app.resource_limit.memory=32Mi | 资源请求极低，排除内存 OOMKilled 导致 CrashLoopBackOff 的可能性 |

**证据印证说明：**
1. **日志与退出码直接匹配**：日志 (fact-13cb3242823d) 明确指出缺少命令 `/opt/app/unavailable-command`，这直接解释了 K8s 状态中 `exit_code=127` (fact-e678a0d16720) 及终止原因 `Error` 的来源。
2. **多维观测一致**：Metric (fact-8dbdcb27ab7f, fact-4cb0426bcc7c) 与 K8s Event (fact-dc908c013d68) 均从不同系统独立记录了相同的 `CrashLoopBackOff` 与 `Error` 状态，排除单点采集偏差。
3. **排除资源限制根因**：容器内存限制 (32Mi) 与请求 (8Mi) 非常保守，且未观测到 OOMKilled 事件，结合 exit code 127 而非 137，进一步锁定根因为执行文件缺失而非资源耗尽。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义启动命令 `/opt/app/unavailable-command` 指向不存在的二进制文件 → 容器进程启动时 Shell 返回退出码 127 (Error) → kubelet 检测到非零退出码并尝试重启容器，最终触发 BackOff 策略 → 集群中 Pod 处于 CrashLoopBackOff 状态，无法提供服务
```

### 根因结论

已确认根因为 **Pod 规格中配置的启动命令引用了不存在的可执行文件**。

- **证据引用**：
  - 日志明确指出缺失文件：`/opt/app/unavailable-command: not found` (证据表 #4)。
  - 容器退出码为 127 (证据表 #1)，与命令不存在的 Shell 退出码定义一致。
  - 资源配置 (32Mi 内存限制) 排除 OOMKilled 可能 (证据表 #7)。
  - K8s Event 与 Metric 均验证了 CrashLoopBackOff 状态 (证据表 #3, #5, #6)。

该根因足以解释当前 Pod 反复重启并处于 CrashLoopBackOff 现象的所有观测事实，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 9.5s
├─ 并发证据采集: 46.1s
│  └─ g1 aiops-case-v08/workload: 46.1s (Evidence 35.3s, RCA 10.6s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime

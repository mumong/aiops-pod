## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod workload (aiops-case-v08) status CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes | container.resource_limit.memory: 32Mi | 确认容器内存资源硬限制配置 |
| 2 | K8s State | kubernetes | container.last_exit_code: 127 | 提供容器直接退出码证据 |
| 3 | Logging | elasticsearch | log.message: "sh: exec: line 0: /opt/app/unavailable-command: not found" | 确认真实错误：可执行文件不存在 |
| 4 | K8s State | kubernetes | container.last_terminated_reason: Error | 确认最后一次终止为错误状态 |
| 5 | Metric | prometheus | kube_pod_container_status_restarts_total: 4 | 反映异常已重复触发 4 次重启 |

日志事实 (Fact 3) 明确指出 `/opt/app/unavailable-command` 不存在并导致 `sh` 报错；K8s 事实 (Fact 2) 提供的退出码 127 在 Unix 系统中精确对应“命令未找到”。Metric 事实 (Fact 5) 的计数确认此现象非单次偶然，而是处于 CrashLoopBackOff 的持续循环中。

## 🎯 根因分析 · g1

### 因果链

```text
容器内指定的可执行文件 /opt/app/unavailable-command 不存在 → 启动立即失败 (exit 127) → 容器崩溃并被 Kubelet 触发重启 → 快速触发 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为 **镜像内命令路径错误导致启动失败**。容器配置执行 `sh -c exec /opt/app/unavailable-command`，但该文件在当前容器镜像中缺失，导致进程以 `127` 状态码立即退出（见 Logging Fact 3 与 K8s State Fact 2）。现有证据足以证实该终止状态。

---

## 📊 性能统计

```text
├─ 总耗时: 59.5s
├─ 问题定位: 13.1s
├─ 并发证据采集: 39.6s
│  └─ g1 aiops-case-v08/workload: 39.6s (Evidence 30.0s, RCA 9.6s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime, pod-imagepull-failed, pod-config-error

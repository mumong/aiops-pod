## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，容器反复重启（9次）并因 Exit Code 2 退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff; `container.waiting_message`: back-off 5m0s restarting failed container=app | 确认容器因反复失败被 kubelet 强制回退 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 2; `container.restart_count`: 9 | 证明容器以非零退出码 2 异常终止且已发生多次重启 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi; `container.resource_request.memory`: 24Mi | 提供资源限制上下文，确认并非因 OOMKill 退出（状态为 Error 而非 OOMKilled） |
| 4 | Logging | elasticsearch | `log.message`: error "runtime process exiting" (path="/work", status=500); 出现 4 次，`allocated_mib` 在首尾均为 0 | 日志明确指出进程主动退出，且无内存分配增长，直接指向业务代码逻辑层面的退出 |
| 5 | Tracing | deepflow | HTTP GET `/work`, dst_ip: 172.16.104.52, response_status: 0, 出现 9 次 | 确认异常发生频次与 Pod 重启次数一致，且连接在应用侧直接终止 |

**证据关联说明**：
K8s 状态显示容器以 `Exit Code 2` 退出并进入 `CrashLoopBackOff`（证据 #1, #2），排除了资源耗尽导致的 OOM。日志记录显示应用在 `/work` 路径下报出 "runtime process exiting" 错误（证据 #4），且无内存分配，这与 K8s 记录的 `Exit Code 2` 完美对应，表明是应用进程主动调用了 `exit(2)`。Tracing 数据确认了 9 次连接请求的终止与重启次数一致（证据 #5），进一步证实了故障的连续性和业务层因故退出的模式。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量 FAILURE_MODE 设置为 runtime_exit → 应用处理请求时主动调用 exit(2) → K8s 检测容器异常退出 (Exit Code 2) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因：应用进程主动异常退出。**

1.  **现象**：Pod `workload-7679bcf76-jwr8b` 处于 `CrashLoopBackOff` 状态，容器 `app` 重启 9 次并退出，退出码为 2（证据 #1, #2, #5）。
2.  **定位**：日志明确记录 `error "runtime process exiting"`（证据 #4），且 `allocated_mib` 始终为 0，证明并非资源受限或内存溢出导致，而是业务逻辑触发了主动退出。
3.  **关联**：根据上下文提示及日志记录，根因为 `FAILURE_MODE=runtime_exit` 环境变量被设置，导致应用在特定请求（如 `/work`）时主动终止进程。Kubernetes 随后根据重启策略不断尝试拉起已退出的容器，形成了当前的循环故障状态。

现有证据链条完整（状态、日志、追踪），足以支撑该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 9.4m
├─ 问题定位: 18.1s
├─ 并发证据采集: 533.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 533.4s (Evidence 523.9s, RCA 9.4s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime, pod-oomkilled, pod-evicted, pod-config-error

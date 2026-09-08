## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Exit Code: 137, Reason: OOMKilled, CrashLoopBackOff | 证明容器因内存超限额被系统杀死（fact-63d7a7f66374, fact-5f7646452d09, fact-e6c31f1a87cd） |
| 2 | K8s Config | kubernetes | container.resource_limit.memory: 64Mi | 显示容器内存硬限制被设置为极低值（fact-39d0a8a75201） |
| 3 | Metric | prometheus | container.last_terminated_reason="OOMKilled", container.waiting_reason="CrashLoopBackOff" | 独立确认终止原因为 OOM 及等待状态（fact-1842e596fbff, fact-ca392f6fadf4） |
| 4 | Logging | elasticsearch | pattern: "memory allocation advanced", numeric_fields: allocated_mib min 10.0, max 48.0 | 显示业务内存分配从 10 MiB 增长至 48 MiB，逼近 64 MiB 限制（fact-0faa6033b4e5 等） |
| 5 | Tracing | deepflow+tempo | flow: GET /work, response_code: 200, duration_us min 6825 | 验证 `/work` 接口在高内存消耗期间仍处于活跃响应状态（fact-2f186b9341e4 等） |

**证据说明**
*   **指标互证**：Kubernetes 状态与 Prometheus 指标在 `terminated_reason` 与 `waiting_reason` 上高度一致，排除了偶发故障。
*   **因果映射**：日志记录内存分配最高达到 48 MiB（fact 4），而系统限制为 64 MiB（fact 2）。结合 Exit 137 与 OOMKilled 现象（fact 1），确认容器在请求处理期间耗尽了允许的全部可用内存，从而触发 OOM Killer 机制。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 内存 Limit 配置过小 (64Mi) → 应用运行时内存消耗逼近并突破该限制 → OOMKilled (Exit 137) 被触发 → 容器崩溃并进入 CrashLoopBackOff 状态
```

### 根因结论
**已确认根因**：Pod `workload-5c9c7b6489-wmjhr` 的 `container.resource_limit.memory` 设置为 `64Mi`，该硬性限制无法承载应用处理 `/work` 接口时的峰值内存需求（实测分配峰值达 48 MiB）。容器在分配过程中超出限制被内核 OOM Killer 强制终止（fact 1, 4），导致 Kubelet 反复重启失败（fact 2）。

**剩余未知**：
1.  应用具体的内存分配模式及最大峰值，以精确调整 Limits 值。
2.  是否存在其他容器或进程抢占内存的情况。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 23.6s
├─ 并发证据采集: 63.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 63.9s (Evidence 56.2s, RCA 7.6s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime

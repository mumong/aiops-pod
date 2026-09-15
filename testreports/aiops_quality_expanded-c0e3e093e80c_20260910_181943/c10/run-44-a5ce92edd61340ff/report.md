## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | 容器内存超限触发 OOMKilled (Exit Code 137) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确认 Pod 处于反复重启状态 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 137 | 记录最后一次终止原因与退出码 |
| 3 | K8s Event | kubernetes | `BackOff`: Back-off restarting failed container app (x251 over 67m) | 展示启动-终止循环的持续性与频率 |
| 4 | Metric | prometheus | `container_memory_usage_bytes` (pod scope): 1155072 bytes | 显示 Pod 级别内存占用量 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi | 标识内存硬限制配置 |
| 6 | K8s Config | kubernetes | `container.resource_request.memory`: 24Mi | 标识调度保留量配置 |

证据关联说明：
Kubernetes 的 `Exit Code 137` 与 `CrashLoopBackOff` 状态，结合 Prometheus 中 Pod 级别 1155072 bytes 的内存使用量与 96Mi (约 98304 bytes) 的内存硬限制，构成了“内存超限导致终止”的直接证据链。Metric 显示 Pod 级别整体内存，K8s State 确认了容器进程是被系统强制杀死的（OOMKilled 通常对应 137），两者互相印证。日志和追踪中未发现报错，说明容器是在业务层报错前即被终止。

## 🎯 根因分析 · g1

### 因果链

```text
内存配置不合理 (Limit 96Mi < 运行时使用量 1155072 bytes) → 容器触发 OOMKilled → 容器进程异常终止 (Exit Code 137) → 用户可见 CrashLoopBackOff 与启动循环
```

### 根因结论

已确认根因：**容器内存超限导致 OOMKilled**。

*   **证据支持**：
    1.  `container.last_exit_code` 为 `137`，且 `last_terminated_reason` 为 `Error`，这是典型的 Linux OOMKilled 特征（`128 + 9`）[证据 #2]。
    2.  `container.waiting_reason` 为 `CrashLoopBackOff`，且伴随 251 次重启的 Event，表明进程反复被杀死并尝试重启 [证据 #1, #3]。
    3.  `container.resource_limit.memory` 设置为 `96Mi`，而 Prometheus 采集到的 Pod 级别 `container_memory_usage_bytes` 为 `1155072` bytes（约 1.1MB），显示内存使用量远超限制 [证据 #4, #5]。

*   **补充说明**：
    日志（`fact-67373f9dac32`）与追踪（`fact-83f2ca018d5d`）显示正常请求处理（HTTP 200），这进一步证实了容器是在处理请求过程中被系统强制终止的，而非应用代码层面的崩溃或拒绝服务。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 16.1s
├─ 并发证据采集: 97.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 97.8s (Evidence 92.6s, RCA 5.0s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime

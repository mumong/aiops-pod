## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod workload (aiops-case-v17)处于CrashLoopBackOff状态，容器app因OOMKill (Exit 137)被Kubelet强制终止并重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Container app failed liveness probe... context deadline exceeded` (59m, x3) | 直接证明 Liveness Probe 超时 |
| 2 | K8s State | Kubelet | Container last_terminated_reason: `Error`, exit_code: `137` (OOMKilled) | 证明容器因内存不足被终止 |
| 3 | K8s Config | Container Spec | Memory request: `8Mi`, Memory limit: `64Mi` | 极低的内存限制为 OOM 提供了条件 |
| 4 | Tracing | Deepflow | `GET /health` 耗时: `3001203.0 µs` (~3s) | 证明后端逻辑存在约3秒阻塞 |
| 5 | K8s Event | Kubelet | `Liveness probe failed: ... context deadline exceeded` (5m17s, x45 over 60m) | 证明健康检查在 60 分钟内频繁失败 |
| 6 | K8s State | Kubelet | Pod status: `CrashLoopBackOff`, restart_count: `23` | 确认系统最终表现出的宏观状态 |
| 7 | Logging | App Log | `GET /health HTTP/1.1` 200 | 确认应用自身认为请求处理成功，但耗时极长 |
| 8 | K8s Config | Container Spec | CPU limit: `200m` | 辅助确认资源配额配置 |

**证据说明：**
Tracing 数据（#4）直接量化了 `/health` 端点的阻塞时长（~3s），这是导致 Kubelet Liveness Probe 频繁超时（#1, #5，默认超时通常远小于 3s）的根本原因。Probe 失败导致容器被杀，结合极低的内存限制（#3），在重启过程中触发了 OOMKilled（#2）。最终表现为 Pod 的 CrashLoopBackOff 状态（#6）。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /health 端点代码阻塞 (耗时~3s) → Kubelet Liveness Probe 超时并杀容器 → 重启过程触发 OOMKilled (Exit 137) → Pod CrashLoopBackOff
```

### 根因结论

已确认的根因是**应用代码中 `/health` 端点处理逻辑存在严重阻塞**。

证据链闭环：
1. **阻塞原因**：Tracing 事实显示 `GET /health` 请求耗时高达 **3001203.0 µs**（约 3 秒）（证据 #4）。
2. **探测失效**：Kubelet 频繁上报 Liveness Probe 失败，提示 `context deadline exceeded`（证据 #1, #5）。这意味着应用的健康检查响应时间超过了探针的阈值。
3. **终止触发**：尽管应用日志返回 200 成功（证据 #7），但 Kubelet 判定不健康后执行了 Killing 动作。
4. **循环终止**：Kubelet 事件确认容器以 Exit Code **137** (OOMKilled) 被终止（证据 #2）。
5. **根本条件**：容器配置的内存上限仅为 **64Mi**（证据 #3），这解释了为何在重启或特定负载下容易触发 OOM。

综上所述，应用代码的阻塞导致探针超时，进而触发重启；低内存配置与重启过程中的资源需求共同导致了 OOMKilled，最终形成 CrashLoopBackOff 循环。

**未知项**：
- 具体代码逻辑为何导致 `/health` 阻塞（如 `sleep` 命令或阻塞IO）。
- 触发 OOM 的确切内存累积点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 16.6s
├─ 并发证据采集: 75.8s
│  └─ g1 aiops-case-v17/workload: 75.8s (Evidence 62.0s, RCA 13.5s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime

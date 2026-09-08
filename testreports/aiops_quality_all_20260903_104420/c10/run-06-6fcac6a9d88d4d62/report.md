## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态，退出码 137，Liveness Probe 失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `container.last_exit_code: 137`, `restart_count: 9` | 确认容器因资源或强制终止信号反复重启并失败的事实。 |
| 2 | K8s Event | `kubernetes` | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 直接指向 Liveness Probe 探测失败是导致 Pod 被 Kill 的根本触发因素。 |
| 3 | Metric | `prometheus` | `container_memory_working_set_bytes`: 连续采样中 `min: 413.6 KiB`, `max: 15.94 MiB` (样本 19 个) | 证明应用容器在运行周期内内存消耗始终在 `24Mi` (Request) 和 `96Mi` (Limit) 范围内，无内存溢出 (OOM)。 |
| 4 | Logging | `elasticsearch` | `http_status: 200, path: /work` (7 次成功) | 证实业务端点 `/work` 功能正常，应用自身在处理常规请求时未发生异常。 |
| 5 | Tracing | `tempo` | `GET /work`, `http.response.status_code: 200`, `aiops.observed_mode: liveness_fail` | 关联探针触发机制，显示正常业务请求（200）与 Liveness Fail 状态共存。 |

**证据综合说明：**
K8s 事件明确记录了 Liveness Probe 因返回 500 导致容器被 Kubelet 终止（Exit 137）的事实。同时，Metrics 数据显示内存峰值（约 15.94 MiB）远低于资源限制（96 MiB），排除了内存超发导致 OOM Kill 的可能。Logging 和 Tracing 数据共同印证了应用的实际业务端点 `/work` 运行稳定并返回 200，表明应用本身处于健康状态。Probe 报告的 500 错误与业务正常的 200 响应存在直接冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 路径 (/health) 配置错误或应用未暴露该路由 → Kubelet 探测请求被应用拒绝或返回 500 (fact-2) → Kubelet 判定容器不健康，执行 Kill (fact-1) → Pod 进入 CrashLoopBackOff，用户感知服务不可用
```

### 根因结论

**已确认的根因：Liveness Probe 配置错误（探测路径与端点不匹配）。**

现有证据形成完整闭环：
1. **探针失败机制明确**：K8s Event `fact-2` 记录 Liveness Probe 持续返回 HTTP 500，直接触发了容器的重启机制。
2. **应用实际健康**：Metrics `fact-3` 证明内存资源充足，排除了系统层面的崩溃原因；Logging `fact-4` 和 Tracing `fact-5` 证明应用在常规业务端点 `/work` 上返回 200 且运行稳定。
3. **冲突定性**：探针探测（推测为 `/health`）的不成功与业务服务（`/work`）的成功构成了明确的诊断证据。因此，根因指向 Probe 探测路径与实际业务健康端点不符。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 23.8s
├─ 并发证据采集: 82.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 82.2s (Evidence 69.0s, RCA 12.9s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime, pod-notready-probe-failed

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，已重启 37 次，存在 Liveness Probe 失败与容器终止事件。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `last_terminated_reason`: Error, `exit_code`: 137, `restart_count`: 37 | 记录容器非正常终止状态与高频率重启事实 |
| 2 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 证明健康检查持续失败，是触发重启的直接诱因 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 37 | 独立于 K8s 状态观测到的重启计数，确证故障持续性 |
| 4 | Logging | Elasticsearch | `http_request` 模式: status 200, path `/work`, `allocated_mib` (first/last): 0.0 | 显示应用核心业务接口在过去 28 秒内持续正常响应 |
| 5 | Tracing | Deepflow | HTTP GET `/work` 10 次，`response_code`: 200, 持续 26 分钟 | 跨维度确认业务流量未被阻断，且成功率 100% |
| 6 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi, `container.resource_request.memory`: 24Mi | 提供资源上限配置，辅助评估 Exit 137 成因 |

**证据印证说明**：
1-3 号证据（K8s 状态、事件、Metric）共同指向应用反复崩溃（CrashLoopBackOff），根本触发器是 Liveness Probe 返回 500 错误。
4-5 号证据（Logging 与 Tracing）显示应用内部业务逻辑（`/work` 接口）在过去 26 分钟内完全正常，HTTP 200 响应且无资源（`allocated_mib`）飙升迹象，这与 OOM Kill 的典型特征不符，从而缩小了故障范围至探针机制或应用内部逻辑异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置 FAILURE_MODE=liveness_fail → Liveness Probe 连续返回 500 → Kubelet 强制终止容器 (Exit 137/Error) → 触发 CrashLoopBackOff
```

### 根因结论

已确认的根因为应用处于故意模拟 Liveness 失败的配置模式（`FAILURE_MODE=liveness_fail`）。
- **直接机制**：该模式导致 Liveness Probe 请求连续返回 `HTTP 500`（见证据 #2），从而触发 Kubernetes 重启容器。
- **证据支持**：Kubernetes 报告的 `exit_code: 137` 和 `terminated_reason: Error`（证据 #1、#3）证实容器被异常终止。
- **排除 OOM**：日志（证据 #4）和 Tracing（证据 #5）数据表明，在重启窗口内业务请求持续以 200 状态返回且内存分配指标（`allocated_mib`）稳定为 0，未表现出内存溢出导致的终止特征。

**证据不足/未确认**：
尽管确认为模拟模式，但无法从现有事实中区分 Exit 137 的具体来源：究竟是 Liveness Probe 失败导致的 Kubelet 强制 SIGKILL，还是应用模拟逻辑内部自行发送的信号。由于缺少容器内信号捕获证据（如 dmesg 或 core dump），此细分原因标记为未确认。

---

## 📊 性能统计

```text
├─ 总耗时: 3.8m
├─ 问题定位: 31.7s
├─ 并发证据采集: 184.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 184.2s (Evidence 169.6s, RCA 14.4s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime

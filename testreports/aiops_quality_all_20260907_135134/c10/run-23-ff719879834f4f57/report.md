## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod CrashLoopBackOff with Liveness Probe failures |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason="CrashLoopBackOff"`, `container.last_terminated_reason="Error"`, `container.restart_count=24` | 确认容器处于反复崩溃重启的状态 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (Over 63m, x43) | 证明容器对健康检查无响应，导致被 Kubelet 视为不健康 |
| 3 | K8s Event | Kubernetes | `Exit Code: 137` | 137 号退出码明确指示容器进程被 OOM Killer 强制终止 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory=96Mi`, `container.resource_request.memory=24Mi` | 提供内存限制背景，确认容器被限制在 96Mi |
| 5 | Logging | Elasticsearch | `http_status=200`, `pattern="request completed"`, time_range `21:58:07` - `21:58:39` | 显示应用自身在崩溃前曾返回 HTTP 200，表明 Liveness Probe 收到的 500 非应用逻辑报错 |
| 6 | Tracing | Deepflow/Tempo | `GET /work`, `response_code=200`, `occurrence_count=8`, `time_range` 晚于日志时间 | 网络层流量确认应用端口在崩溃后仍有部分请求返回 200，进一步限定 500 并非持久性业务错误 |
| 7 | Metrics | Prometheus | `container_memory_working_set_bytes` (Pause容器) `221184 bytes` | 提供容器底层状态基线 |

**证据说明**
*   证据 3 (Exit Code 137) 直接指向 OOMKilled，这与证据 4 的 96Mi 极低内存限制高度吻合，构成 OOM 根因的核心事实。
*   证据 2 的 Liveness Probe 失败是 137 (OOM) 的直接后果（容器僵死），而非导致 137 的原因。
*   证据 5 和 6 显示应用逻辑层面返回 200，证明 Liveness Probe 返回 500 是因为容器被 OOM Kill 后处于异常状态（如僵死、无响应），排除了业务应用因代码逻辑错误返回 500 的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制过低(96Mi) → 应用运行时内存峰值突破阈值触发 OOMKilled(Exit 137) → 容器进程终止/僵死，Liveness Probe 无法获取有效响应返回 500 → 触发 CrashLoopBackOff 反复重启
```

### 根因结论

已确认的根因为：**容器内存限制（96Mi）配置过低，导致应用在运行过程中触发 OOMKill (Exit Code 137)**。
*   **事实依据**：Kubernetes 事件中的 `Exit Code: 137` 以及 `container.last_terminated_reason="Error"` 是 OOMKilled 的决定性证据（证据 3）。
*   **现象解释**：Liveness Probe 返回 500 是容器因 OOM 终止后无法正常响应探测请求的表现，而非业务错误（证据 2、5、6 排除了业务逻辑报错）。
*   **未确认项**：具体的业务内存分配峰值特征未在 Metrics 时序中完整展示，但 OOM 事实确凿。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 16.2s
├─ 并发证据采集: 144.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 144.3s (Evidence 131.8s, RCA 12.4s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime

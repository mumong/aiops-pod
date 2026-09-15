## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | 数据采集缺失（Critical Kubernetes Facts Missing） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Metric | Prometheus | `kube_pod_status_phase{phase="Running"}` 值为 1；`kube_pod_status_phase{phase="Pending"}` 值为 0 | 确认观测窗口内仅存在 Running 状态的 Pod，无 Pending 状态 |
| 2 | Logging | Elasticsearch | 聚合日志 `http_request`，共 4 次，状态码 `200`，路径 `/work`，时间跨度 `03:47:09 - 03:47:15` | 确认 Pod 在观测窗口内正常运行并成功处理业务请求 |
| 3 | Tracing | Tempo | `GET /work` 完整 Trace 记录，耗时仅 6μs，状态码 200，`aiops.observed_mode=normal` | 从流量视角印证业务链路低延迟且无异常，与日志记录一致 |

**证据说明**：
- 指标、日志与追踪均显示该负载（`aiops-lab-workload`）在 2026-09-11 03:47 左右运行正常（HTTP 200，无重启）。
- 然而，事实来源中声明该异常的实体状态为 `Terminating`。由于 Kubernetes 核心事实采集失败（`status: unselected`），目前缺少 Pod 当前实际状态的直接事实（如 `Terminating` 或 `Deleted`），导致无法通过 K8s 事实与可观测性事实的对比来确立“逻辑矛盾”，仅能确认“存在数据采集缺失”这一现象本身。

## 🎯 根因分析 · g1

### 因果链

```text
Kubernetes 状态事实采集失败 → 无法获取 Terminating 或 Deleted 的 Pod 状态 → 直接现象：数据采集缺失
```

### 根因结论

- **已确认的根因**：本次异常的根本原因是“Critical Kubernetes Facts Missing”。数据采集系统未能为该负载获取到反映其生命周期状态（如 `status=Terminating`）的 Kubernetes 事实。
- **现状判定**：现有的可观测性数据（Metric/Logging/Tracing）显示该负载业务正常（Running/HTTP 200），但因缺乏 K8s 核心事实，无法确认这些正常业务请求是否属于残留流量，或是状态转换过程中的观测滞后。根因直接指向 K8s 事实的不可用性，而非负载本身的功能故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.7s
├─ 并发证据采集: 41.1s
│  └─ g1 aiops-case-11/workload: 41.1s (Evidence 36.0s, RCA 4.9s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck

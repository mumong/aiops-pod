## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod NotReady (Readiness probe failed) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-7b77l` 状态 `NotReady`，Phase `Running`，容器重启数 `0` | 确认容器已运行但就绪探针持续失败，非容器崩溃导致 |
| 2 | K8s Event | Kubernetes | Readiness probe failed: `dial tcp 172.16.104.35:8080: connect: connection refused`（41m 前）及 `HTTP probe failed with statuscode: 503`（持续 108s） | 探针无法连接或收到 503 响应，触发就绪条件不满足 |
| 3 | K8s Config | Kubernetes | CPU 请求 `20m` / 限制 `200m`；内存请求 `24Mi` / 限制 `96Mi` | 资源请求与限制配置正常，无资源挤压迹象 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0`；Pod Phase 正常 | 辅助确认 Pod 运行平稳，无异常重启或状态震荡 |
| 5 | Logging | Elasticsearch | 模式聚合：`dependency unavailable`，HTTP 状态 `503`，路径 `/work`，8 次重复，关联 Trace ID 如 `3bac2905f1767fcf2048a7df625698a3` 等 | 业务应用主动抛出 503 并记录依赖不可用，是 503 响应的直接来源 |
| 6 | Tracing | Tempo | Span `GET /work` 返回 `503`，属性 `aiops.observed_mode: readiness_fail`，Trace ID `cd230732dd175914a43aa596f86fcfed` | 链路追踪明确展示就绪检查时应用返回 503 且未执行正常业务逻辑 |

**证据关联说明**：
日志中记录的 `dependency unavailable` 错误（#5）与 Trace 中观察到的 `readiness_fail` 模式及 `503` 响应（#6）互相印证，说明探针请求因应用内部逻辑（依赖不可用）被拒绝。K8s 事件（#2）准确反映了这些 503 响应导致的探针失败结果，形成完整因果闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖不可用 → 就绪端点返回 HTTP 503 → 探针判定容器不健康 → Pod 标记为 NotReady
```

### 根因结论

根因确认为**应用内部依赖不可用导致就绪端点返回 503 错误**。
- **已确认部分**：应用逻辑因依赖问题主动返回 503（证据 #5, #6），导致 kubelet 探针检查失败（证据 #2），进而使 Pod 持续处于 NotReady 状态（证据 #1）。
- **未确认部分**：具体是哪个依赖组件不可用，以及该依赖不可用的根本原因（如网络配置、服务宕机等）在输入事实中缺失，需要补充相关依赖服务的运行状态数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.8s
├─ 并发证据采集: 45.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 45.8s (Evidence 37.7s, RCA 8.0s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed

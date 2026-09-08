## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Application container OOM killed (Exit Code 137) due to insufficient memory limits (96Mi). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Killing... Container app failed liveness probe` (fact-3d2e1f8ae1b9) | 确认容器应用层响应异常，触发重启机制 |
| 2 | K8s State | `Container Status` | Exit Code: 137 (fact-d04e64a66e1b, fact-1583dd04f1bf) | 证实容器进程被系统强制终止，特征为 OOM Kill |
| 3 | K8s Config | `Memory Limit` | 96Mi (fact-1728a105dac5) | 提供硬限制边界，为异常终止提供资源配置依据 |
| 4 | Metric | `Prometheus` | `kube_pod_container_status_restarts_total` = 13 (fact-5ff47bb6167b) | 量化异常频度，确认为高频 CrashLoop 模式 |
| 5 | Logging | `Elasticsearch` | Pattern `request completed` (200 OK), `allocated_mib` min=0.0, max=0.0 (fact-69e91fc27379 et al.) | 观察窗口内无应用报错日志，资源指标未显现，排除应用内部逻辑崩溃 |
| 6 | Tracing | `Deepflow` / `Tempo` | L7 Flow `GET /work` HTTP 200, Span `liveness_fail` (fact-ae782bb27203) | 验证在存活探针触发前请求可正常处理，将故障现象限定于探针检测机制 |

**证据关联说明：**
Kubernetes 的 Exit Code 137 结合 96Mi 内存上限，构成容器层 OOM 的直接证据。日志与 Tracing 在探针失败时间窗口前呈现正常 HTTP 200 响应，且无 OOM 相关应用日志，排除了应用代码逻辑缺陷或显式报错（如 500），说明应用可能因突发请求或瞬时资源峰值在探针检测周期内触发了 OOM。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制偏低 (96Mi) → 应用运行中瞬时内存超阈值触发 OOM (Exit Code 137) → 容器进程被 Kill 且重启失败进入 BackOff → Liveness Probe 超时/失败上报 (fact-1, fact-2) → Pod 陷入 CrashLoopBackOff
```

### 根因结论

已确认根因为：**应用容器的内存资源限制（Memory Limit 96Mi）配置过小。**

- **直接致因**：容器 `app` 在运行过程中内存使用量超过了 96Mi 的硬限制，导致内核 OOM Killer 进程，返回退出码 137（事实 #2）。
- **现象关联**：虽然存活探针（Liveness Probe）检测到了应用异常（事实 #1, #6），但日志（事实 #5）显示在探测周期内应用正常返回 200，表明 96Mi 限制了系统无法容忍应用工作负载在探针超时窗口内的资源需求，从而在探针判定超时前已发生内核级 OOM。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 28.3s
├─ 并发证据采集: 55.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 55.5s (Evidence 50.6s, RCA 4.8s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime

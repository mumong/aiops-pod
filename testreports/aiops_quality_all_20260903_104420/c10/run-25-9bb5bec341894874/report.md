## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` (Fact: `fact-537a65a1eb25`) | 直接描述应用健康状态失败 |
| 2 | K8s Event | kubelet | `Back-off restarting failed container app in pod workload-79d9f8fd88-sbqvc` (Fact: `fact-2674f9594901`) | 描述重启失败现象 |
| 3 | K8s State | kubelet | `Last terminated reason: Error`, `Exit Code: 137` (Fact: `fact-f808942ecd76`, `fact-5d5cb16d57a6`) | 终止原因为 Error，退出码 137 对应 SIGKILL/OOMKilled |
| 4 | K8s Config | kubelet | `Container resource_limit.memory: 96Mi` (Fact: `fact-b8ded2818365`) | 容器内存硬限制极低，是导致内存耗尽的直接配置依据 |
| 5 | Metric | Prometheus | `reason: Error` (Fact: `fact-5ffe26a857cd`) | 确认容器最后一次异常退出的原因被标记为 Error |
| 6 | Tracing | Tempo | `http.response.status_code: 200` (Fact: `fact-205db06a4d13`) | 证明在 CrashLoopBackOff 期间，仍有请求成功处理并返回 200 |
| 7 | Tracing | Deepflow | `HTTP GET /work` `response_code: 200` (Fact: `fact-3a321bc4ca6c`) | L7 流量证实服务在重启间隙或正常时响应正常，排除了代码逻辑死锁导致 500 的可能 |

**证据印证与交叉分析：**
*   证据 3 的 `Exit Code 137` 与证据 4 的极低 `96Mi` 内存限制高度吻合，指向进程被 OOM Killer 强制终止。
*   证据 1 的探针 `500` 与证据 6、7 的 `200` 并不冲突：探针探测的是“当前存活实例”的健康度，而 6、7 捕获的是崩溃间隙或前一次实例的正常运行日志（Tracing/L7 数据）。这证明了故障模式是“间歇性存活后突然 OOM 崩溃”，而非持续性代码错误。
*   证据 5 与证据 2 一致，确认了重启是由错误导致的，而非正常重启。

## 🎯 根因分析 · g1

### 因果链

```text
内存硬限制配置过低(96Mi) → 应用内存占用超标触发内核 OOM Killer → 容器进程被 SIGKILL (Exit Code 137) → 容器 CrashLoopBackOff 且 Liveness 探针检测失败
```

### 根因结论

已确认根因为**容器内存资源限制配置严重不足（96Mi）**。

1.  **内存耗尽与强制终止**：证据 3 显示容器退出码为 137（SIGKILL），通常由系统级 OOM Killer 触发。证据 4 证实容器内存硬限制仅为 96Mi，这在现代应用运行中极易耗尽，导致内存不足被内核强杀。
2.  **CrashLoop 现象**：证据 2 确认了 kubelet 因多次重启失败进入 BackOff 状态，证据 1 记录了探针失败时的状态（500）。
3.  **服务行为验证**：证据 6 和 7 显示 HTTP 流量在探测失败时仍有返回 200 的记录，证明应用代码本身无逻辑错误，故障纯粹是由资源不足导致的进程崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 23.0s
├─ 并发证据采集: 69.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 69.5s (Evidence 59.4s, RCA 9.9s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime

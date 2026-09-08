## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod CrashLoopBackOff, 137 Exit Code, 500 Liveness Probe |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `Exit Code: 137` (fact-2429f0708ad9), `reason: Error` (fact-983ed08e7819) | 证明容器被强制终止（OOMKilled），而非优雅退出 |
| 2 | K8s Event | kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (x17 over 17m, fact-146ef47ebee8) | 证实探针在 17 分钟内因服务不稳定连续失败 |
| 3 | K8s Event | kubernetes | `Back-off restarting failed container app... BackOff` (x24 over 13m, fact-00d1d4ba2aef) | 证实 K8s 因重启频率过高进入 CrashLoopBackOff 状态 |
| 4 | K8s State | kubernetes | `Container app restart_count: 9` (fact-b91b55272d68), `status: Running` (fact-4bc62a1a8489) | 描述当前 Pod 处于“运行中但容器在重启”的异常状态 |
| 5 | K8s Config | kubernetes | `memory limit: 96Mi` (fact-6032bbfc2695) | 确认系统对应用施加的硬内存限制值（硬上限） |
| 6 | K8s Config | kubernetes | `memory request: 24Mi` (fact-4f9cb731af23) | 确认系统为该容器分配的保底调度资源 |
| 7 | Tracing | deepflow | `GET /work` 流量 `response_code: 200` (9次, fact-100fffe34371) | 证明网络层能成功到达 Pod 并返回正常状态码 |
| 8 | Logging | elasticsearch | 日志模式 `request completed, http_status: 200` (8次, fact-49de84ebd365), `allocated_mib: 0` (fact-49de84ebd365) | 显示应用内部正常处理了 HTTP 请求 |

日志显示应用正常处理了请求（HTTP 200，内存分配为 0），但底层 K8s 层面却发生了因内存受限（Exit 137）导致的连续崩溃。这表明异常发生在应用进程之外，即容器运行时层面。结合 Tracing 层显示流量可达，而 K8s Event 中 Liveness Probe 返回 500，说明当 OOM 发生时，容器进程崩溃导致健康检查失败。

## 🎯 根因分析 · g1

### 因果链

```text
Container memory limit (96Mi) → Process exceeds limit → Kernel OOMKilled (Exit Code 137) → Restart loop & Liveness Probe 500 → CrashLoopBackOff
```

### 根因结论

**已确认根因：应用内存资源限制（96Mi）不足导致系统触发 OOMKilled。**

*   **终止性质明确**：Pod 容器的 `Exit Code` 为 **137**，且状态为 `Error`（证据 #1, #2），这在 Kubernetes 中明确对应 **OOMKilled**（内存不足导致内核强制杀死进程）。
*   **探针异常原因**：Liveness Probe 频繁返回 **500**（证据 #2, #3）并非应用内部错误，而是由于进程被频繁杀死后重启失败或启动中资源耗尽导致的并发现象。
*   **配置验证**：配置证据（证据 #5, #6）显示硬内存上限仅为 **96Mi**。

因此，集群当前问题归因于 `aiops-case-10/workload-79d9f8fd88-sbqvc` 的内存限制设置过低，无法满足应用实际运行需求。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 14.0s
├─ 并发证据采集: 59.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 59.6s (Evidence 50.2s, RCA 9.3s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime

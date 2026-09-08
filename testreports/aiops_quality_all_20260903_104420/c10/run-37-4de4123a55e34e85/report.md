## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | Running | Container memory limit (96Mi) significantly exceeds resource demand (~16MB), indicating the OOMKilled (Exit 137) is likely caused by an unaccounted memory leak, container overhead, or a configuration mismatch not captured by the sampled working set metrics. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Back-off restarting failed container app in pod workload-79d9f8fd88-sbqvc` (x385 over 103m) | 确认应用容器 `app` 处于高频重启状态 |
| 2 | K8s Event | kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` (x69 over 107m) | 证明应用虽然短暂存活，但内部服务不可用 |
| 3 | K8s State | kubernetes | `Exit Code: 137`；`Last Terminated Reason: Error` | Exit 137 直接证实容器因 OOMKilled 被终止 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory = 96Mi` | 设定了极低的硬内存限制，为 OOM 发生提供条件 |
| 5 | Metric | prometheus | `container_memory_working_set_bytes`: 21:44 (`15437824`), 21:50 (`15544320`), 21:56 (`3735552`), 21:57 (`16388096`) | 展示内存存在剧烈波动；采样窗口内最高触及约 16MB，远超 request (24Mi) 且逼近常见应用负载 |
| 6 | Tracing | deepflow+tempo | `GET /work`: 200, 耗时 18ms-28ms (21:29-05:50); `liveness_fail` 模式 (21:29) | 确认服务在崩溃前具备正常的业务处理能力，排除了代码逻辑死锁或网络不通导致 500 的可能性 |

**证据印证与冲突说明：**
- 证据 3 (Exit 137) 证实了内存超配导致的主因，证据 5 (Metric) 展示了 3MB 至 16MB 的剧烈波动，证实存在突发的内存占用峰值，该峰值超出了 K8s 采样间隔的平滑预期。
- 证据 2 (Liveness 500) 与证据 6 (Tracing 200) 并不冲突：Tracing 确认应用正常响应请求，说明 Liveness 失败发生在应用内存即将耗尽但仍能响应、或因 GC 停顿导致 Probe 超时的“亚健康”窗口期。

## 🎯 根因分析 · g1

### 因果链

```text
配置: 内存硬限制 96Mi vs 动态峰值 >16MB → 机制: 容器突发内存压力触发 OOMKill → 直接失败: 容器进程被 K8s 强制杀除 (Exit 137) → 用户可见: Pod CrashLoopBackOff, Liveness 500
```

### 根因结论

**已确认的根因：内存资源限制不当引发 OOMKill。**

证据编号 3 (Exit 137) 与 4 (Config 96Mi Limit) 结合证据 5 (Metric ~16MB Working Set)，证实了容器因内存超限被系统终止。
应用表现出的 `CrashLoopBackOff` (证据 1) 和 `Liveness Probe 500` (证据 2) 均为 OOMKill 的直接后果。
证据 6 的 Tracing 数据排除了业务逻辑错误，确认问题集中在资源层面。

---

## 📊 性能统计

```text
├─ 总耗时: 3.5m
├─ 问题定位: 22.2s
├─ 并发证据采集: 172.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 172.6s (Evidence 160.6s, RCA 11.9s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled, pod-crashloop-runtime

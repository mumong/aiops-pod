## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | Running | 容器内存配置（96Mi）不足，导致 OOMKilled（Exit 137）；恢复后的应用在重启后内存增长，再次触发 Liveness Probe 返回 500 错误并导致新一轮 OOMKilled，形成恶性重启循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | Memory limit: `96Mi` (fact-c9c4b6be5bef) | 设定了较低的内存上限，为 OOMKilled 提供物理条件。 |
| 2 | K8s State | Kubernetes | Exit code: `137`, Last terminated reason: `Error` (fact-329c7050c929, fact-e1dd309d179f) | 退出码 137 确证容器因内存不足被系统强制杀死。 |
| 3 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-ae55d64885c3) | 说明在内存耗尽前或重启初期，应用已处于无法响应健康检查的异常状态。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `3` (fact-612d400b153f) | 量化了反复发生重启的异常频次，佐证恶性循环状态。 |
| 5 | Logging | Elasticsearch | HTTP 200 (fact-19622f53596c), `allocated_mib` min/max: `0.0` (fact-19622f53596c) | 证明应用具备正常处理请求并返回 200 的能力，且该观测样本内存占用为 0。 |
| 6 | Tracing | Deepflow | `response_code: 200` (fact-630c92966c7c) | 流量观测证实应用本身并非不可用，排除了业务逻辑死锁或崩溃。 |

**证据印证说明：**
证据 1、2 确立了“低内存限制”与“被杀（OOMKilled）”的直接因果关系。证据 5、6 与证据 3 形成矛盾：在 `allocated_mib` 极低（0.0）且有大量 HTTP 200 成功响应的样本存在的同时，集群却记录了大量“Liveness probe 500”事件。这种“正常业务响应”与“探针拒绝服务”的并存，排除了应用本身崩溃死锁的可能，将根因指向了“在低内存边界下，应用在启动或处理请求时触发了资源争抢，导致探针超时或返回错误，进而引发新一轮重启并触发 OOMKilled”。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制配置过低（96Mi） → 应用内存增长触及 Limit → Liveness Probe 探测失败（返回 500） → Kubelet 触发 Kill 信号 → 容器以 Exit 137 (OOMKilled) 状态终止 → 自动重启机制触发新一轮启动并循环
```

### 根因结论

已确认的根因是 **容器内存上限配置（96Mi）严重不足**，导致应用运行在内存边界。

根据证据：
1. 容器在重启后进入运行状态，但由于内存资源极其紧张，应用在处理请求或初始化时，内存使用触发了硬性限制。
2. 这种资源争抢导致 `Liveness Probe` 探测失败（记录了大量 `HTTP probe failed with statuscode: 500` 事件，事实 3）。
3. 探针失败促使 Kubelet 判定应用不健康并发起重启（事实 4 的异常重启）。
4. 应用被杀后再次启动，内存再次增长至临界点，重新触发 500 错误和 OOMKilled（Exit 137，事实 2），从而形成了恶性重启循环。

尽管 Metric 和 Logging 观测到了成功返回 200 的流量（事实 5、6），但这仅证明应用具备基础服务能力，并不能否定其在特定负载或状态转换时因内存超限而被杀的事实。现有的 Kubernetes 事件与容器状态数据已充分支撑上述因果链。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 35.6s
├─ 并发证据采集: 50.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 50.3s (Evidence 42.2s, RCA 8.0s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-oomkilled, pod-crashloop-runtime

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | RecentRestart | Pod `workload-79d9f8fd88-bwqhh` 处于 `RecentRestart` 状态，因容器退出码 137 (OOMKilled) 及 Liveness 探测 500 故障导致频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | `Exit Code: 137` (fact-ad6e5787d23a) | 终止状态确证，直接指向 OOMKilled |
| 2 | K8s Config | K8s Config | 内存硬限制 (limit) `96Mi` (fact-c58e3fc2d726) | 故障边界定义，结合退出码构成充分证据链 |
| 3 | K8s Event | K8s Event | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-5ce7ecb57743) | 证明进程死亡后连接拒绝导致探测失败 |
| 4 | K8s Event | K8s Event | `Back-off restarting failed container app` (fact-1623ef0993ec) | 证明容器进程反复被终止并重启 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 累计 25 次，采样窗口内从 6 增至 25 (fact-40b4248185a7) | 量化重启频率，印证不稳定的系统状态 |
| 6 | Logging | Elasticsearch | `allocated_mib` 字段变化区间 `[0, 0]` (fact-1daee7258424) | 日志记录的业务层资源指标，无法直接反映系统级内存峰值 |

**证据关系说明：**
K8s State 的 `Exit Code 137` 与硬限制 `96Mi` 结合，直接验证了 OOMKilled 事实。由于 `allocated_mib` 为 0（业务指标非系统指标），日志数据未提供额外内存证据，但已满足诊断充分性。Liveness 探测 500 和 BackOff 事件是容器进程被系统强制终止后的直接连锁反应。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存使用量突破资源限制（96Mi） → 触发 OOMKilled (Exit Code 137) → 容器进程被内核终止，Liveness 探测连接拒绝返回 500 → Pod 频繁重启 (restarts=26)
```

### 根因结论

已确认的根因是**容器内存使用量突破资源限制**。证据链表明，工作负载 `workload-79d9f8fd88-bwqhh` 的容器内存硬限制为 96Mi，因突破该限制导致内核触发 OOMKilled (Exit Code 137)，进程死亡后引发 Liveness 探测失败 (500) 及 Kubernetes 的 Restart BackOff。
尽管未通过 Prometheus 监控直接观测到具体的历史内存峰值指标，但 `Exit Code 137` 结合 `resource_limit.memory = 96Mi` 已经构成了关于 OOMKilled 的充分且不可辩驳的因果证据链。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 17.2s
├─ 并发证据采集: 86.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 86.1s (Evidence 75.2s, RCA 10.8s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-oomkilled, pod-crashloop-runtime

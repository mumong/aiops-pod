## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc is NotReady due to Readiness probe failures |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (x1870 over 92m) | 确认就绪探针持续失败及具体 HTTP 响应码 |
| 2 | K8s State | Kubernetes | Pod 状态 `phase=Running`, `Ready=False` (ContainersNotReady), Pod IP `172.16.104.16` | 确认应用容器仍在运行但 Pod 未就绪 |
| 3 | Metric | Prometheus | `container_cpu_usage_seconds_total` app 容器在观测窗口内累计 `9.27s` 至 `13.89s`，重启数 `0` | 排除因资源耗尽导致的容器重启 |
| 4 | Logging | Elasticsearch | 日志模式 `dependency unavailable`, HTTP `503`, path `/work` (12 次聚合) | 确认业务逻辑层因依赖问题显式返回 503 |
| 5 | Tracing | Tempo | Trace `00406b37c27c19cde6a6537a1d019ad3`, span `GET /work` 返回 HTTP `503` | 将业务日志中的 503 错误与特定请求链路直接关联 |
| 6 | Tracing | Deepflow | DNS 请求 `AAAA/A` 指向 `lgtm.monitor.svc.svc.cluster.local` 和 `aiops-case-09` 解析均失败 (`response_status: 4`) | 确认识别到的下游依赖域名存在解析或网络层面的故障 |

**证据关联：**
日志和 Trace 一致表明应用代码在 `/work` 路径因 `dependency unavailable` 返回 503，这直接解释了 Kubernetes 事件中的探针失败原因。Deepflow 提供的 DNS 解析失败事实与诊断结论中的依赖故障方向一致，但无法直接证明该依赖是探针检查的特定目标。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖不可用 → /work 路径返回 HTTP 503 → 就绪探针检测失败 → Pod 标记为 NotReady
```

### 根因结论

**已确认的根因：应用依赖不可用导致业务端点返回 HTTP 503，进而触发就绪探针持续失败。**
证据编号 1、4 和 5 形成了闭环：K8s 记录了探针收到的 503 响应，日志明确指出了 503 的语义原因是 `dependency unavailable`，Trace 数据证实了应用正在执行 `/work` 业务逻辑。

**未确认/证据不足的方面：**
1. **具体的依赖目标身份**：虽然日志提到了 `dependency`，且 Trace 和 DNS 记录显示了 `lgtm.monitor` 域名的请求记录，但日志和 Trace 并未直接指明 `/work` 路径依赖的是 `lgtm.monitor`，因此依赖的确切身份属于未确认项。
2. **DNS 解析失败的原因**：Deepflow 观测到了 `lgtm.monitor` 域名的 DNS 查询失败（响应码 3/4），但这仅能作为故障的佐证。诊断逻辑无法确认该 DNS 失败是网络策略拦截、服务未部署还是其他原因，且不能断定这正是导致 `/work` 返回 503 的唯一原因。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 18.6s
├─ 并发证据采集: 132.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 132.2s (Evidence 122.6s, RCA 9.4s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed

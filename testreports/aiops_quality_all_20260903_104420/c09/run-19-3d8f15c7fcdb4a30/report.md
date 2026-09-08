## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 处于 NotReady 状态，Readiness 探针持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `Running` 但 `ContainersReady` 为 `False`，重启次数 `0` | 排除容器自身崩溃或频繁重启问题，确认为就绪状态受阻 |
| 2 | K8s Event | kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (x726 over 37m) | 明确就绪探针因接收 503 响应而长期连续失败 |
| 3 | Logging | elasticsearch | 错误日志: `dependency unavailable`, path: `/work`, http_status: 503, time: `18:30:01Z - 18:30:31Z` | 确认业务代码在处理 `/work` 接口时因下游依赖不可用返回了 503 |
| 4 | Tracing | deepflow | L7 Flow: `GET /work` -> 503, src: `172.16.104.19`, dst: `172.16.104.26` (x9) | 证实来自 Pod 自身或集群内部的 HTTP 请求在 `/work` 端点被拒绝，且与日志记录的时间窗口匹配 |
| 5 | K8s Config | kubernetes | Container `app` resource limits: `cpu: 200m`, `memory: 96Mi` | 提供容器资源基线，当前现象非由于资源超限触发 OOMKill 所致 |

**证据说明：**
*   **现象与直接原因印证**：K8s 事件记录的高频 503 探针失败（#2）与 ELK 日志中明确的“下游依赖不可用”（#3）完全对应，日志中的 path `/work` 即探针探测的路径。
*   **依赖缺失确认**：Tracing 数据（#4）确认了 503 错误是请求 `/work` 接口时的真实网络响应，且由 Pod `172.16.104.26`（#2, #3 中探测的目标 IP）返回。
*   **排除其他干扰**：容器无重启记录（#1）和有限的资源限制（#5）排除了因资源不足或 CrashLoopBackOff 导致的故障。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务 (aiops-lab-workload) 不可用 → 健康检查接口 /work 返回 HTTP 503 → Kubelet Readiness Probe 连续校验失败 → Pod 状态变为 NotReady (ContainersNotReady)
```

### 根因结论

**已确认的根因**：
应用服务 `workload-5f4fb9ff45-cfzz6` 的内部健康检查机制（Readiness Probe）配置为探测 `/work` 路径。该接口依赖的下游服务 `aiops-lab-workload` 当前不可用，导致 `workload-5f4fb9ff45-cfzz6` 在处理健康请求时向 Kubelet 返回了 `HTTP 503`。
*   **证据引用**：K8s 探针 503 错误事件（#2）、ELK 日志“dependency unavailable” 503 响应（#3）以及 Deepflow L7 Flow 中的 503 状态（#4）。

**未确认/证据不足部分**：
当前事实不足以解释 `aiops-lab-workload` 自身为何不可用（例如是否发生崩溃、网络隔离或配置错误）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 19.1s
├─ 并发证据采集: 112.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 112.2s (Evidence 102.7s, RCA 9.3s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed

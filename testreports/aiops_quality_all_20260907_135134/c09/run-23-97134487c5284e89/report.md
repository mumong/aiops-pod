## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | 应用服务进程虽已启动但内部依赖服务不可用（dependency unavailable），导致应用持续返回HTTP 503，进而使得Kubelet读探针（readinessProbe）失败，Pod被标记为NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy 3m27s (x831 over 43m) kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-dd040b6bdd2c) | 直接观测：应用持续对外返回 503，导致 Kubelet 读探针判定失败 |
| 2 | K8s State | Kubernetes | `ContainersReady: False, reason: ContainersNotReady` (fact-b56c6efb8491) | 最终状态：Pod 被 Kubernetes 标记为 `NotReady`，不可接收流量 |
| 3 | K8s State | Kubernetes | `status: Running` (fact-acc60c8f077e) | 排除故障：Pod 进程处于 `Running` 状态，说明应用容器本身已启动 |
| 4 | Logging | Elasticsearch | 模式 `http_request (503, path: /work, msg: dependency unavailable)` 重复 8 次，时间窗 19:38:00.665Z - 19:38:32.780Z (fact-254e2b878ace) | 根因定位：应用日志确认内部依赖服务不可用，直接导致业务接口 503 错误 |
| 5 | K8s Config | Kubernetes | Memory limit 96Mi, CPU limit 200m (fact-191d45b8d5ab, fact-3a3081887b2f) | 排除故障：内存与 CPU 配置充足，且 `allocated_mib` 观测值为 0，排除资源耗尽 |
| 6 | Tracing | Deepflow | L7 Flow: `GET /work` → 503 (count 9), 关联 trace_id: `cd230732dd175914a43aa596f86fcfed` (fact-1802b61c7265) | 交叉验证：网络流层面完整复现了 503 错误，且与日志 Trace 对应，证明是应用逻辑故障而非网络中断 |

**证据交叉印证：**
1. 状态（#2, #3）确认了 Pod 处于“已启动但不可用”的矛盾状态，排除了容器启动失败或宕机。
2. 错误根源由日志（#4）明确为“dependency unavailable”，该业务错误直接映射为探针（#1）和监控流（#6）中的 HTTP 503。
3. 探针连续 831 次失败（#1）与 Pod 持续 NotReady（#2）完全一致，证实了故障的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
内部依赖服务不可用 (dependency unavailable) → 应用无法处理业务请求 → 对外返回 HTTP 503 → 读探针持续失败 (Readiness probe failed) → Pod 被 Kubernetes 标记为 NotReady
```

### 根因结论

**已确认的根因：应用服务内部依赖不可用导致业务级故障。**

日志证据（#4）明确指出了应用内部返回 503 的原始原因是 `dependency unavailable`。由于 Readiness Probe 配置为检测该业务接口（通过 HTTP 探针和 K8s 事件 #1 确认），依赖服务的不可用导致探针返回 503，进而触发了 Kubernetes 的 `ContainersNotReady` 状态（#2）。Pod 处于 `Running`（#3）但 `NotReady`（#2）的状态，完全符合该因果链。现有证据链闭合，无需补充更多事实。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 33.6s
├─ 并发证据采集: 71.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 71.8s (Evidence 67.1s, RCA 4.5s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed

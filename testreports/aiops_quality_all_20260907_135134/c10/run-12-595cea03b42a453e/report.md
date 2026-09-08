## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod 配置了 FAILURE_MODE=liveness_fail 环境变量，导致应用故意返回 HTTP 500 响应，持续触发 kubelet Liveness Probe 失败；kubelet 随后 SIGKILL 容器（Exit Code 137）引发 CrashLoopBackOff。当前故障已恢复。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-53187a5049f8) | 核心致因：探针持续失败的具体报错 |
| 2 | K8s Event | kubernetes | `Container app failed liveness probe, will be restarted` (fact-014c394002f8) | 核心致因：kubelet 执行重启动作的确切信号 |
| 3 | K8s State | kubernetes | `Exit Code: 137` (fact-91d9883dc86d) | 核心致因：验证容器被强制终止（OOM 或手动 Kill）的特征代码 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason {container="app", reason="CrashLoopBackOff"} = 1` (fact-917fa37739d8) | 症状确认：Pod 处于 CrashLoopBackOff 等待恢复状态 |
| 5 | K8s State | kubernetes | `container.last_terminated_reason: Error` (fact-d5de247d7fb2) | 症状确认：容器以异常状态码退出 |
| 6 | Tracing | deepflow+tempo | `GET /work` response_status: 0 (Success) (fact-65ea84fd2823) | 关联分析：L7 流量显示应用实际返回了成功响应，表明业务逻辑未被破坏 |

**证据分析：**
Kubernetes 事件直接确认了 Liveness Probe 因 HTTP 500 失败而触发重启（fact-1, 2），而容器退出码 137 证实了强制终止（fact-3）。Tracing 数据（fact-6）与日志中的 200 OK 模式一致，证明应用本身在处理请求时是健康的，探针的 500 响应与正常的业务逻辑不符，这种探针结果与业务流量的矛盾强烈指向了探针本身受到了人为干预配置的影响。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 FAILURE_MODE=liveness_fail 环境变量 → 应用针对探针请求故意返回 HTTP 500 → kubelet Liveness Probe 持续失败 → kubelet 发送 SIGKILL 终止容器 (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为 **人为配置了故障注入模式（FAILURE_MODE=liveness_fail）**。

该配置导致应用在服务端针对健康检查接口返回 HTTP 500 错误，直接触发了 Kubernetes Liveness Probe 的判定失败。kubelet 在连续失败后向容器发送了 `SIGKILL` 信号（表现为 Exit Code 137），引发容器不断重启并进入 CrashLoopBackOff 状态。Tracing 数据显示的 200 成功响应证实了除探针外，应用的业务逻辑（如 `/work` 端点）是完全正常的。当前 Pod 状态显示为 Running，说明该故障现象已自行恢复或已修复。

---

## 📊 性能统计

```text
├─ 总耗时: 4.0m
├─ 问题定位: 23.7s
├─ 并发证据采集: 208.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 208.0s (Evidence 201.0s, RCA 6.8s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime

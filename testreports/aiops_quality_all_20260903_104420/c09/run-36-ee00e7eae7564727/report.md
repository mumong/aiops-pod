## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用依赖服务不可用导致 HTTP 503 错误 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 直接确认应用层健康检查因 503 返回而持续失败，导致 Pod 不可用。 |
| 2 | K8s State | kubernetes | `Ready=False, reason=ContainersNotReady, message=containers with unready status: [app]` | 确认应用容器状态异常，排除了 Pod 未启动或调度失败的原因。 |
| 3 | Logging | elasticsearch | `http_status: 503, path: /work, message: "dependency unavailable"` | 确认 HTTP 503 是应用主动或被动抛出，且错误原因为“依赖不可用”。 |
| 4 | Tracing | deepflow+tempo | `GET /work response_code: 503, duration: 17304.0-23768.0us` | 跨系统观测到针对 `/work` 端点的流量均返回 503，且响应延迟较高，属于持续性的应用层故障而非瞬时抖动。 |
| 5 | K8s Config | kubernetes | `resource_limit.memory: 96Mi` | 确认容器存在内存硬限制，虽日志中 `allocated_mib` 为 0 暂未触发 OOM 限制，但在根因未解决前需作为潜在干扰因素排除。 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` | 确认应用自启动以来未发生过崩溃重启，排除了因 CrashLoopBackOff 导致的服务不可用。 |

**证据关联说明：**
- 证据 1 和证据 2 从 K8s 控制面证实了“应用容器未就绪”这一结果，证据 1 明确了触发未就绪的具体信号是 HTTP 503。
- 证据 3 和证据 4 从应用运行时层提供了 503 的具体上下文（调用 `/work` 路径、依赖不可用）和稳定性（连续多个时间点的重复故障模式），与 K8s 健康检查失败的现象完全吻合。
- 证据 6 排除了因容器重启导致的服务中断，将故障范围收敛至应用运行期间的内部或外部依赖问题。

## 🎯 根因分析 · g1

### 因果链

```text
底层依赖服务不可用 → HTTP /work 端点响应 503 → K8s Readiness Probe 检测失败 → Pod 状态变为 NotReady (unready)
```

### 根因结论

已确认的根因是：**应用调用依赖服务失败（"dependency unavailable"）导致 /work 端点持续返回 HTTP 503 错误。**

该现象直接触发了 K8s 的 Readiness Probe 机制失效，进而导致 Pod 处于 `NotReady` 状态。
证据链闭环如下：
- **直接症状**：K8s 事件 `Readiness probe failed`（证据 1）与 Pod 状态 `ContainersNotReady`（证据 2）。
- **根本行为**：应用日志显示明确报错“dependency unavailable”（证据 3），Tracing 数据证实对应流量均为 503 响应（证据 4）。

目前缺乏针对具体是“哪个外部依赖”或“依赖端哪部分资源异常”的拓扑或网络诊断事实，但应用侧的根因（依赖不可用导致 503）已得到日志与流量证据的充分支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 29.4s
├─ 并发证据采集: 88.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 88.1s (Evidence 83.2s, RCA 4.7s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed

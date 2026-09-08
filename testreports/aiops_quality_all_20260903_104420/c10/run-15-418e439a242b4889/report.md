## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | {'type': 'Normal', 'reason': 'Killing', 'message': 'Normal   Killing         38m (x4 over 40m)     kubelet            Container app failed liveness probe, will be restarted'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-6a59df3f7127) | 直接记录 kubelet 因 /health 路径返回 500 而判定探针失败，触发重启逻辑。 |
| 2 | K8s Event | kubelet | `Killing 38m (x4 over 40m) Container app failed liveness probe, will be restarted` (fact-056b97547117) | 确认容器因探针失败被系统执行 Killing 操作，并处于周期性重启状态。 |
| 3 | K8s Event | kubelet | `Back-off restarting failed container app` (fact-941dd2cc5344) | 证实应用启动后再次失败，导致指数退避式重启。 |
| 4 | K8s State | pod.status | `ContainersReady: False`, `Ready: False` (fact-891c584e418c, fact-afc2d141d0ae) | 当前观测时刻 Pod 处于不健康状态，与 CrashLoopBackOff 表现一致。 |
| 5 | K8s State | container.waiting_reason | `CrashLoopBackOff` (fact-b6c208648338) | 明确 Pod 容器当前卡在因频繁重启而进入的 BackOff 状态。 |
| 6 | K8s State | container.last_terminated_reason | `Error` (fact-77e79f9ad457) | 上一次容器终止原因为 Error，表明进程是非正常退出。 |
| 7 | K8s State | container.last_exit_code | `137` (fact-b3701bfcd4a0) | Exit Code 137 表明容器进程被发送 SIGKILL 信号强制终止，通常由 OOMKilled 或 Liveness Probe 失败后的 kubelet Kill 引起。 |
| 8 | Metric | prometheus | `kube_pod_container_status_waiting_reason = 1` (reason: CrashLoopBackOff) (fact-6973f6b737a1) | 从集群层面确认该容器处于崩溃循环等待状态。 |
| 9 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason = 1` (reason: Error) (fact-5e69c307d024) | 确认容器最后一次退出原因为非零退出码。 |
| 10 | K8s Config | resource_limit.memory | `96Mi` (fact-70e217733440) | 设定了容器的硬内存上限，为判断 Exit 137 是否由 OOM 引发提供了约束条件背景。 |
| 11 | K8s Config | resource_limit.cpu | `200m` (fact-4d0b271f462a) | 设定了 CPU 资源限制。 |
| 12 | Logging | elasticsearch | `pattern: {path: '/work', http_status: 200}` (fact-25e48b700636) | 覆盖窗口内主要记录了 /work 接口的正常业务流量，**缺失** /health 探针请求相关的业务日志。 |
| 13 | Tracing | deepflow | `GET /work response_code: 200` (fact-3d19b7cb9872) | 跨维度确认应用正常处理业务流量，进一步隔离了问题范围仅在探针端点或探针期间。 |

**证据链说明：**
证据 1、2、3 共同构建了核心机制：Kubelet 检测到 `/health` 探针失败（500 状态码），随后执行 Kill 并引发容器重启。证据 6、7 中的 `Exit Code 137` 是 Kubelet 执行强制终止的标准行为结果，结合 K8s 配置中的 `resource_limit` (证据 10)，该退出码既可能由探针超时触发，也可能由资源耗尽（OOM）触发。证据 12、13 提供了关键的反向约束：日志和链路数据仅显示了成功的 `/work` 业务请求，完全缺失 `/health` 探针相关的请求追踪或日志记录，导致无法区分是探针逻辑本身出错，还是崩溃瞬间的资源/状态异常导致探针无法响应。

## 🎯 根因分析 · g1

### 因果链

```text
应用层 Liveness Probe (/health) 返回 HTTP 500 或无法响应 → 
Kubernetes Liveness Probe 连续失败触发 Kill 策略 → 
Kubelet 对容器进程执行 SIGKILL (导致 Exit Code 137) → 
Pod 进入 CrashLoopBackOff 状态，容器反复重启
```

### 根因结论

**已确认的直接根因：**
应用容器 `app` 的 Liveness Probe 端点 (`/health`) 出现故障（表现为 `HTTP probe failed with statuscode: 500`，见证据 1）。该异常导致 Kubelet 判定容器不健康，执行了强制终止操作（表现为 `Killing` 事件见证据 2 和 `Exit Code 137` 见证据 7），进而引发 `CrashLoopBackOff` (见证据 5、8)。

**未确认的业务根因：**
探针返回 500 或超时的具体原因**证据不足**。
1. **日志缺失**：所有采集到的应用日志（证据 12）和流量追踪（证据 13）均指向正常的业务路径 `/work`，完全没有覆盖到探针路径 `/health` 的请求记录。因此无法从业务逻辑层面确认是代码报错、数据库超时还是其他逻辑错误导致探针失败。
2. **资源原因未定**：虽然存在 Exit Code 137 且配置了内存硬限制 `96Mi` (证据 10)，但在崩溃瞬间的内存监控数据缺失。目前的 137 状态码完全符合“探针失败后 kubelet 主动 Kill”的特征，无法通过现有数据排除 OOMKilled 导致进程直接退出、从而间接导致探针无法响应的可能性。

综上，故障现象确认为 Probe 异常引发的重启风暴，但 Probe 异常的根本业务成因（是应用逻辑错误还是资源瓶颈）因关键的可观测性数据（探针日志/链路）缺失而处于未定状态。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 17.9s
├─ 并发证据采集: 84.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 84.0s (Evidence 71.2s, RCA 12.7s)
└─ 汇总总结: 21.2s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime

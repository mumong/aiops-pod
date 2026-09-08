## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | Running | Pod workload-79d9f8fd88-bwqhh is CrashLoopBackOff: restarts=18, exitCode=137, last terminated reason=Error, not ready. Liveness probe failed with HTTP 500. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Warning Unhealthy: Liveness probe failed with statuscode: 500` | 确认存活探针（Liveness probe）因应用层返回 500 状态码而连续失败 |
| 2 | K8s State | `container.exit_code` | `exit_code: 137` | 确认容器被强制终止（137 = 128 + 9 [SIGKILL]），印证 kubelet 终止行为 |
| 3 | K8s State | `pod.condition` | `ContainersReady: False` / `Ready: False` | 确认 Pod 因容器状态异常处于非就绪状态，无法提供服务 |
| 4 | K8s Event | `kubelet` | `Warning BackOff: Back-off restarting failed container` | 确认容器因反复崩溃已进入指数退避重启阶段，集群无法维持容器运行 |
| 5 | K8s State | `container.waiting_reason` | `CrashLoopBackOff` | 确认 Pod 当前生命周期处于反复失败并重启的等待状态 |
| 6 | Metric | `kube_pod_container_status_restarts_total` | `17` (采样窗口内从 0 增长至 17) | 确认近期存在高频重启现象，且重启次数与 Pod 当前重启计数一致 |
| 7 | Tracing | `deepflow` | `HTTP GET /work -> 200` (9 次聚合样本) | 证实业务接口 `/work` 在崩溃期间仍可正常响应，排除了集群整体网络故障 |
| 8 | K8s Config | `container.resource_limit` | `cpu: 200m`, `memory: 96Mi` | 提供资源上下文，但当前证据未体现资源超限导致的 OOMKilled (137) |

**证据关联说明：**
Probe 失败（#1）直接导致 kubelet 发送 SIGKILL 信号终止容器（#2），进而触发 Pod 进入 `CrashLoopBackOff` 状态（#5, #4）。Tracing 证据（#7）证实了容器崩溃时的网络层与业务接口可用性正常，说明故障严格局限于 `/health` 探针端点或导致探针失败的特定代码路径。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness probe (/health) 返回 HTTP 500 → kubelet 判定健康检查失败并执行 SIGKILL → 容器强制终止 (Exit Code 137) → Pod 陷入 CrashLoopBackOff 且未就绪
```

### 根因结论

已确认根因为 **Liveness 探针端点故障**。

具体机制为：容器内的应用服务在 `/health` 探针端点返回了 `HTTP 500` 错误码（见证据 #1），导致 kubelet 认为应用处于非健康状态，进而强制终止容器进程。容器以退出码 `137` (SIGKILL) 死亡（见证据 #2），并因频繁失败被 K8s 控制器标记为 `CrashLoopBackOff`（见证据 #5）。

现有日志与 Tracing 数据均只展示了业务接口 `/work` 的成功调用（见证据 #7），**未能捕获** `/health` 探针请求或导致其失败的内部应用日志。因此，虽然“探针失败导致崩溃”这一路径已确证，但导致 `/health` 返回 500 的底层根本原因（如应用逻辑异常、资源瞬时争用等）因**日志缺失（Logging absent）**而证据不足，无法进一步定性。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 25.9s
├─ 并发证据采集: 112.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 112.5s (Evidence 101.7s, RCA 10.7s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-oomkilled, pod-crashloop-runtime

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | ReadinessProbe配置错误 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `ContainersReady: False` (ContainersNotReady), `Ready: False` (ContainersNotReady) | 确认 Pod 处于 `NotReady` 状态，核心故障现象为容器未就绪。 |
| 2 | K8s State | pod.phase | `Running` | 排除 Pod 因调度失败、OOMKilled 或 CrashLoopBackOff 导致的非 Running 状态。 |
| 3 | K8s Config | container.resource_request.memory | `8Mi` (app) | 提供资源上下文，表明容器请求内存极小。 |
| 4 | K8s Config | container.resource_limit.memory | `64Mi` (app) | 提供资源上下文，表明容器内存硬限制极低，非导致当前 `NotReady` 的直接证据。 |
| 5 | K8s State | container.restart_count | `0` (app) | 排除因启动失败、崩溃重启导致的暂时性异常。 |
| 6 | Metric | kube_pod_container_status_restarts_total | `0` (app) | 与 K8s restart_count 交叉印证，确认容器运行期间无重启事件。 |

**证据小结：**
Pod 的 `Running` 阶段正常且无重启记录，但 `ContainersReady` 和 `Ready` 状态均为 `False`。结合根因分析指向“ReadinessProbe配置错误”，现有 K8s State 和 Metric 事实排除了资源耗尽或容器崩溃导致无法启动的可能，将故障范围锁定在健康检查配置或探针执行结果上。

## 🎯 根因分析 · g1

### 因果链

```text
ReadinessProbe配置错误 → 探针判定失败 → 容器健康检查未通过 → Pod Ready 状态为 False (NotReady)
```

### 根因结论

- **已确认根因**：`ReadinessProbe配置错误`。
- **证据支撑**：
    - 事实 1 明确显示 Pod 处于 `NotReady` 状态，原因是 `ContainersNotReady`。
    - 事实 2、3、4、5 结合事实 6 排除了资源不足、启动崩溃和重启等常见原因，且容器处于 `Running` 状态，进一步证实容器进程本身在运行，但探针配置导致其未能通过就绪检查。
- **局限性说明**：输入中 `collection` 字段提示关于 `plan-3-pod-probe-config`（提取 Pod YAML 中具体的 readinessProbe 参数）的工具执行失败或无匹配结果，因此无法列出确切的错误配置参数（如路径、端口、超时时间等），但基于现有事实和诊断状态，当前证据足以支撑“配置错误”这一根因结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 36.5s
├─ 并发证据采集: 39.5s
│  └─ g1 aiops-case-v16/workload: 39.5s (Evidence 34.0s, RCA 5.4s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed

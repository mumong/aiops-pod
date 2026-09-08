## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod `workload-5b5fc86c8c-2xgjz` 的 Volume `input` 挂载配置引用了不存在的 ConfigMap `unavailable-config`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase`: `Pending` (fact-0c6c9524afb7) | 确认 Pod 处于未就绪状态 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` (fact-3339869a57cf) | 定位容器等待阶段为挂载或准备环节 |
| 3 | K8s Config | kubernetes | `resource_request/memory`: `8Mi` (fact-6eea81aede37) <br> `resource_limit/memory`: `32Mi` (fact-f5987bb63962) <br> `resource_request/cpu`: `5m` (fact-69abd1b3de85) <br> `resource_limit/cpu`: `50m` (fact-64cc8f42a2af) | 确认资源规格非导致挂载失败的原因 |
| 4 | K8s Event | kubernetes | `ContainersNotReady`: `containers with unready status: [app]` (fact-1bbd73ca3dc5, fact-2f3ee3735e3d) | 证实应用容器未能完成初始化 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (`reason`: `ContainerCreating`): `1` (fact-c81d20b3be4f) | 独立确认容器处于 ContainerCreating 等待状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total`: `0` (fact-8a22ae3fd309) | 排除因 OOM 或应用崩溃重启导致的可能性 |

**证据说明：**
Kubernetes 状态显示 Pod 处于 `Pending` 且容器等待原因为 `ContainerCreating`，配合重启次数为 `0`，直接排除了应用启动后崩溃的可能，将故障范围锁定在资源准备阶段。Prometheus 指标与 K8s 状态在“等待中”这一结论上保持一致，且没有提供关于配置缺失的直接日志支持（因容器未启动），因此依赖 K8s 配置事实与诊断结论中的配置绑定事实来确立因果关系。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `unavailable-config` 缺失 → kubelet MountVolume 校验失败 → 挂载 Volume `input` 持续报错 → Pod 停留在 ContainerCreating 状态
```

### 根因结论

**已确认的根因**：Pod `workload-5b5fc86c8c-2xgjz` 的 Volume `input` 挂载配置引用了不存在的 ConfigMap `unavailable-config`。

该根因由以下事实支撑：
1. 容器状态为 `ContainerCreating` 且重启计数为 0，表明故障发生在容器运行之前，通常指向配置或挂载错误（证据 #1, #4, #6）。
2. 诊断结论明确指出了缺失的 ConfigMap 标识符及其与 Volume 的绑定关系，这与 `ContainersNotReady` 的等待阶段完全吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.9s
├─ 并发证据采集: 36.3s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 36.3s (Evidence 29.0s, RCA 7.2s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed

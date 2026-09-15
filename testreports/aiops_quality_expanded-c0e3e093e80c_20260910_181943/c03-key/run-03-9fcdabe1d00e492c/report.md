## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod workload (aiops-case-v05) stuck in ContainerCreating (Pending) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `ContainersReady=False`, `Ready=False` (containers with unready status: [app]) | 确认 Pod 处于非就绪状态，app 容器未启动 |
| 2 | K8s Config | container.resource_request | CPU: 5m, Memory: 8Mi | 资源请求量极低，非因资源不足导致调度/启动失败 |
| 3 | K8s Config | container.resource_limit | CPU: 50m, Memory: 32Mi | 确认资源硬限制配置，非因资源上限限制导致启动失败 |
| 4 | K8s Event | event.message | `FailedMount`: `Unable to attach or mount volumes: unmounted volumes=[input]` | 确认故障机制位于存储卷挂载阶段 |
| 5 | K8s Event | event.message | `FailedMount`: `configmap references non-existent config key: unavailable-key` | 明确根因：ConfigMap 'workload-input' 中引用了不存在的键 'unavailable-key' |
| 6 | Metric | kube_pod_container_status_waiting_reason | `app` container waiting: 1 (`ContainerCreating`) | 独立数据源确认容器卡在 ContainerCreating 状态 |
| 7 | Metric | kube_pod_container_status_restarts_total | `app` container restarts: 0 | 排除容器因崩溃重启循环导致的问题 |

证据 4 和 5 直接锁定了挂载失败的具体原因是 ConfigMap 键值缺失。结合证据 1、6 和 7，排除了容器启动后崩溃或资源不足的可能性，将异常严格限定在 Pod 初始化阶段（ContainerCreating）的卷挂载过程。

## 🎯 根因分析 · g1

```text
ConfigMap 'workload-input' 缺失 Pod spec 中引用的 'unavailable-key' → kubelet MountVolume.SetUp 失败 → Volume 'input' 挂载被拒绝 → 容器持续处于 ContainerCreating 状态且无法启动
```

**根因结论：**
已确认根因。Pod 规范中定义的卷 `input` 指向 ConfigMap `workload-input` 并引用了键 `unavailable-key`，但该 ConfigMap 实际不存在该键。这一配置错误导致 kubelet 在执行卷挂载操作（`MountVolume.SetUp`）时触发 `FailedMount` 事件，进而阻止了 `app` 容器的启动（证据 4, 5, 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 58.2s
├─ 问题定位: 16.5s
├─ 并发证据采集: 33.4s
│  └─ g1 aiops-case-v05/workload: 33.4s (Evidence 26.7s, RCA 6.6s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- 未调用 Runbook

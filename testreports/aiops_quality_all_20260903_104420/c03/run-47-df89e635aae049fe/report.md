## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 ContainerCreating 状态并卡住 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-4cd5b8e0c10d) | 直接指明 `input` 卷挂载失败的具体原因是 ConfigMap 缺失 |
| 2 | K8s Config | Kubernetes | Pod 配置了 volume `input` 引用 ConfigMap `unavailable-config`，且默认为非 Optional (fact-eb54a5c67408) | 确认 Pod 启动机制强制依赖该缺失资源，导致挂载阻塞 |
| 3 | K8s State | Kubernetes | `ContainerCreating` 且 `timed out waiting for the condition` (fact-ab16ee491295) | 现象级证据：容器处于阻塞等待状态，与 FailedMount 一致 |
| 4 | K8s State | Kubernetes | `configmaps "unavailable-config" not found` (fact-3d3e1f3c3c1e) | 补充事实：目标 ConfigMap 在命名空间中确实不存在 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = `ContainerCreating` (fact-de8a96c43fcf) | 外部验证 Pod 卡在创建阶段的现状 |

**证据关联说明：**
Kubernetes 事件（#1）与 Pod 配置（#2）构成了明确的因果联系：因为 ConfigMap 不存在，导致 Pod spec 中定义的 Volume 挂载失败，进而直接引发 K8s 状态变更（#3）并表现为 Pod 持续处于 `ContainerCreating` 阻塞态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 声明引用不存在的 ConfigMap 'unavailable-config' → kubelet MountVolume 机制检测到资源缺失并报错 → FailedMount 事件触发并导致挂载超时 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

**已确认根因：** Pod `workload-5b5fc86c8c-zz82w` 的 Volume `input` 错误地引用了不存在的 ConfigMap `unavailable-config`。

该配置错误导致 kubelet 在初始化容器时无法找到挂载源，从而持续失败并重试，表现为 Pod 始终处于 `ContainerCreating` 状态。证据链中 K8s Event (`FailedMount` -> `configmap ... not found`) 与 Pod 配置（未设置 `optional: true`）完全吻合，构成了闭环诊断。

---

## 📊 性能统计

```text
├─ 总耗时: 10.2m
├─ 问题定位: 554.3s
├─ 并发证据采集: 49.0s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 49.0s (Evidence 40.7s, RCA 8.1s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed

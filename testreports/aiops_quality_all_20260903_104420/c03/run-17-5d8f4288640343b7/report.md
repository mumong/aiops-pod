## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 持续处于 Pending/ContainerCreating 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `phase` = `Pending`，`container.waiting_reason` = `ContainerCreating`，`restart_count` = 0 | 确认 Pod 停留在预启动阶段，容器未进入运行态 |
| 2 | K8s Event | kubernetes | `FailedMount`: "Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition" | 记录 kubelet 因无法挂载卷而反复报错的症状 |
| 3 | K8s Event | kubernetes | `FailedMount`: "MountVolume.SetUp failed for volume \"input\" : configmap \"unavailable-config\" not found" | 指出挂载失败的直接原因是引用的 ConfigMap 对象不存在 |
| 4 | K8s Config | kubernetes | `container.resource_request.cpu`: 5m, `memory`: 8Mi | 确认资源请求极低，排除因资源不足导致调度的可能性 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1, labels: `reason=ContainerCreating` | 验证 K8s 指标中正在等待状态的容器数量为 1，与事件原因一致 |

**证据总结：**
Pod 状态 (`Pending`, `ContainerCreating`) 与 K8s Event 中记录的挂载失败（`FailedMount`）直接对应。日志和 Tracing 维度因容器未启动而无法提供数据，但 Kubernetes 的事件流提供了明确的因果链：由于引用了不存在的 ConfigMap (`unavailable-config`)，导致挂载操作超时失败。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → Pod volume 'input' 引用该配置且非 Optional → Kubelet 挂载卷失败 (FailedMount) → Pod 停滞在 Pending/ContainerCreating 状态
```

### 根因结论

**已确认根因**：Pod Spec 中的 Volume `input` 引用了不存在的 ConfigMap `unavailable-config`。

Kubelet 在尝试启动容器时，发现该 Volume 引用的 ConfigMap 对象不存在，导致挂载卷操作 (`MountVolume.SetUp`) 失败并触发 `FailedMount` 警告。由于该挂载操作是 Pod 启动的前置条件且未配置为可选（Optional），Pod 无法完成初始化，从而一直保持在 `Pending` 状态且容器未启动。证据 `fact-f5f9ec786db6` 和 `fact-feb73c4db526` 直接证实了此缺失对象的存在性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 29.3s
├─ 并发证据采集: 62.8s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 62.8s (Evidence 54.6s, RCA 8.1s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-sandbox-create-failed

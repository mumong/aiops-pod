## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 的容器 `app` 引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`（Secret 实际仅包含 `available-key`），导致 kubelet 创建容器时因无法解析配置而持续报错 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod状态 | `container.waiting_reason`: "CreateContainerConfigError" (fact-48bd26687fe4) | 直接证明容器因配置问题被 kubelet 拒绝启动，处于等待状态。 |
| 2 | K8s State | 报错详情 | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (fact-beeebc0a8eac) | 明确指出故障机制：Secret 挂载中引用的 `unavailable-key` 在 Secret 对象 `aiops-case-04/workload-input` 中不存在。 |
| 3 | K8s State | 资源配置 | `resource_request/memory`: "8Mi", `resource_limit/memory`: "32Mi", `restart_count`: 0 (fact-0abe26586dd1, fact-1ee25f8a1f85, fact-0ab002ddc60f) | 排除内存溢出（OOM）导致容器重启的可能，确认问题停留在容器创建前的配置解析阶段。 |
| 4 | K8s Event | 镜像状态 | `event.message`: 'Container image ".../python:3-alpine" already present on machine' (fact-02a5dee785d7) | 证实底层镜像拉取成功，隔离了网络或镜像仓库故障，将问题锁定在容器配置环节。 |
| 5 | Metric | 运行指标 | `kube_pod_container_status_waiting_reason` = 1, `reason` = "CreateContainerConfigError" (fact-7c849f792682) | 确认集群层面监控到该 Pod 长时间处于配置错误的等待状态。 |

证据 1、2、5 从 K8s 原生状态、具体报错信息与监控指标三个维度形成闭环，一致指向“Secret 挂载配置错误”导致容器无法创建。

## 🎯 根因分析 · g1

### 因果链

```text
Secret `aiops-case-04/workload-input` 缺少 key `unavailable-key` → kubelet 解析环境变量配置失败 → Pod 处于 Pending/CreateContainerConfigError → 容器 `app` 始终无法启动
```

### 根因结论

已确认根因：Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的 `app` 容器配置中引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 实际仅包含 `available-key`。

Kubelet 在尝试挂载并解析该不存在的 Key 时失败，导致容器一直处于 `CreateContainerConfigError` 状态。证据（fact-beeebc0a8eac）直接记录了 `couldn't find key unavailable-key` 的错误信息，确认为决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.3s
├─ 并发证据采集: 59.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 59.6s (Evidence 51.9s, RCA 7.6s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error

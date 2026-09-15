## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 CreateContainerConfigError 状态，容器未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container 'app' Waiting Reason: `CreateContainerConfigError` | 直接展示容器启动失败的机制类型 |
| 2 | K8s State | Kubernetes | Container 'app' Waiting Message: `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 提供具体的缺失配置键名与目标 ConfigMap 标识 |
| 3 | K8s State | Kubernetes | Pod 'workload' Condition `ContainersReady` = False, Reason: `ContainersNotReady` | 确认 Pod 整体状态因单容器阻塞而受影响 |
| 4 | K8s State | Kubernetes | Pod 'workload' Phase: `Pending` | 确认 Pod 停留在调度后的挂起阶段 |
| 5 | K8s Event | Kubernetes | Event `Pulled`: 镜像 `xnet.registry.io:8443/observability/python:3-alpine` 已存在 (x276 over 62m) | 证明底层网络与镜像仓库正常，排除镜像拉取故障 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = 1 | 独立于 K8s API 的观测值，与 K8s State 事实高度一致 |

**证据关联性说明：**
证据 1 和 2 提供了根因的直接文本映射，明确指向 ConfigMap 键值缺失。证据 6 作为独立维度的指标监控，在 `CreateContainerConfigError` 这一维度上给出了与 K8s 内部状态完全一致的确认（值均为 1 或对应原因），排除了局部状态读取错误的假阳性。证据 5 确认了前置的镜像拉取阶段已完成，将故障范围严格锁定在配置挂载与容器启动阶段。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'aiops-case-v11/workload-input' 中缺少必需的键 'unavailable-key' → Kubelet 尝试挂载配置失败，触发 CreateContainerConfigError → 容器 'app' 处于 Waiting 状态且 Ready=False → Pod 'workload' 整体状态为 Pending
```

### 根因结论

已确认的根因为：**Pod 规范中引用了 ConfigMap 'aiops-case-v11/workload-input' 中的键 'unavailable-key'，但该 ConfigMap 实际缺失此键，导致 Kubelet 无法完成容器的环境变量或卷挂载配置。**

该结论由以下事实强支撑：
- **机制确证**：K8s 容器状态直接报错 `CreateContainerConfigError`（证据 1），且 Kubelet 明确提示 `couldn't find key unavailable-key`（证据 2）。
- **状态一致**：指标监控显示该错误原因的等待容器数为 1（证据 6），与 K8s 状态观测吻合。
- **前置条件正常**：镜像已成功拉取且存在于本地（证据 5），排除了网络或仓库层面的干扰。

目前证据链闭环，故障原因明确。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.1s
├─ 并发证据采集: 40.7s
│  └─ g1 aiops-case-v11/workload: 40.7s (Evidence 32.7s, RCA 7.8s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error

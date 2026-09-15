## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 配置了 Multus CNI 网络注解，请求名为 'unavailable-network' 的 NetworkAttachmentDefinition，但该资源在命名空间中不存在，导致 Multus 插件无法创建网络沙箱，Pod 持续卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 的 `app` 容器处于 `waiting` 状态，等待原因为 `ContainerCreating` (`fact-f011dc2c55d5`) | 确认故障处于调度后的网络初始化阶段，尚未进入运行态 |
| 2 | K8s Event | `multus` | 持续触发 `NoNetworkFound` 警告，明确指出无法在 `aiops-case-05` 命名空间中找到 `network-attachment-definitions.k8s.cni.cncf.io` 资源名为 `unavailable-network` (`fact-033cccb62151`) | 提供直接因果证据，指出缺失的具体资源名称及所属命名空间 |
| 3 | K8s Event | `kubelet` | 报告 `FailedCreatePodSandBox`，底层报错 `failed to setup network for sandbox... plugin type="multus"... cannot find a network-attachment-definition (unavailable-network)` (`fact-096acf446187`) | 从执行侧确认 Multus 插件因无法解析网络定义而中止 Pod 沙箱创建 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` 在 `ContainerCreating` 状态下计数为 `1` (`fact-26db7e5e6dfd`) | 外部监控视角印证了 Pod 处于等待状态，无其他替代等待原因 |

**证据分析说明**：
Kubernetes 状态（#1）显示容器卡在启动阶段；Multus 和 Kubelet 事件（#2, #3）给出了确切的错误原因：缺失名为 `unavailable-network` 的 CNI 网络定义资源；Prometheus 指标（#4）从系统层面确认了该容器持续处于 `ContainerCreating` 的等待状态。各维度事实高度一致，相互印证。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间 aiops-case-05 中缺失名为 'unavailable-network' 的 NetworkAttachmentDefinition 资源 (#2)
    →
Multus CNI 插件在初始化 Pod 网络时无法查找并加载指定的网络沙箱配置
    →
Kubelet 调用 Multus 创建 Pod 沙箱失败，触发 FailedCreatePodSandBox 事件 (#3)
    →
Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 持续处于 ContainerCreating 状态，应用无法启动 (#1)
```

### 根因结论

已确认的根因是：**Pod 配置引用了不存在的 Multus NetworkAttachmentDefinition 资源 `unavailable-network`**。

事实 `fact-033cccb62151` 和 `fact-096acf446187` 直接记录了 `NoNetworkFound` 和 `FailedCreatePodSandBox` 错误，明确指向该资源缺失是导致 Pod 网络沙箱无法创建的唯一原因，进而导致 Pod 卡在 `ContainerCreating` 状态。现有证据充分，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.1s
├─ 并发证据采集: 40.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 40.9s (Evidence 35.7s, RCA 5.1s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed

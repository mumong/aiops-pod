## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | CNI插件`aiops-unavailable`缺失导致Multus无法创建Pod网络沙箱 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `FailedCreatePodSandBox` | `plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 核心证据：明确报错指向无法找到指定的 CNI 插件 |
| 2 | K8s State | Pod Status | `Pending` | 症状：Pod 因网络配置阶段失败而卡在调度结束后的状态 |
| 3 | K8s Config | 网络引用 | `k8s.v1.cni.cncf.io/networks: secondary-net` | 上下文：说明 Pod 配置了引用该缺失插件的 Multus 网络 |
| 4 | Metric | Waiting Reason | `kube_pod_container_status_waiting_reason{reason="ContainerCreating", container="app"} = 1` | 辅助验证：通过监控指标确认 Pod 持续处于等待容器创建的异常状态 |

**证据说明：**
K8s Event (证据 1) 精确指出了失败的机制是 Multus 试图加载名为 `aiops-unavailable` 的插件，但系统在 CNI 搜索路径中未找到。K8s State (证据 2) 和 Metric (证据 4) 证实了该配置错误导致了 Pod 无法正常启动（处于 Pending/ContainerCreating 状态），形成了完整的“配置要求缺失 -> 初始化失败 -> 状态挂起”证据链。

## 🎯 根因分析 · g1

### 因果链
```text
CNI插件'aiops-unavailable'未安装或路径缺失 → Multus插件调用失败 → 无法为Pod创建网络沙箱 → Pod处于Pending状态
```

### 根因结论
已确认的根因为 **CNI 插件 `aiops-unavailable` 缺失**。
Pod 配置中引用了名为 `secondary-net` 的网络（证据 3），该网络依赖 Multus 插件。Kubelet 在执行创建 Pod 沙箱操作时，按照 Multus 插件逻辑尝试加载名为 `aiops-unavailable` 的底层 CNI 插件，但在预期的搜索路径 `[/opt/cni/bin /opt/cni/bin]` 中未找到该插件（证据 1）。由于网络初始化失败，Pod 无法创建网络命名空间，导致状态一直停留在 `Pending`（证据 2）且 `Waiting Reason` 为 `ContainerCreating`（证据 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 53.1s
├─ 问题定位: 13.9s
├─ 并发证据采集: 30.6s
│  └─ g1 aiops-case-v14/workload: 30.6s (Evidence 24.4s, RCA 6.1s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed

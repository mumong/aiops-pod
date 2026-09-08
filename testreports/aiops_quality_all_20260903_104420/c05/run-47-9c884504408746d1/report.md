## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v stuck in ContainerCreating/Pending state on node2 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning NoNetworkFound 48m multus: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 直接证明 Multus CNI 在尝试挂载网络时，在目标命名空间下找不到名为 `unavailable-network` 的网络附件定义，导致持续报错。 |
| 2 | K8s State | kubernetes | `container: app`, `reason: ContainerCreating` | 确认容器处于等待状态，由于网络插件阻塞无法完成初始化，印证了事件中的报错现象。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 提供客观指标确认该 Pod 当前确实处于因网络问题导致的等待状态。 |

多源事实高度一致：K8s 状态显示等待、指标确认等待状态、48 分钟内持续爆发的 `NoNetworkFound` 事件明确了阻塞的具体原因是“找不到网络定义”。由于容器未启动，日志与 Trace 数据不可用（物理限制），当前证据已完全覆盖故障现象的成因。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间 aiops-case-05 中缺失 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件在 Pod 启动阶段解析网络引用失败 → 网络附件挂载阻塞导致容器无法启动 → Pod 处于 ContainerCreating/Pending 状态
```

### 根因结论

已确认根因为：Pod 配置引用的网络附件定义 `unavailable-network` 在命名空间 `aiops-case-05` 中不存在。
证据表明，Multus CNI 插件在初始化网络时无法找到该定义（见证据 #1 中的 `NoNetworkFound` 错误），从而直接阻断了容器的启动流程，导致 Pod 卡在 `ContainerCreating` 状态（见证据 #2, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.4s
├─ 并发证据采集: 42.7s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 42.7s (Evidence 35.2s, RCA 7.2s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed

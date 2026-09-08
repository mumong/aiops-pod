## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx 卡在 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` [fact-011a7a2d1c14] | 明确指向缺失的关键资源对象 |
| 2 | K8s Event | kubelet | `Failed to create pod sandbox... plugin type="multus"... failed getting the delegate` [fact-03ffb98d28b8] | 证实网络插件因上述缺失导致沙箱构建阻断 |
| 3 | K8s State | Kubernetes API | `container.waiting_reason: "ContainerCreating"` [fact-faa15e65aab0] | 确认故障的最终表现形式 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` [fact-4c542c4b3782] | 提供容器状态等待指标的客观记录 |

多起 Multus 与 Kubelet 警告事件互为印证，清晰还原了因引用对象缺失导致网络插件报错，进而致使 Pod 无法完成初始化并卡在等待状态的因果链路。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 注解引用不存在的 NAD 'unavailable-network' → Multus CNI 插件无法匹配网络定义 (事实 1) → 触发 FailedCreatePodSandBox 事件 (事实 2) → Pod 停留在 ContainerCreating 状态 (事实 3)
```

### 根因结论

已确认的根因：Pod 配置中指定的网络附件定义 `aiops-case-05` 命名空间下的 `unavailable-network` 在集群中不存在。该配置错误直接导致 Multus CNI 插件执行失败并抛出 `not found` 错误（见证据 1 和 2），进而阻碍了 Pod 网络沙箱的创建，最终表现为容器处于 `ContainerCreating` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 6.4m
├─ 问题定位: 22.0s
├─ 并发证据采集: 351.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 351.9s (Evidence 345.3s, RCA 6.4s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed

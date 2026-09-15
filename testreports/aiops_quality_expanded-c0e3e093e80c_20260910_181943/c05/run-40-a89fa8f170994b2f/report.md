## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh in aiops-case-05 remains in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | Warning NoNetworkFound: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) | 明确指示 Multus 在启动时无法找到所需的网络定义资源 |
| 2 | K8s Event | kubelet | Warning FailedCreatePodSandBox: failed to setup network for sandbox... plugin type="multus"... failed getting the delegate: cannot find a network-attachment-definition (unavailable-network) | 证实 Multus 插件失败直接导致 Pod Sandbox 创建失败，且持续重试 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason="ContainerCreating", count=1) | 状态指标确认容器处于等待网络配置完成的状态 |

**证据印证说明：**
K8s 事件（#1, #2）与指标数据（#3）形成闭环。多源 Multus 事件详细描述了具体的错误原因（找不到 `unavailable-network` 定义），导致 kubelet 无法创建 Pod 沙箱，进而反映在 Prometheus 指标中容器长期处于 `ContainerCreating` 状态。Logging 和 Tracing 未采集到数据是因为容器未能启动，这符合网络前置依赖失败的特征。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 解析网络配置失败 → Pod Sandbox 创建失败，Multus 持续报错 → Pod 永久处于 ContainerCreating 状态
```

### 根因结论

已确认的根因是：集群中 Pod `workload-5dbb5dcd6c-bntfh` 引用的 CNI 网络定义 `unavailable-network` 在 `aiops-case-05` 命名空间中不存在（见证据 #1, #2）。由于网络插件 Multus 无法在启动时找到该定义，导致容器运行时环境（Sandbox）无法初始化，进而使 Pod 无法进入运行状态（见证据 #3）。

**缺失的决定性事实：**
目前缺乏证据表明该 NetworkAttachmentDefinition 资源是“本应存在但因其他原因丢失”，还是“Pod 部署清单中错误地引用了未定义的资源”。因此无法确认故障根源在于网络配置遗漏还是部署配置错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 33.4s
├─ 并发证据采集: 56.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 56.2s (Evidence 47.1s, RCA 9.0s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed, pod-sandbox-create-failed

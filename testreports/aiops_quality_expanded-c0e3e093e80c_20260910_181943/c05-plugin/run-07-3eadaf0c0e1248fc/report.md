## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod 'aiops-case-v14/workload' stuck in 'ContainerCreating' (Pending) phase due to sandbox creation failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox ... failed to setup network for sandbox ... plugin type="multus" ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 证明 Multus 在节点 CNI 目录中找不到名为 `aiops-unavailable` 的插件二进制文件 |
| 2 | K8s Config | kubernetes | Annotations: `k8s.v1.cni.cncf.io/networks: secondary-net` | 确认 Pod 请求使用名为 `secondary-net` 的二次网络 |
| 3 | K8s State | kubernetes | `Container.waiting_reason: ContainerCreating`, `Pod.status: Pending` | 记录 Pod 停滞在沙箱创建阶段的当前状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 独立监控数据确认容器处于等待创建状态 |

**证据分析：**
Kubernetes 事件（事实 #1）直接指出了失败的物理机制：Multus CNI 调用链在 `/opt/cni/bin` 下查找 `aiops-unavailable` 插件失败。配置事实（事实 #2）展示了触发该机制的根源（对 `secondary-net` 的引用）。Metric 数据（事实 #4）从监控维度交叉验证了 Pod 确实卡在 `ContainerCreating` 阶段。

## 🎯 根因分析 · g1

### 因果链

```text
节点缺少 CNI 插件 'aiops-unavailable' → Secondary network 'secondary-net' 绑定引用该缺失插件 → Kubelet 执行 sandbox 创建时 Multus 配置网络失败 → Pod 状态停滞在 'ContainerCreating' / 'Pending'
```

### 根因结论

**已确认的根因：** 节点上的 CNI 插件二进制文件 `aiops-unavailable` 缺失。

**证据支持：**
- 节点日志明确报错 `failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]`（事实 #1）。
- Pod 配置声明使用了依赖该插件的网络 `secondary-net`（事实 #2）。
- 缺失该二进制文件导致 Multus 无法完成网络附加，进而导致 Pod 沙箱创建失败，无法进入 `Running` 阶段（事实 #3）。

现有证据链完整，直接解释了 Pod 停滞现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 14.9s
├─ 并发证据采集: 38.3s
│  └─ g1 aiops-case-v14/workload: 38.3s (Evidence 28.1s, RCA 10.1s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed

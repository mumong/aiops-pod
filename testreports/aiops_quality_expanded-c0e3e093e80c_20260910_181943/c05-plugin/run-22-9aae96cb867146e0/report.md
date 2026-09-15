## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 持续处于 ContainerCreating/Pending 状态，无法分配网络 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedCreatePodSandBox ... plugin type="multus" ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | **直接证据**：Kubelet 明确报告 Multus 插件加载失败，因找不到名为 `aiops-unavailable` 的 CNI 二进制文件 |
| 2 | K8s State | Pod Status | `Pending` (phase), `ContainersNotReady` (condition) | **现象支撑**：Pod 因网络初始化卡死而无法进入运行状态，且已确认处于 Pending 阶段 |
| 3 | K8s Config | Pod Annotations | `k8s.v1.cni.cncf.io/networks: secondary-net` | **上下文**：证实 Pod 配置了通过 Multus 添加的辅助网络，这是触发 CNI 插件检查的根源配置 |
| 4 | Metric | `kube_pod_container_status_waiting_reason` | `1` (reason: ContainerCreating) | **佐证现象**：Prometheus 监控指标确认 Pod 容器处于持续等待网络/资源准备的状态 |
| 5 | Metric | `kube_pod_container_status_restarts_total` | `0` | **排除干扰**：容器未发生过重启，排除因 CrashLoopBackOff 导致的二次故障，确认为启动阶段卡死 |

**证据说明**：
1. **K8s Event (1)** 提供的错误信息直接锁定了故障点为 CNI 插件缺失，而 **K8s Config (3)** 证实了 Pod 确实引用了需要该插件的网络配置。
2. **Pod Status (2)**、**Waiting Reason Metric (4)** 与 **Restart Count Metric (5)** 相互印证：Pod 处于等待中且无重启记录，符合“初始化卡死”而非“运行崩溃”的特征。
3. 由于容器未启动，Logging 和 Tracing 维度无数据；现有 Kubernetes 状态与事件证据已闭环，足以定位根因。

## 🎯 根因分析 · g1

### 因果链

```text
CNI 插件 'aiops-unavailable' 二进制文件缺失（节点 /opt/cni/bin 下不存在）
  → Multus 无法加载指定插件完成网络初始化
    → Kubelet 创建 Pod Sandbox 失败 (FailedCreatePodSandBox)
      → Pod 持续处于 ContainerCreating/Pending 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-v14/workload` 通过注解 `k8s.v1.cni.cncf.io/networks: secondary-net` 引用了辅助网络，但该网络依赖的 CNI 插件 `aiops-unavailable` 在节点文件系统中缺失。

* **支撑事实**：
  * **K8s Event (事实#1)** 明确报错 `failed to find plugin "aiops-unavailable"`。
  * **K8s Config (事实#3)** 确认了 Pod 确实请求了使用该插件的网络。
* **现象关联**：
  * 该失败直接导致 **Pod Status (事实#2)** 卡在 `Pending` 且状态为 `ContainerCreating`。
  * **Metric (事实#4, #5)** 确认了容器处于 Waiting 状态且未发生过重试。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 43.3s
├─ 并发证据采集: 39.7s
│  └─ g1 aiops-case-v14/workload: 39.7s (Evidence 32.6s, RCA 7.0s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed

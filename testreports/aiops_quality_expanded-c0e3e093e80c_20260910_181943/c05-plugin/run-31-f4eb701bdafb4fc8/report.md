## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `FailedCreatePodSandBox` | 47m kubelet: `Failed to create pod sandbox: ... plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` (fact-7d6c770ec5fd) | **直接根因证据**：明确指示 Multus 网络插件加载失败，核心原因为系统路径中缺失 `aiops-unavailable` 插件二进制文件。 |
| 2 | K8s Event | Annotations/Annotations | `k8s.v1.cni.cncf.io/networks: secondary-net` (fact-a7c70ee91e82) | **配置证据**：证实 Pod 被配置了名为 `secondary-net` 的多网络接口，解释了为何调用的是 Multus 插件。 |
| 3 | Metric | `kube_pod_container_status_waiting_reason` | `ContainerCreating` (fact-ebf91cc3150f) | **状态印证**：Metric 数据与 K8s Event 描述的状态一致，确认容器处于 CNI 配置阻塞的等待阶段。 |
| 4 | K8s Config | Resources | 请求量：5m CPU, 8Mi Memory (fact-0b2902512d03, fact-3aca9c629bae)；限制量：50m CPU, 32Mi Memory (fact-65bc75846760, fact-f8cdde593446) | **排除资源因素**：显式列出资源请求与限制，说明 Pod 调度与配置正常，当前卡滞非由资源不足引起。 |

**证据关联性说明：**
- K8s Event（#1）提供了唯一的直接故障原因，定位到具体的 CNI 插件缺失。
- K8s Config（#2）解释了触发该插件需求的业务配置来源。
- Metric（#3）确认了故障现象处于持续的等待状态，且未进入应用生命周期（配合日志缺失说明）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义了 secondary-net 网络引用 → 节点 /opt/cni/bin 路径缺失 aiops-unavailable 二进制文件 → Multus CNI 插件加载失败，Sandbox 网络配置中止 → Pod 持续处于 ContainerCreating/Pending 状态
```

### 根因结论

**已确认根因**：节点上 CNI 插件缺失。

集群中的 Pod `aiops-case-v14/workload` 试图挂载名为 `secondary-net` 的自定义网络，该配置要求节点上的 CNI 插件目录中存在对应的 `aiops-unavailable` 插件可执行文件。证据显示该插件在节点路径下完全缺失，导致 `multus` 插件无法执行网络配置任务，从而引发 `FailedCreatePodSandBox` 事件并使 Pod 停滞。现有 K8s Event 提供了确凿的事实支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 23.4s
├─ 并发证据采集: 32.2s
│  └─ g1 aiops-case-v14/workload: 32.2s (Evidence 25.2s, RCA 6.7s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed

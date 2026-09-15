## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload (aiops-case-v14) stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Failed to create pod sandbox: ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` (fact-da4fa231fa15) | 核心证据：指出容器网络初始化因缺少特定 CNI 插件二进制文件而终止。 |
| 2 | K8s State | pod.status | `Pending`, `ContainerCreating` (fact-43a01dead9f1, fact-500c3703e541) | 确认可观测到的直接现象：Pod 无法完成启动阶段，停留在等待状态。 |
| 3 | Metric | kube_pod_container_status_waiting_reason | `reason="ContainerCreating"`, `value=1` (fact-5753db635850) | 独立于 K8s API 的确认，验证容器处于网络配置受阻的等待中。 |
| 4 | K8s Config | pod.annotation | `k8s.v1.cni.cncf.io/networks: secondary-net` (fact-164c8988fc74) | 上下文证据：解释为何会触发对 "aiops-unavailable" 插件的查找。 |

**证据分析：**
证据 1 给出了具体的失败原因为 `failed to find plugin "aiops-unavailable"`，直接解释了证据 2 和证据 3 中 Pod 处于 `Pending/ContainerCreating` 状态的原因。证据 4 补充说明了该插件调用是由 Secondary Net 配置触发的。Kubelet 的报错事实（#1）与 Pod 状态（#2）及 Metric 指标（#3）完全一致，形成了从原因到现象的闭环。Logging 和 Tracing 因 Pod 未启动而未采集到数据，但这不影响基于 K8s 原生事实和 Metrics 的结论。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 的 /opt/cni/bin 目录缺失 'aiops-unavailable' CNI 二进制文件 → Multus 插件无法配置 secondary-net 网络 → Kubelet 报告 FailedCreatePodSandBox → Pod 卡在 Pending/ContainerCreating 状态
```

### 根因结论

已确认的根因是**节点 `node2` 的 `/opt/cni/bin` 目录下缺失名为 `aiops-unavailable` 的 CNI 插件二进制文件**（证据 #1）。

由于 Pod `aiops-case-v14/workload` 通过注解引用了该插件（证据 #4），Multus 在尝试为 Pod 配置 `secondary-net` 时因找不到插件而报错，导致 Kubelet 无法创建 Pod 沙箱（evidence #1），从而使 Pod 永远停留在 `Pending` 状态（证据 #2, #3）。

目前的诊断不足以解释“为何该二进制文件会缺失”（例如是部署遗漏还是文件损坏），但现有证据已足够解释当前的故障现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.2s
├─ 并发证据采集: 37.2s
│  └─ g1 aiops-case-v14/workload: 37.2s (Evidence 29.1s, RCA 7.9s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed

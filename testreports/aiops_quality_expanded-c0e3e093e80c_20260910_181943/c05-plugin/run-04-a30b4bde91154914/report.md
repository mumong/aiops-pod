## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 处于 ContainerCreating 状态，Sandbox 创建失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubelet` 日志 | `Warning FailedCreatePodSandBox ... Failed to create pod sandbox: rpc error: ... plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 直接定位到网络插件缺失，导致沙箱创建失败 |
| 2 | K8s State | `Pod Status` | `status: "ContainerCreating"`, `phase: "Pending"` | 确认 Pod 停留在初始化阶段，容器未实际启动 |
| 3 | K8s Config | `ConfigMap/Annotation` | `k8s.v1.cni.cncf.io/networks: secondary-net` | 证实 Pod 配置了 Multus CNI 及 secondary-net 网络，触发对特定插件的调用 |

**证据说明：**
*   **证据 1** 提供了故障的直接因果链：Pod 配置的 `secondary-net` 要求加载 `aiops-unavailable` 插件，但节点路径中该文件缺失，引发 `FailedCreatePodSandBox` 异常。
*   **证据 2** 与证据 1 现象一致，排除了因资源竞争导致的 Pending，确认瓶颈在于容器生命周期（沙箱创建）。
*   **证据 3** 解释了触发点，Pod 注解正确指向了缺失的插件，确认配置意图与运行环境的差异。

## 🎯 根因分析 · g1

### 因果链

```text
Multus 配置要求加载 'aiops-unavailable' CNI 插件 → 节点 node2 系统路径 [/opt/cni/bin] 缺失该插件二进制文件 → Kubelet 调用 CNI 失败并抛出 FailedCreatePodSandBox 错误 → Pod aiops-case-v14/workload 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为**目标节点缺少必需的 CNI 插件二进制文件**。

Pod `aiops-case-v14/workload` 的 `secondary-net` 网络配置（`k8s.v1.cni.cncf.io/networks: secondary-net`）指示 Multus 加载名为 `aiops-unavailable` 的插件。然而，Kubelet 日志（事实 1）明确指出在 CNI 插件查找路径中未能找到该二进制文件。这导致沙箱创建阶段失败，使 Pod 始终停留在 `ContainerCreating` 状态，无法进入 `Running`。现有证据（K8s 事件与状态）已充分支撑此结论，无需更多日志或指标确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.8s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-v14/workload: 37.8s (Evidence 30.1s, RCA 7.6s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed

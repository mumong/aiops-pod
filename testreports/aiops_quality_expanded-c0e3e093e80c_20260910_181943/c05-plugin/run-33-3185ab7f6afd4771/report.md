## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 持续处于 ContainerCreating 状态，无法创建沙箱并启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-b9720a9f6dfa` | `FailedCreatePodSandBox: ... plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | **核心诊断**：明确指出了 Pod 绑定 `secondary-net` 时，因节点缺失名为 `aiops-unavailable` 的 CNI 插件二进制文件导致网络初始化失败。 |
| 2 | K8s Config | `fact-4a6a771ce8a6` | `k8s.v1.cni.cncf.io/networks: secondary-net` | **上下文**：确认 Pod 定义了非默认的 Multus 网络请求，与事件中的网络名称对应。 |
| 3 | K8s State | `fact-eb1319976ed9` | `ContainerCreating` (reason) | **现象确认**：验证容器因等待底层环境准备（网络沙箱）而停滞。 |
| 4 | K8s State | `fact-2c3cd91a05f3` | `Pending` (phase) | **现象确认**：Pod 处于待调度/待就绪状态，未进入 Running。 |
| 5 | Metric | `fact-50bebcdb34c1` | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | **交叉验证**：Metrics 状态与 K8s 事件和状态一致，证实等待原因为网络初始化受阻。 |
| 6 | K8s State | `fact-7e2dd1d9afd1` | `restart_count: 0` | **排除干扰**：容器尚未启动过，不存在因 OOMKilled 或 CrashLoopBackOff 导致的重启。 |

**证据说明：**
K8s Event (#1) 提供了最直接的错误信息，指出缺少特定 CNI 插件。Pod 配置 (#2) 证实了该插件的需求来源。K8s State (#3, #4) 与 Metric (#5) 共同验证了 Pod 当前卡在网络初始化阶段的“等待”现象，且因重启次数为 0 (#6) 排除了应用层逻辑错误。Logging 和 Tracing 因容器未启动而缺失，但这符合当前故障状态。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 的 /opt/cni/bin 路径中缺失 'aiops-unavailable' 插件二进制文件 → Multus CNI 插件在添加容器到 'secondary-net' 网络时无法找到并执行该插件 → kubelet 创建沙箱失败 (FailedCreatePodSandBox) → Pod aiops-case-v14/workload 无法启动并持续处于 ContainerCreating 状态
```

### 根因结论

**已确认根因**：Pod 配置的 Multus 网络 `secondary-net` 引用了名为 `aiops-unavailable` 的二进制 CNI 插件，但调度到的节点上该插件缺失。

这直接导致 kubelet 在初始化 Pod 沙箱时调用 Multus 插件失败，引发 `FailedCreatePodSandBox` 错误，进而使 Pod 陷入 `ContainerCreating` 的等待状态（证据：`fact-b9720a9f6dfa`, `fact-4a6a771ce8a6`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 21.4s
├─ 并发证据采集: 34.9s
│  └─ g1 aiops-case-v14/workload: 34.9s (Evidence 27.1s, RCA 7.6s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed

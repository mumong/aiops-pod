## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 卡在 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-8a4afadd7f22` | `FailedCreatePodSandBox`: plugin type="multus" name="multus-cni-network" failed (add): error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path | 确认故障直接原因：CNI 插件缺失导致网络沙箱创建失败 |
| 2 | K8s Config | `fact-56d9bb9abf7d` | `Annotations: k8s.v1.cni.cncf.io/networks: secondary-net` | 指出 Pod 依赖二级网络插件 "secondary-net" |
| 3 | K8s State | `fact-b257c3fa1cff` | Container "app" waiting_reason: `ContainerCreating` | 证实容器处于启动前等待阶段，未进入运行态 |
| 4 | K8s State | `fact-412a43eb61fb` | Pod phase: `Pending` | 结合事件表明 Pod 调度成功但无法进入运行阶段 |
| 5 | Metric | `fact-e9eeeb06d94d` | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 | 独立量化验证 Pod 卡滞在 ContainerCreating 状态 |
| 6 | Metric | `fact-6592e48318f8` | `kube_pod_status_phase{phase="Pending"}` = 1 | 独立量化验证 Pod 阶段停留在 Pending |
| 7 | K8s Config | `fact-1211c1363cd7` | Container "app" resource_limit.memory: `32Mi` | 资源配置上下文（非故障原因） |
| 8 | K8s Config | `fact-3b76435093be` | Container "app" resource_limit.cpu: `50m` | 资源配置上下文（非故障原因） |

**证据印证：**
- 维度 1 与 2 结合：Pod 声明使用 "secondary-net" 网络，Multus 在尝试附加该网络时因找不到插件 "aiops-unavailable" 而报错。
- 维度 3、4 与 5、6 结合：K8s 原生状态（Pending/ContainerCreating）与 Prometheus 监控指标（Waiting Reason/Phase）完全一致，排除了单点数据异常。
- Logging/Tracing 标记为 `not_applicable`，因为容器从未启动，这是 CNI 阶段失败的自然结果。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 CNI 插件路径下缺失插件 "aiops-unavailable" → Multus 无法为 secondary-net 附加网络 → kubelet 报 FailedCreatePodSandBox 错误 → Pod aiops-case-v14/workload 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为 **CNI 插件缺失**。
Pod YAML 中通过注解 `k8s.v1.cni.cncf.io/networks: secondary-net` 请求使用 "secondary-net" 网络，而负责处理该网络的 Multus CNI 插件在节点上找不到依赖的自定义插件 "aiops-unavailable"（`fact-8a4afadd7f22`）。这导致网络沙箱创建失败，Pod 无法完成初始化。
Metric 数据（`fact-e9eeeb06d94d`, `fact-6592e48318f8`）独立验证了 Pod 持续处于 `ContainerCreating` 和 `Pending` 状态，与事件日志中的失败机制相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 25.0s
├─ 并发证据采集: 48.0s
│  └─ g1 aiops-case-v14/workload: 48.0s (Evidence 35.9s, RCA 11.0s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-imagepull-failed, pod-config-error

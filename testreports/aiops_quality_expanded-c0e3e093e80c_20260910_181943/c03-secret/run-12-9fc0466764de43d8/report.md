## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 处于 Pending/ContainerCreating 状态，持续挂载失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod State | Pod Phase: Pending, Ready Condition: False | 确认 Pod 停滞在 Pending 阶段，未处于 Running 状态 |
| 2 | K8s Event | Kubelet | FailedMount: secret "unavailable-input" not found | **直接证据**：明确指向依赖的 Secret 对象不存在 |
| 3 | K8s Event | Kubelet | FailedMount: Unable to attach or mount volumes: unmounted volumes=[input]: timed out waiting | 佐证挂载操作因资源缺失陷入超时循环 |
| 4 | K8s State | Pod Container Status | Waiting Reason: ContainerCreating | 解释为何应用未启动且无日志输出 |

**证据印证：**
1. 事实 #1（Pod Pending）与事实 #3（Volume Mount Timeout）结合，证实故障发生在启动前（Pre-start）的卷挂载阶段。
2. 事实 #2（Secret "unavailable-input" not found）给出了上述事实的精确原因，排除了网络或集群资源层面的故障。
3. 事实 #4 解释了 Logging/Tracing 维度的 `not_applicable` 状态，因容器未进入运行态，无法采集业务应用日志。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 缺失（Namespace: aiops-case-v04） → Pod spec 卷 'input' 挂载检查失败（FailedMount） → Kubelet 持续重试导致 Pod 卡在 Pending/ContainerCreating 状态 → 应用逻辑无法执行
```

### 根因结论

Pod `aiops-case-v04/workload` 处于 **Pending/ContainerCreating** 状态的根因是 **卷挂载依赖缺失**（证据 #2）。

具体而言，Pod 规范中定义的 Volume `input` 引用了 Secret `unavailable-input`，但在 `aiops-case-v04` 命名空间中该 Secret 对象不存在。Kubelet 在预检阶段无法找到目标资源，导致挂载操作反复失败（证据 #2、#3），进而阻止了容器进入 Running 状态（证据 #1、#4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.4s
├─ 并发证据采集: 40.9s
│  └─ g1 aiops-case-v04/workload: 40.9s (Evidence 32.0s, RCA 8.7s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed

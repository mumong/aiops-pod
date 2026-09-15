## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload stuck in ContainerCreating (Pending) due to FailedMount on 'input' volume |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-a2429cb1e3dd` | Pod `aiops-case-v06/workload` phase 为 `Pending`，Status 为 `Pending` | 确认 Pod 调度成功但启动阻塞 |
| 2 | K8s State | `fact-c62643bb5305` | 容器 `app` 等待原因为 `ContainerCreating` | 定位到容器生命周期停滞在挂载阶段 |
| 3 | K8s Event | `fact-18bfd9a5f205` | `FailedMount`: "Unable to attach or mount volumes: unmounted volumes=[input]" | 确认挂载失败的具体卷名称 |
| 4 | K8s Event | `fact-bab1effa89f0` | `FailedMount`: "hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory" | 根因定位：宿主机目标路径不存在或非目录 |

**证据分析：**
K8s 状态（#1, #2）与事件（#3）一致指向挂载失败，而事件 `fact-bab1effa89f0` 明确提供了失败的具体路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 及原因 `not a directory`，直接证实了宿主机环境缺失或无效。

## 🎯 根因分析 · g1

### 因果链

```text
hostPath 目录 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或非目录 → kubelet hostPath 类型检查失败 → 卷挂载失败 (FailedMount) → Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认根因：**
Pod `aiops-case-v06/workload` 的 `input` 卷挂载失败。Kubelet 在节点上执行挂载操作时，发现目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不存在或不是一个有效的目录（`hostPath type check failed`），导致卷挂载流程中断，容器无法启动（见证据 #3, #4）。

**未确认项：**
目标目录是意外被删除，还是从未在节点环境搭建阶段创建（见输入 unknowns）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 23.0s
├─ 并发证据采集: 32.9s
│  └─ g1 aiops-case-v06/workload: 32.9s (Evidence 23.6s, RCA 9.2s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed

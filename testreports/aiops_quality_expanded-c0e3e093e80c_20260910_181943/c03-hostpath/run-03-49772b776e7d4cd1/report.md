## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod `aiops-case-v06/workload` 配置了一个 `HostPath` 卷 `input`，指定挂载节点 `node2` 上的路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input`。由于该路径在目标节点上不存在（或不是目录），导致 `kubelet` 挂载失败，容器被阻塞在 `ContainerCreating` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `FailedMount`: hostPath type check failed: `/var/lib/aiops-fixture-unavailable-7f394bef/input` is not a directory (fact-1968112acb90) | 核心故障证据，直接指明挂载失败的具体原因 |
| 2 | K8s State | `kubernetes` | `pod.status`: `Pending` (fact-771fc3f848e2) | 症状确认，Pod 处于待调度/创建等待状态 |
| 3 | K8s State | `kubernetes` | `container.waiting_reason`: `ContainerCreating` (fact-4df9b94cc166) | 症状确认，容器因挂载阻塞尚未进入运行态 |
| 4 | K8s Event | `kubernetes` | `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition (fact-5b74d637a9e1) | 辅助验证，反映了多次挂载尝试的超时状态 |

证据分析：
- K8s 事件 `FailedMount` 明确指出 `hostPath` 路径校验失败（非目录），这与 `ContainerCreating` 状态一致，证实了 Pod 因存储卷配置问题被阻塞。
- 无应用日志与 Trace 数据，符合容器未启动的预期。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机 node2 路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或不是目录 → Pod YAML 配置 HostPath 卷挂载到该路径 → kubelet 挂载卷失败 (hostPath type check failed) → Pod 状态停留在 Pending / ContainerCreating
```

### 根因结论

**根因确认**：
Pod `aiops-case-v06/workload` 挂载的 `HostPath` 卷 `input` 指向的目标路径在节点 `node2` 上不存在或不符合目录要求（证据 #1），导致 `kubelet` 挂载失败并阻断容器启动（证据 #2, #3）。

**缺失信息**：
无法确认该路径缺失是宿主机文件系统异常（如意外删除）还是 Pod 配置本身存在错误。

---

## 📊 性能统计

```text
├─ 总耗时: 55.7s
├─ 问题定位: 11.6s
├─ 并发证据采集: 36.0s
│  └─ g1 aiops-case-v06/workload: 36.0s (Evidence 28.3s, RCA 7.6s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed

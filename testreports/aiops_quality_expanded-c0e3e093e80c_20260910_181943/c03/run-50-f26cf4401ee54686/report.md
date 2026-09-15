## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 持续处于 ContainerCreating 状态未恢复 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-ad6ca1cfe187) | `FailedMount`：configmap "unavailable-config" not found (8m52s, x60 over 114m) | 确认卷挂载失败的直接错误信息，指向缺失的 ConfigMap |
| 2 | K8s Event | kubernetes (fact-da8038005e77) | `FailedMount`：Unable to attach or mount volumes: unmounted volumes=[input] (3m56s, x49 over 112m) | 佐证挂载失败已持续较长时间 (112m+) 且被 kubelet 持续重试 |
| 3 | K8s State | kubernetes (fact-535bf1ee646d) | `Pending` | 提供 Pod 整体调度/生命周期停滞的状态确认 |
| 4 | Metric | prometheus (fact-68db1b283ac2) | `kube_pod_container_status_waiting_reason`=1 (reason: `ContainerCreating`) | 确认容器因等待特定状态 (ContainerCreating) 而停止运行 |
| 5 | Metric | prometheus (fact-46939f856bd2) | `kube_pod_container_status_restarts_total`=0 | 确认容器尚未启动，因此未发生过重启 |

**证据印证说明：**
事件 (fact-ad6ca1cfe187, fact-da8038005e77) 中的 `FailedMount` 与 `unavailable-config` 缺失明确解释了为何容器状态卡在 `ContainerCreating` 且重启数为 0 (Metric fact-68db1b283ac2, fact-46939f856bd2)。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 模板引用不存在的 ConfigMap 'unavailable-config' (fact-ad6ca1cfe187) → Kubelet 挂载 volume 'input' 失败并持续重试 (fact-ad6ca1cfe187, fact-da8038005e77) → 沙箱创建阻塞，Pod 状态转为 Pending (fact-535bf1ee646d) → 用户可见 Pod 持续处于 ContainerCreating 状态未恢复
```

### 根因结论

**已确认的根因：** Pod `aiops-case-03/workload-5b5fc86c8c-xn974` 的 `volume 'input'` 配置引用了不存在的 ConfigMap `unavailable-config`。由于该卷配置为非可选 (Optional=false)，Kubelet 在尝试挂载时因找不到配置数据而持续失败并报错 `FailedMount`，导致容器运行时无法启动沙箱，Pod 因此被永久卡在 `ContainerCreating` / `Pending` 状态。

**关键证据引用：** `fact-ad6ca1cfe187` (ConfigMap not found), `fact-535bf1ee646d` (Pending 状态)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 28.8s
├─ 并发证据采集: 28.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 28.2s (Evidence 18.8s, RCA 9.3s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-sandbox-create-failed

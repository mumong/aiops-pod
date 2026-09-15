## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod `workload-6584f97c76-h4lt9` 的容器配置中引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key`，而该 Secret 实际仅包含 `available-key`，导致 Kubelet 在拉取容器配置时失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (Failed, x12 over 62m) | 记录 Kubelet 拉取容器配置时的具体错误 |
| 2 | K8s State | kubernetes | `waiting_reason: CreateContainerConfigError` (container: app) | 确认容器因配置错误处于等待状态 |
| 3 | K8s State | kubernetes | `waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 明确指出缺失的键名及所在的 Secret |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (`reason: CreateContainerConfigError`) | 监控数据证实容器正在因配置错误等待 |
| 5 | K8s State | kubernetes | `pod.status: Pending`, `restart_count: 0` | 确认 Pod 尚未启动且未发生过重启 |

**证据关联说明：**
K8s Event (1) 与 Waiting Message (2, 3) 在 Kubelet 层面相互印证，共同指向 `aiops-case-04/workload-input` Secret 中缺少 `unavailable-key` 这一事实；Metric (4) 的 `CreateContainerConfigError` 与 K8s 状态完全同步，而 `restart_count: 0` (5) 证实了该错误导致容器始终停留在启动前的等待阶段，未产生任何应用日志或业务请求。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了 Secret `aiops-case-04/workload-input` 中不存在的 Key `unavailable-key` → Kubelet 拉取容器配置失败 → Pod 容器进入 `CreateContainerConfigError` 状态并停止在 `Pending` → 用户侧无法使用该应用服务
```

### 根因结论

已确认根因为**应用配置引用了不存在的数据键**（证据 1-3）。

Pod `aiops-case-04/workload-6584f97c76-h4lt9` 的容器定义中请求使用 Secret `aiops-case-04/workload-input` 里的 `unavailable-key`，但该 Secret 实际仅包含 `available-key`。Kubelet 在尝试挂载该配置以启动容器 `app` 时检测到缺失，从而主动终止了启动流程，导致容器持续报错 `CreateContainerConfigError` 且 Pod 处于 `Pending` 状态（证据 4, 5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.8s
├─ 并发证据采集: 46.7s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 46.7s (Evidence 40.4s, RCA 6.2s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error

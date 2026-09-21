## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod workload (aiops-case-v07) 处于 ImagePullBackOff 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: "ImagePullBackOff" (容器: app) | 确认 Pod 当前卡在镜像拉取失败状态 |
| 2 | K8s Event | Kubernetes | `Failed` 事件: "rpc error: code = NotFound desc = failed to pull and unpack image ...: not found" | 明确故障机制：远程仓库返回 NotFound 错误 |
| 3 | K8s Config | Kubernetes | `image`: "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908" | 锚定引发故障的确切镜像及不存在的标签 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}`: 1 | 验证 K8s 状态指标与 Event 现象一致 |
| 5 | K8s State | Kubernetes | `pod.status`: "Pending", `restart_count`: 0 | 确认 Pod 始终无法启动且未发生过重启 |

证据 2 与 3 结合指出了明确的失败原因：Kubelet 尝试拉取配置中指定的特定镜像标签时，仓库直接报错 `NotFound`。证据 4 和 1 从指标层面佐证了这一 K8s 内部状态，确认了故障的持续性。

## 🎯 根因分析 · g1

```text
镜像标签 'aiops-fixture-unavailable-20260908' 在仓库中不存在 → Kubelet 拉取镜像返回 NotFound 错误 → K8s 持续尝试拉取失败并进入 Back-off 状态 → Pod 处于 ImagePullBackOff 且 Pending
```

### 根因结论

**已确认根因**：Pod `aiops-case-v07/workload` 配置中引用的容器镜像标签 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程镜像仓库中不存在（对应事实 3、证据 2）。

该根因直接导致了 Kubelet 拉取失败，进而使 Pod 状态持续处于 `ImagePullBackOff` 和 `Pending`，用户可见现象为容器无法正常启动且处于 Back-off 退避阶段（对应事实 1、证据 1、4、5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.9s
├─ 并发证据采集: 44.5s
│  └─ g1 aiops-case-v07/workload: 44.5s (Evidence 36.3s, RCA 8.1s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

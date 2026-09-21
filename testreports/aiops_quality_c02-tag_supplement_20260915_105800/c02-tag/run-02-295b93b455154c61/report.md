## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | aiops-case-v07/workload Pod处于ImagePullBackOff状态，Pending且未运行 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason="ImagePullBackOff", pod.status="Pending" | 确定 Pod 当前异常状态 |
| 2 | K8s Event | kubernetes | Warning Failed: Failed to pull image ".../pause:aiops-fixture-unavailable-20260908": rpc error: code = NotFound desc = ... not found | 直接证据，证明镜像 tag 不存在 |
| 3 | K8s Event | kubernetes | Normal BackOff: Back-off pulling image ".../pause:aiops-fixture-unavailable-20260908" (x7 over 2m21s) | 现象延续性，证明节点正在重试拉取并进入退避 |
| 4 | Metric | prometheus | kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1 (当前值) | 确认容器等待状态的指标映射，与 K8s 事件一致 |

**证据说明：**
- K8s 事件记录 `fact-4c7a599848e5` 明确指出 `NotFound` 错误，直接对应 `fact-e59459845ae6` 中的 `ImagePullBackOff` 原因。
- Metric 数据 `fact-e8a134f7c0a9` 独立验证了容器处于 `ImagePullBackOff` 等待状态的客观事实。
- Logging 和 Tracing 维度均为 `not_applicable`，因容器尚未启动，无应用级数据佐证，但 K8s 层证据已形成闭环。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 tag "aiops-fixture-unavailable-20260908" 在仓库中不存在 → Kubelet 解析 reference 失败 (NotFound) → 无法拉起容器并进入回退等待状态 → Pod 处于 Pending 且 ImagePullBackOff 状态
```

### 根因结论

已确认的根因为：Pod 配置的 `pause` 镜像 tag（`aiops-fixture-unavailable-20260908`）在指定镜像仓库 `registry.cn-hangzhou.aliyuncs.com/google_containers` 中不存在。

该结论由 K8s 事件事实 `fact-4c7a599848e5` 中记录的 `rpc error: code = NotFound` 直接支撑，并伴随 Kubelet 持续的重试退避行为（`fact-0c2ef33ad414`），导致 Pod 长期卡在 `ImagePullBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.4s
├─ 并发证据采集: 41.3s
│  └─ g1 aiops-case-v07/workload: 41.3s (Evidence 33.8s, RCA 7.3s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

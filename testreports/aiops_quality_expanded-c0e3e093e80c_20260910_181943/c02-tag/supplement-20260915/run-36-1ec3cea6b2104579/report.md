## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | 镜像 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908' 在目标仓库中不存在（NotFound） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Warning Failed: `rpc error: code = NotFound desc = failed to pull and unpack image... pause:aiops-fixture-unavailable-20260908` | 直接指出镜像拉取失败的底层错误为 NotFound |
| 2 | K8s State | container.status | Waiting Reason: `ImagePullBackOff`, Message: `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 确认容器当前处于镜像拉取失败后的退避状态 |
| 3 | K8s State | pod.condition | Ready: `False`, Reason: `ContainersNotReady`, Message: `containers with unready status: [app]` | 证实 Pod 因容器未就绪而未达到可用状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1, Reason: `ImagePullBackOff` | 独立指标证实当前容器处于等待拉取镜像状态 |

上述 K8s 事件明确记录了镜像解析失败的 `NotFound` 错误，直接对应容器状态的 `ImagePullBackOff`。监控指标仅提供了单一时间点的 `1` 值且 `trend_evaluable=false`，作为同步状态的佐证。由于容器未能启动，日志与链路追踪为空，物理上无法提供更丰富的调用上下文。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库不存在目标版本 (NotFound) → kubelet 拉取镜像失败 → 容器状态进入 ImagePullBackOff → Pod 保持 Pending 且不可用
```

### 根因结论

已确认根因为目标镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程仓库中不存在。

证据表明：K8s 事件（#1）记录了明确的 `NotFound` 错误，证明镜像拉取失败非网络或权限问题，而是资源不存在；容器状态（#2）和 Pod 条件（#3）证实该失败直接导致了 `ImagePullBackOff` 和 `ContainersNotReady`。监控数据（#4）进一步确认了该状态的持续性。日志与链路追踪为空是由于容器从未成功启动，属于结果而非原因。

---

## 📊 性能统计

```text
├─ 总耗时: 56.8s
├─ 问题定位: 14.0s
├─ 并发证据采集: 34.7s
│  └─ g1 aiops-case-v07/workload: 34.7s (Evidence 29.4s, RCA 5.2s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

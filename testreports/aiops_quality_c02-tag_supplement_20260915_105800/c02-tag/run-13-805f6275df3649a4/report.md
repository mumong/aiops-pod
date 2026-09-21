## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod `aiops-case-v07/workload` 配置的镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在目标仓库中不存在（Tag 错误/缺失）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `ImagePullBackOff` (fact-id: fact-9f6c1fa66f96) | 确认容器正处于因镜像拉取失败导致的等待状态 |
| 2 | K8s Event | Kubernetes | `Failed` (x4): `rpc error: code = NotFound desc = ... registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908: not found` (fact-id: fact-61091c1e640a) | 证明底层镜像拉取服务明确返回 404 NotFound，确认镜像不可用 |
| 3 | K8s Event | Kubernetes | `BackOff` (x44): `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (fact-id: fact-bb7509139991) | 反映 kubelet 已多次尝试拉取该镜像并进入指数退避阶段，符合持续失败的特征 |
| 4 | K8s State | Kubernetes | `container.waiting_message`: `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (fact-id: fact-3e9720bf7a52) | 进一步锁定具体的镜像引用路径 |
| 5 | K8s State | Kubernetes | `container.restart_count`: 0 (fact-id: fact-6a2f1afc40c6) | 排除因资源争抢导致容器 CrashLoopBackOff 的可能，印证故障发生在启动阶段 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (app, ImagePullBackOff): 1 (fact-id: fact-5a4e8db24ae2) | 监控指标独立印证当前等待原因及状态，无其他等待原因出现 |

Kubernetes 状态与事件记录高度一致，Kubelet 在多次重试拉取特定镜像均返回 `NotFound` 后，将容器状态标记为 `ImagePullBackOff` 并进入退避机制。Metric 数据在监控维度上同步记录了该容器处于 `ImagePullBackOff` 等待状态。

## 🎯 根因分析 · g1

### 因果链

```text
目标镜像 Tag 在仓库中不存在 (registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908) → Kubelet 拉取镜像失败 (返回 NotFound) → 容器无法启动并进入退避重试 (ImagePullBackOff) → Pod `aiops-case-v07/workload` 长期处于 Pending/不Ready 状态
```

### 根因结论

已确认根因为：**Pod 配置的镜像引用 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在目标仓库中不存在（Tag 错误/缺失）**。

证据编号 **2** (Event: `not found`) 与 **4** (Waiting Message) 直接揭示了底层拉取失败的明确原因；证据 **1**、**3** 和 **6** 分别从容器状态、重试机制和监控维度佐证了这一持续性的镜像不可用现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.3s
├─ 并发证据采集: 39.8s
│  └─ g1 aiops-case-v07/workload: 39.8s (Evidence 32.8s, RCA 6.7s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

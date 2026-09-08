## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 配置了无效镜像仓库域名 'registry.invalid'，导致 DNS 解析失败，镜像拉取被阻断。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 状态 `Pending`；容器 `app` 状态 `waiting_reason=ImagePullBackOff`；`containersNotReady: [app]` | 直接定位异常实体的当前阻塞状态 |
| 2 | K8s Event | kubernetes | `Failed` (x4): `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host`；`Error: ErrImagePull` | 证明 DNS 解析失败是拉取失败的直接触发点 |
| 3 | K8s Event | kubernetes | `BackOff` (x66): `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认拉取操作已进入重试退避阶段，持续阻塞 |
| 4 | K8s State | kubernetes | `container.waiting_message`: `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 提供 Pod 内部容器因镜像拉取受阻的明确状态文本 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` | 从监控层面独立印证了 Pod 等待拉取镜像的异常事实 |
| 6 | Metric | prometheus | `kube_pod_status_phase{container="app", phase="Pending"} = 1` | 从监控层面印证了 Pod 未成功启动且处于挂起状态的结论 |

**证据互证说明：**
- **事实印证**：K8s 事件记录了 `no such host` 的具体 DNS 错误，配合 `container.waiting_reason=ImagePullBackOff` 的状态变更，逻辑闭环确认了“镜像拉取受阻”这一核心事实。
- **维度一致**：Prometheus 指标（Fact #5, #6）与 K8s 状态（Fact #1）在异常类型（ImagePullBackOff）和运行阶段（Pending）上完全一致，排除了瞬时网络抖动后恢复正常的可能性，确认为配置层面的持续阻断。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置了无效镜像仓库域名 'registry.invalid' → DNS 解析失败 (lookup ... no such host) → 镜像拉取被阻断 (ImagePullBackOff) → Pod 状态变为 Pending 且无法提供服务
```

### 根因结论

已确认根因为：**Pod 配置了无效镜像仓库域名 `registry.invalid`**。

该配置导致 kubelet 在拉取镜像时触发 DNS 查询失败（`no such host`），进而使镜像拉取操作不断重试并进入 `BackOff` 阶段。该因果链直接造成了 Pod 持续处于 `Pending` 状态且容器无法就绪的现象（支撑证据：Fact #2, #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.2s
├─ 并发证据采集: 33.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 33.3s (Evidence 28.8s, RCA 4.4s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed

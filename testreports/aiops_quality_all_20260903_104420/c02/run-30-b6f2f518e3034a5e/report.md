## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod 状态 | `container.waiting_reason: ImagePullBackOff` | 确认异常状态 |
| 2 | K8s State | 容器日志 | `message: "Back-off pulling image \"registry.invalid/aiops/workload:missing\"" ` | 暴露镜像地址及域名问题 |
| 3 | K8s Event | 事件记录 | `BackOff x262 over 63m` | 确保持续重试与退避行为 |
| 4 | K8s State | 拓扑信息 | `pod.status: Pending`, `pod.condition: ContainersReady False` | 印证容器无法就绪 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: 1` (reason=ImagePullBackOff) | 提供指标层面的佐证 |

**证据说明**
- **现象一致**：Kubernetes 的 K8s State (fact-13551aa1b15b) 显示 `ImagePullBackOff`，且 Metric (fact-3ba4b5ee4c39) 在同一时刻验证了该状态值。
- **机制明确**：K8s Event (fact-e67d8384cfc5) 记录了长达 63 分钟的 `Back-off` 行为，说明拉取动作在反复失败后进入了指数退避阶段，符合 `ImagePullBackOff` 的典型表现。
- **核心线索**：真实错误信息 (fact-b23984ca35d0) 明确指出镜像源为 `registry.invalid`，该域名属于保留的无效测试域名，直接导致解析失败。

## 🎯 根因分析 · g1

### 因果链

```text
配置了无效域名镜像源 (registry.invalid) → DNS 解析失败 (无法连接仓库) → 拉取触发指数退避机制 → Pod 处于 ImagePullBackOff 状态
```

### 根因结论

**已确认根因：镜像地址配置错误（使用了无效的 `.invalid` 域名）**。

- Pod `aiops-case-02/workload-65b7f54794-rnlv4` 尝试拉取镜像 `registry.invalid/aiops/workload:missing`。
- 证据 **fact-b23984ca35d0** 和 **fact-e67d8384cfc5** 显示 Kubelet 在拉取该镜像时遭遇失败，并进入了 `Back-off pulling image` 的状态。
- `.invalid` 是一个保留域名（RFC 2606），在标准网络环境中不可解析，这构成了拉取失败的直接机制。
- Metric 数据 **fact-3ba4b5ee4c39** 提供了独立的确认：当前等待原因指标 `waiting_reason` 确认为 `ImagePullBackOff`。

**未确认项**：
- 由于域名本身不可解析，无法进一步验证仓库端的 `Tag: missing` 是否真实存在或仓库是否有其他网络连通性问题（证据不足）。
- Logging 和 Tracing 维度因底层权限问题执行失败且容器未启动，无应用日志，因此对“镜像内容”本身的分析缺失，但不影响对“拉取失败原因”的诊断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 24.3s
├─ 并发证据采集: 56.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 56.7s (Evidence 47.8s, RCA 8.7s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

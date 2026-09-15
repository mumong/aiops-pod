## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-jmq6b 处于 ImagePullBackOff 状态，持续无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": ... failed to resolve reference ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-59ee9d0371d7) | 核心证据，直接指出镜像仓库域名在 DNS 中不可达 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: ImagePullBackOff, `container.waiting_message`: Back-off pulling image "registry.invalid/aiops/workload:missing" (fact-57328e7af436, fact-befc2ed55ebd) | 证实容器处于因拉取镜像失败而触发的退避状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason=ImagePullBackOff) (fact-345c9e5c7e31) | 辅助观测，确认集群层面存在 ImagePullBackOff 状态 |
| 4 | K8s State | Kubernetes | `pod.status`: Pending, `pod.condition.Ready`: False (ContainersNotReady) (fact-62d24db27cb0, fact-e5c8b4bbb99d) | 描述现象结果，Pod 停留在 Pending 阶段无法转为 Running |

上述 K8s 事件直接揭示了镜像解析失败的确切原因（DNS 查询失败）。K8s 状态字段（ImagePullBackOff）与 Prometheus 监控指标相互印证了当前持续处于镜像拉取退避中。Pod 处于 Pending 状态是由于镜像无法拉取导致的必然结果。

## 🎯 根因分析 · g1

### 因果链

```text
集群 DNS 127.0.0.53 无法解析 registry.invalid (事实: #1) → Kubelet 拉取镜像时 DNS 查询失败 → 镜像拉取报错并进入指数退避 (Fact: #2) → Pod 处于 ImagePullBackOff 并锁定在 Pending 状态 (Fact: #4)
```

### 根因结论

已确认根因为镜像仓库域名 `registry.invalid` 无法在集群 DNS (`127.0.0.53`) 中解析。
- **支撑依据**：K8s 事件日志 (`fact-59ee9d0371d7`) 明确记录了 DNS 解析失败错误。
- **排除项**：资源限制配置（CPU/Memory）和网络插件日志在现象中未表现出关联性；日志和追踪系统因容器未启动而无可观测数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.5s
├─ 并发证据采集: 39.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 39.3s (Evidence 31.1s, RCA 8.1s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed

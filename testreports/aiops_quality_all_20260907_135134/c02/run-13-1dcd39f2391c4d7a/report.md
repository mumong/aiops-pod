## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 中引用的镜像 registry 'registry.invalid' 为无效域名，导致节点在尝试解析该仓库地址时发生 DNS 查询失败（NXDOMAIN），镜像拉取流程从第一步即被阻断。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `waiting_reason`: "ImagePullBackOff" (container: app) | 确认容器因镜像拉取失败而处于等待状态 [fact-30dfe88db922] |
| 2 | K8s State | kubernetes | `waiting_message`: `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 明确指定导致失败的具体镜像源为无效域名 `registry.invalid` [fact-f7fac86e3ff7] |
| 3 | K8s State | kubernetes | `pod.phase`: "Pending"；`pod.condition`: ContainersReady/Ready 均为 `False` | 确认 Pod 未能推进至 Running 状态，符合镜像拉取失败的特征 [fact-33355b26e642], [fact-07e844b9d84a] |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 值为 "1"，标签 `reason="ImagePullBackOff"` | 从监控侧证实该 Pod 持续处于拉取等待状态 [fact-baae4dc4df65] |

**证据小结：**
Kubernetes API 直接报告了镜像拉取失败的具体原因（ImagePullBackOff），并提供了引发该错误的关键字（registry.invalid）。Prometheus 监控数据从另一个维度确认了这一状态，且该状态持续存在。资源请求（5m CPU/8Mi Mem）与拉取失败无因果关系，排除了资源调度层面的阻碍。

## 🎯 根因分析 · g1

### 因果链

```text
配置中引用无效域名镜像 'registry.invalid' → 节点 DNS 解析失败阻断拉取 → ImagePullBackOff → Pod 处于 Pending 状态，无法启动
```

### 根因结论

已确认根因为 Pod 配置中引用的容器镜像地址 `registry.invalid/aiops/workload:missing` 为无效域名。该无效域名导致节点在执行镜像拉取操作时遭遇 DNS 解析失败（NXDOMAIN），致使 Pod 被卡在 `ImagePullBackOff` 状态，进而表现为 `ContainersReady` 状态为 `False`。证据 [fact-30dfe88db922]、[fact-f7fac86e3ff7] 及 [fact-baae4dc4df65] 完整支撑了这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 29.1s
├─ 并发证据采集: 43.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 43.3s (Evidence 36.0s, RCA 7.1s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed

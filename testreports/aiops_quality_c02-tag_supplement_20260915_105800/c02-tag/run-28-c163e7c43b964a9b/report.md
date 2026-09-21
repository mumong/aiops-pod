## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 引用了不存在的镜像 tag 'aiops-fixture-unavailable-20260908'，导致 kubelet 拉取失败并陷入 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": ... not found` (fact-27b9dd33086f) | 确证镜像拉取失败的直接错误信息，镜像 tag 不存在 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `ImagePullBackOff`; `container.waiting_message`: `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (fact-8bcd77216303, fact-99742244fbe4) | 展示容器当前处于重试退避状态，原因指向同一缺失镜像 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: `1` (labels: `container="app", reason="ImagePullBackOff"`) (fact-07e0f604d9d6) | 从监控侧独立印证了 app 容器处于 ImagePullBackOff 状态 |
| 4 | K8s State | kubernetes | `pod.status`: `Pending`; `pod.phase`: `Pending` (fact-240a96ffb8ff, fact-547d32f7b69a) | 确认 Pod 因无法启动容器而处于未就绪阶段 |

上述 K8s 事件、容器状态及 Prometheus 指标共同印证了同一结论：Pod 无法启动是因为指定的镜像 tag 在远程仓库中不存在，导致拉取失败并持续重试。

## 🎯 根因分析 · g1

### 因果链
```text
Pod aiops-case-v07/workload 配置了不存在的镜像 tag 'aiops-fixture-unavailable-20260908' 
→ kubelet 拉取镜像时返回 registry 404 (not found) 
→ Pod 进入 ImagePullBackOff 状态并持续退避重试 
→ Pod 保持 Pending 状态，用户无法访问服务
```

### 根因结论
已确认根因：Pod `aiops-case-v07/workload` 引用了不存在的镜像 tag `aiops-fixture-unavailable-20260908`，导致 kubelet 拉取失败并陷入 `ImagePullBackOff`。

证据支撑：
- 事实 1 (`fact-27b9dd33086f`)：K8s Event 明确报告 `Failed to pull image ... not found`。
- 事实 2 (`fact-8bcd77216303`, `fact-99742244fbe4`)：容器状态为 `ImagePullBackOff`，且报错信息与 Event 一致。
- 事实 3 (`fact-07e0f604d9d6`)：Prometheus 指标 `kube_pod_container_status_waiting_reason` 独立观测到 `ImagePullBackOff` 值为 1。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.2s
├─ 并发证据采集: 32.6s
│  └─ g1 aiops-case-v07/workload: 32.6s (Evidence 27.2s, RCA 5.3s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

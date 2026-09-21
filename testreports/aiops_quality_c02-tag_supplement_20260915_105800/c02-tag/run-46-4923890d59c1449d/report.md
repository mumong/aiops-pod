## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod workload (aiops-case-v07)处于Pending和ImagePullBackOff状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v07/workload` 状态为 `Pending` (fact_id: fact-1a789db31154) | 确认 Pod 当前未运行，处于等待启动阶段 |
| 2 | K8s Event | Kubernetes | `Warning Failed ... Error: ErrImagePull` (fact_id: fact-d709d6c4af76) | 确认容器启动阶段发生镜像拉取错误 |
| 3 | K8s Event | Kubernetes | `Warning Failed ... failed to resolve reference "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": ... not found` (fact_id: fact-d7091bbe7d9f) | 提供决定性证据：特定镜像 tag 在远程仓库中不存在，直接指向根因 |
| 4 | K8s Event | Kubernetes | `Normal BackOff ... Back-off pulling image` (fact_id: fact-f33e62e6c27d) | 确认 kubelet 因连续失败已进入指数退避重试机制 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: `ImagePullBackOff`) (fact_id: fact-8f397004c3b9) | 指标数据与事件日志中的状态一致，确认 Pod 持续处于等待拉取镜像的阻塞状态 |
| 6 | K8s Config | Kubernetes | 容器 `app` 内存限制 `32Mi`，请求 `8Mi`；CPU 限制 `50m`，请求 `5m` (fact_id: fact-178c6731d02e, fact-36a217633987, fact-c6c37a6e55eb, fact-e4b1a26b6d38) | 提供资源约束上下文；虽非本次拉取失败主因，但排除了因资源不足导致启动被拒的可能性 |

证据 1 至 4 完整展示了从“镜像拉取失败 (ErrImagePull)”到“进入指数退避 (BackOff)”的 Kubernetes 生命周期行为，其中事实 #3 直接指出了失败的技术根源：目标镜像 tag `aiops-fixture-unavailable-20260908` 在阿里云容器镜像仓库中找不到。指标证据 5 独立证实了 Pod 当前仍处于 `ImagePullBackOff` 的阻塞状态。

## 🎯 根因分析 · g1

### 因果链

```text
目标镜像 tag 不存在于远程仓库 (registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908) 
→ kubelet 尝试拉取镜像并收到 NotFound 错误 (ErrImagePull) 
→ 镜像拉取失败触发指数退避重试 (Back-off pulling image) 
→ Pod 保持 Waiting/ImagePullBackOff 状态，应用无法启动
```

### 根因结论

**已确认根因：容器镜像缺失。**

Pod `aiops-case-v07/workload` 的 `ImagePullBackOff` 故障由 kubelet 无法在远程仓库中找到指定的镜像 tag `aiops-fixture-unavailable-20260908` 直接引起。证据 #3 明确记录了 `NotFound` 错误，证据 #4 记录了随后触发的退避行为，而证据 #5 证实了该状态持续存在。Pod 当前未运行且无重启记录，排除了启动后因 OOM 或其他运行时错误退出并反复重启的情况。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 20.5s
├─ 并发证据采集: 30.2s
│  └─ g1 aiops-case-v07/workload: 30.2s (Evidence 21.9s, RCA 8.2s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

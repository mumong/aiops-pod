## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 处于 ImagePullBackOff 状态，容器等待拉取镜像 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: ImagePullBackOff` (fact-2033b0f27b0d) | 确认 Pod 容器处于镜像拉取退避失败的最终状态 |
| 2 | K8s Event | kubernetes | `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (fact-e6c858781bbf) | 指明 kubelet 正在尝试拉取的具体镜像地址及镜像 Tag |
| 3 | K8s Event | kubernetes | `failed to resolve reference ... : not found` (fact-f50c6e32efb3) | 记录底层容器运行时返回的精确失败原因：镜像引用解析失败且未找到镜像 |
| 4 | K8s State | kubernetes | `container.waiting_reason: ImagePullBackOff` (fact-090380a95dee) | 确认容器应用 `app` 的等待原因为拉取镜像失败 |
| 5 | K8s State | kubernetes | `pod.status: Pending` (fact-830d276ee2d4) | 确认 Pod 整体调度与启动流程停滞 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason[reason="ImagePullBackOff"] = 1` (fact-7a254f68cee7) | 独立监控指标证实应用容器确实处于 ImagePullBackOff 状态 |

**证据印证：**
Kubernetes Event（#3）中容器运行时明确返回 `not found`，直接证实了镜像地址 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在仓库中不可用。该结果与 K8s Event（#1）及 Metric（#6）所观察到的 `ImagePullBackOff` 状态完全一致，共同指向镜像引用配置错误（Tag 不存在）是阻断 Pod 启动的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的镜像 Tag ('aiops-fixture-unavailable-20260908') → 容器运行时拉取镜像返回 'not found' 错误 → kubelet 持续重试并触发退避机制 (Back-off) → Pod 保持 ImagePullBackOff 状态无法启动
```

### 根因结论

已确认根因为：Pod 配置的镜像引用 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程仓库中不存在（Tag 错误或缺失）。

该配置错误导致 kubelet 在拉取容器镜像时遭到运行时返回 `not found` 错误。由于该镜像引用是硬性依赖且无法修正，kubelet 按预期进入指数退避重试策略（BackOff），导致应用容器（app）持续处于 `ImagePullBackOff` 状态，Pod 维持在 `Pending` 状态，无法分配资源及挂载网络，服务因此不可用。

*   支撑证据：Fact #3 提供了底层失败的原始事实（not found），Fact #2 提供了具体失败的镜像引用，Fact #1、#4 和 #6 分别从事件、容器状态和监控指标三个维度确认了由此产生的 `ImagePullBackOff` 症状。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.6s
├─ 并发证据采集: 44.4s
│  └─ g1 aiops-case-v07/workload: 44.4s (Evidence 34.2s, RCA 10.1s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

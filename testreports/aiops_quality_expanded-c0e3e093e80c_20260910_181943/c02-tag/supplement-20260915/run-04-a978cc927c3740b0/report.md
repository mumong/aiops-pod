## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: "ImagePullBackOff" | 直接表征 `app` 容器当前处于拉取镜像等待状态 |
| 2 | K8s State | kubernetes | `pod.phase`: "Pending" | 反映 Pod 因容器未就绪而卡在初始化阶段 |
| 3 | K8s State | kubernetes | `container.waiting_message`: "Back-off pulling image..." | 确认失败的具体镜像标识 |
| 4 | K8s Event | kubernetes | `Failed to pull image... rpc error: code = NotFound desc = failed to resolve reference... not found` | 记录 kubelet 拉取失败的系统级错误日志，明确报错为 404 NotFound |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: `1` (label: `reason=ImagePullBackOff`) | 量化指标验证当前存在一个处于该状态的容器 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total`: `0` | 排除由于 CrashLoopBackOff 或 OOM 导致的高频重启，进一步支持镜像拉取阶段失败 |

**证据关联：**
证据 1-4 从 K8s 内部状态、事件日志和时间推移（Back-off）三个维度相互印证，统一指向镜像拉取失败；证据 5-6 提供了独立的指标视图，证实了拉取失败状态的存在且排除了运行时的重启干扰。K8s 事件中的 `NotFound` 错误与指标中的 `ImagePullBackOff` 状态逻辑完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod manifest 引用不存在的镜像 tag → Registry 返回 NotFound (404) 错误 → kubelet 持续 ImagePull 失败 → 容器状态转为 ImagePullBackOff，Pod 保持 Pending
```

### 根因结论

已确认的根因为：Pod 的容器配置中引用的镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程仓库中不存在。

Kubelet 在尝试拉取该镜像时，Registry 返回了明确的 `NotFound` 错误（见证据 4），导致拉取动作失败。随后 kubelet 进入指数退避（Back-off）重试机制，表现为 `ImagePullBackOff` 状态（见证据 1、3、5）。该故障完全由镜像标签错误或仓库资源不可用引起，与计算资源（见事实 `fact-14695e989e0f`）或网络插件（见事实 `fact-ad50ccc92018`）无关。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.2s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-v07/workload: 41.5s (Evidence 32.2s, RCA 9.2s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

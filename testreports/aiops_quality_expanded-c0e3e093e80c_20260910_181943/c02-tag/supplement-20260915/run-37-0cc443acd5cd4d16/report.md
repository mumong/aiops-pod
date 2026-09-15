## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Error: ErrImagePull` | 确认 Kubelet 初次拉取镜像时即报错 |
| 2 | K8s Event | Kubernetes | `Error: ImagePullBackOff` | 确认系统已对持续失败的拉取动作实施指数退避 |
| 3 | K8s Event | Kubernetes | `rpc error: code = NotFound desc = ... registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908: not found` | 明确错误根源：镜像仓库中不存在指定标签的镜像 |
| 4 | K8s Config | Kubernetes | `resource_limit.memory=32Mi, resource_request.cpu=5m` | 排除资源不足导致的 OOM 或调度失败 |
| 5 | K8s State | Kubernetes | `pod.status="Pending", restart_count=0` | 确认 Pod 处于等待镜像的初始化阶段，且无成功启动过的迹象 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason="ImagePullBackOff"` (fact-id: fact-cb52d4313032) | 监控维度确认容器当前状态确认为镜像拉取失败 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total=0` (fact-id: fact-3a577e7c53c5) | 确认容器未发生过任何运行后重启，与“从未成功拉取镜像”一致 |

**证据印证说明：**
- 维度 3 的 K8s 原始事件日志直接给出了 `NotFound` 错误详情，这是确认根因的核心硬证据。
- 维度 5 的状态（Pending, 0 restarts）与维度 6 的指标（ImagePullBackOff）在现象上高度一致，排除了“启动后崩溃（CrashLoopBackOff）”的可能性。
- 维度 7 明确证实了容器从未有过存活周期，排除了“镜像曾成功拉取但仓库随后删除了该版本”的短期故障可能，指向配置或版本管理的持久性错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 清单引用了不存在的镜像版本 (aiops-fixture-unavailable-20260908) 
  → Kubelet 拉取该标签时仓库返回 NotFound 错误 
  → 镜像拉取持续失败触发 BackOff 机制 
  → Pod 停留在 Pending/ImagePullBackOff 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v07/workload` 无法启动的直接原因是其指定的容器镜像标签 `aiops-fixture-unavailable-20260908` 在镜像仓库 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause` 中不存在。

证据编号 3（K8s Event）中的 `NotFound` 错误原文是决定性证据，证实了镜像仓库层面拒绝拉取。结合证据编号 1、2（持续重试与 BackOff）以及证据编号 6、7（监控指标确认等待原因且无重启记录），所有数据一致指向“镜像不存在”这一事实，排除了网络、鉴权或资源配额等其他常见的拉取失败原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.2s
├─ 并发证据采集: 38.5s
│  └─ g1 aiops-case-v07/workload: 38.5s (Evidence 27.3s, RCA 11.1s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 状态 `Pending`；`Ready=False`；等待原因 `ImagePullBackOff`；等待消息提示“Back-off pulling image 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908'” (`fact-7da615da4875`, `fact-e55bfe293727`, `fact-31ff7030bec0`) | 确认 Pod 因镜像拉取失败而阻塞，未进入运行阶段 |
| 2 | K8s Event | Kubernetes | 容器重启次数 `0` (`fact-35acfab42b00`) | 证实镜像拉取在启动前即被阻断，非启动后崩溃 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (Reason=`ImagePullBackOff`)；`kube_pod_container_status_restarts_total=0` (`fact-76930fe60e1a`, `fact-5324c43fdeb2`) | 独立观测确认 Pod 持续处于拉取退避状态，且无历史重启记录 |
| 4 | K8s Config | Kubernetes | 容器 `app` 配置了 CPU `5m/50m` 与 Memory `8Mi/32Mi` (`fact-330b8f889a6a`, `fact-743f74909d75`, `fact-748dafb38eef`, `fact-ba1f46bec0b1`) | 提供基础资源上下文，资源限制并非拉取失败的直接诱因 |

**证据印证说明：**
- 证据 1（K8s State）中的 `ImagePullBackOff` 与证据 3（Metric）中的 `waiting_reason` 相互印证，确认拉取失败的持续状态。
- 证据 1 中的 `Pending` 状态结合证据 2（重启次数 0），锁定了故障发生在调度后、容器启动前阶段。
- 无有效日志与 Tracing，因为容器物理上未能启动（证据 1），故日志/追踪维度的缺失符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 tag 'aiops-fixture-unavailable-20260908' 不存在于仓库 → Kubelet 拉取镜像返回 NotFound → 容器启动失败并触发退避机制 → Pod 处于 ImagePullBackOff 状态
```

### 根因结论

**根因：容器镜像标签不存在导致拉取失败。**

Kubernetes 集群尝试从 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause` 拉取标签为 `aiops-fixture-unavailable-20260908` 的镜像失败。Kubelet 在拉取失败后进入退避（Back-off）重试逻辑，导致 Pod 处于 `ImagePullBackOff` 状态并永远无法运行。

支撑事实：
- 事实 `fact-7da615da4875`：直接报告了拉取失败的镜像地址与具体的 tag，以及 `Back-off pulling image` 的机制。
- 事实 `fact-e55bfe293727`：确认了 Kubernetes 层面的异常原因为 `ImagePullBackOff`。
- 事实 `fact-76930fe60e1a`：Metric 维度独立确认了处于 `ImagePullBackOff` 状态的 Pod。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.6s
├─ 并发证据采集: 43.3s
│  └─ g1 aiops-case-v07/workload: 43.3s (Evidence 34.5s, RCA 8.7s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

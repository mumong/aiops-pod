## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 处于 Pending 状态，容器因 ImagePullBackOff 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod aiops-case-v07/workload 状态为 Pending；容器 app 处于 ImagePullBackOff 状态，容器未就绪 | 定义异常现象 |
| 2 | K8s Event | Kubernetes | 44m 内重复出现：`Warning Failed ... Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": ... not found` | 证实拉取失败的具体镜像与错误原因 |
| 3 | K8s Event | Kubernetes | 41s 内持续触发 `Normal BackOff ... Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 证实系统已持续退避，异常未自愈 |
| 4 | Metric | Prometheus | 容器 `app` 的 `kube_pod_container_status_waiting_reason=1`，标签 `reason="ImagePullBackOff"`，当前值 1 | 从监控维度印证容器因镜像拉取失败处于等待状态 |

**证据总结：**
K8s 事件日志明确记录了 Registry 返回 `NotFound`，确认镜像 `aiops-fixture-unavailable-20260908` 不存在；K8s 状态与 Metric 共同反映了由此导致的持续等待和退避。资源配置（CPU/Memory）与异常无关。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 tag 不存在于远程仓库 (registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908)
→ kubelet 执行拉取时 registry 返回 NotFound 错误
→ 容器进入 ImagePullBackOff 状态并持续退避
→ Pod 保持 Pending 状态，无法启动
```

### 根因结论

已确认根因：Pod 配置的镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在镜像仓库中不存在。

该根因得到了 K8s 事件日志（`fact-20486734ad79`）中 `Failed to pull image` 及 `not found` 的直接证实，以及 K8s 状态（`fact-689e29562d62`）和监控数据（`fact-a2c4075faa7d`）的交叉印证。证据充分，无需补充其他维度的决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.4s
├─ 并发证据采集: 32.4s
│  └─ g1 aiops-case-v07/workload: 32.4s (Evidence 24.8s, RCA 7.5s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

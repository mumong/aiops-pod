## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod 引用的镜像 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908' 在远程仓库中不存在（NotFound），导致 kubelet 拉取失败并进入 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Pending`, `container.waiting_reason: ImagePullBackOff` | 明确异常实体状态与容器等待原因 |
| 2 | K8s Event | kubernetes | `rpc error: code = NotFound desc = failed to pull ... image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": not found` | 提供镜像拉取失败的根本错误信息 |
| 3 | K8s Event | kubernetes | `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 证实 kubelet 正在对同一镜像进行指数退避重试 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 从监控维度印证容器当前处于 ImagePullBackOff 状态 |
| 5 | K8s State | kubernetes | `pod.condition: Ready=False (ContainersNotReady)`, `container.restart_count: 0` | 排除因资源不足导致的调度失败或容器启动后崩溃（CrashLoopBackOff） |

**证据关联与冲突说明**：
K8s Event 提供了具体的错误代码 `NotFound`，直接锁定了问题在于远程仓库镜像缺失，而非网络或凭证问题。Metric 数据与 K8s 状态严格一致，确认了 `ImagePullBackOff` 是当前的稳定状态。由于 Pod 未成功启动，Logging 和 Tracing 维度显示 `not_applicable`，这符合“镜像不存在导致容器未运行”的物理事实，无矛盾。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用的镜像不存在于仓库 → kubelet 拉取镜像失败(code=NotFound) → Pod 进入 ImagePullBackOff 状态 → 容器无法启动(Pending)
```

### 根因结论

**已确认的根因**：Pod 引用的镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在远程仓库中不存在。

**证据支撑**：
1. **直接证据**：K8s Event（证据 #2）明确指出拉取请求返回了 `NotFound` 错误，证明该特定标签的镜像在仓库中确实缺失。
2. **状态印证**：K8s State（证据 #1）显示容器处于 `ImagePullBackOff`，且 Metric（证据 #4）从监控侧确认了该状态，排除了其他等待原因。
3. **现象吻合**：Pod 始终处于 `Pending` 且重启次数为 0（证据 #5），符合因镜像不可达而从未进入运行阶段的特征。

现有证据已充分支持该根因，无需额外排查。

---

## 📊 性能统计

```text
├─ 总耗时: 57.8s
├─ 问题定位: 19.0s
├─ 并发证据采集: 28.8s
│  └─ g1 aiops-case-v07/workload: 28.8s (Evidence 24.4s, RCA 4.3s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

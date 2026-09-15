## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod配置了不存在的镜像Tag (aiops-fixture-unavailable-20260908) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.waiting_reason` | `ImagePullBackOff` | 确定容器当前处于拉取镜像失败后的退避等待状态 |
| 2 | K8s Event | `event.message` | `Error: ErrImagePull`、`Failed to pull image ... pause:aiops-fixture-unavailable-20260908: not found` | 明确指出具体的失败镜像及 Tag，确认底层错误为“不存在” |
| 3 | K8s Config | `container.waiting_message` | `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 展示 kubelet 正在对缺失镜像进行指数退避重试 |
| 4 | Metric | `kube_pod_container_status_waiting_reason` | `reason="ErrImagePull"`, value=`1` | 从监控层面佐证容器正处于因镜像拉取错误导致的等待状态 |

**证据关联说明：**
事实 #2（K8s Event）提供了最直接的诊断依据，错误原文 `not found` 确认了镜像 Tag `aiops-fixture-unavailable-20260908` 在远程仓库中不存在。该事实与事实 #1（K8s State）的 `ImagePullBackOff` 状态完全对应，事实 #4（Metric）提供了同一状态的独立监控验证。由于容器未能启动，Logging 和 Tracing 维度标记为 `not_applicable`，无相关证据可查。

## 🎯 根因分析 · g1

### 因果链

```text
配置了不存在的镜像Tag → 镜像拉取失败(NotFound) → 容器进入Waiting(ImagePullBackOff) → Pod无法启动且状态为Pending
```

### 根因结论

已确认根因：Pod `aiops-case-v07/workload` 的 `app` 容器配置了无效的镜像 Tag `aiops-fixture-unavailable-20260908`。

该配置直接导致 kubelet 拉取镜像时遭遇 `NotFound` 错误，随后容器状态转为 `ImagePullBackOff` 并持续重试，最终表现为 Pod 处于 `Pending` 状态且不可用。证据 #2 的错误原文与证据 #1 的状态变化共同支撑了这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 57.3s
├─ 问题定位: 16.6s
├─ 并发证据采集: 32.5s
│  └─ g1 aiops-case-v07/workload: 32.5s (Evidence 26.5s, RCA 5.9s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

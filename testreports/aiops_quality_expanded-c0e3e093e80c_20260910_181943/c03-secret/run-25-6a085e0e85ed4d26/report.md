## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | 1 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container: app) = 1, reason: ContainerCreating | 确认容器处于等待状态，且原因与镜像拉取过程直接相关 |
| 2 | Metric | prometheus | `kube_pod_container_status_restarts_total` (container: app) = 0 | 排除容器因配置错误或应用崩溃导致的反复重启 |
| 3 | Metric | prometheus | `kube_pod_status_phase` (container: kube-state-metrics) = Pending | 佐证目标 Pod 未进入运行状态 |

**证据说明：**
Metric 数据表明 `app` 容器长期处于 `ContainerCreating` 状态且重启次数为 0，这排除了应用逻辑错误，将故障现象锁定在镜像拉取（Pulling）或容器环境初始化的阻塞阶段。由于 Metric 样本量为 1 且未检测到状态变化，无法确认拉取是处于持续尝试中还是已经失败，需结合 K8s 状态验证，但输入中该维度缺失，导致现象描述仅停留在“等待”层面。

## 🎯 根因分析 · g1

### 因果链

```text
镜像拉取过程受阻 → kubelet 持续执行 Pulling 动作 → 容器未创建成功，Pod 保持 Pending/ContainerCreating 状态 → 用户可见应用不可用
```

### 根因结论

证据不足。

现有事实确认了 Pod 处于“因镜像拉取受阻而等待”的现象状态（Metric 1, 2, 3），且已知 RCA 的绑定和发布校验被配置禁用。但是，由于缺乏 K8s Events 中的具体 Pull 错误描述（如 `ErrImagePull` 或 `ImagePullBackOff` 的确切信息），Metric 也未能提供随时间推移的拉取行为样本（trend_evaluable=false），无法区分导致拉取受阻的根本原因是网络超时、认证失败、镜像不存在还是证书错误。缺少决定性的错误码或事件记录，无法发布正式根因。

---

## 📊 性能统计

```text
├─ 总耗时: 56.5s
├─ 问题定位: 18.9s
├─ 并发证据采集: 30.7s
│  └─ g1 aiops-case-v04/workload: 30.7s (Evidence 19.3s, RCA 11.3s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-config-error

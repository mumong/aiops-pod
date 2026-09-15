## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 处于 ContainerCreating/Pending 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `Pending` (fact-2b2901e622c9) | 确认 Pod 处于调度完成但未运行状态 |
| 2 | K8s Event | FailedMount | `timed out waiting for the condition` (fact-aa5f973f3484) | 记录容器因卷挂载超时而阻塞 |
| 3 | K8s Event | FailedMount | `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` (fact-b4e4c85a2ecf) | 证实挂载失败的具体原因是目标路径类型校验失败 |
| 4 | K8s Config | Resource Request | Memory `8Mi`, CPU `5m` (fact-2c63bc450a36) | 资源申请极低，排除资源不足导致无法调度的可能性 |
| 5 | K8s Config | Resource Limit | Memory `32Mi`, CPU `50m` (fact-6c0a41aa5d72) | 资源配置符合预期，非资源限制瓶颈 |
| 6 | Metric | Waiting Reason | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-5165e15dd3e9) | 独立确认 Pod 卡在创建阶段，无重启 (restarts=0, fact-00a06a53ba61) |

**证据链逻辑：**
Pod 被调度至节点但无法启动（证据 1），Prometheus 指标独立证实了 ContainerCreating 状态（证据 6）。核心矛盾在于卷挂载：日志与事件显示挂载 `input` 卷失败，且 kubelet 明确返回了 `hostPath type check failed`，指认 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是一个有效的目录（证据 2、3）。资源请求极低（证据 4、5）排除了集群资源不足导致的调度或运行阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 的 HostPath volume 'input' 指向节点上不存在或路径类型不匹配 (not a directory) → Node2 kubelet MountVolume.SetUp 执行失败 → 挂载超时导致 Pod 持续处于 Pending 状态 → 用户可见 Pod 卡在 ContainerCreating
```

### 根因结论

**已确认根因：**
`Pod aiops-case-v06/workload` 启动失败是由于其定义的 `input` HostPath 卷挂载失败（证据 3）。Node 上的挂载点 `volume` `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在节点文件系统中不是一个有效的目录，导致 kubelet 挂载阻塞并超时（证据 2、3）。Pod 未能进入容器启动阶段，因此无日志和 Trace（证据 6）。

**排除项：**
- 集群资源充足：资源请求极低（8Mi/5m），且 Pod 已调度，非资源争用导致。
- 容器应用异常：重启计数为 0，说明容器甚至未启动。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 22.5s
├─ 并发证据采集: 557.1s
│  └─ g1 aiops-case-v06/workload: 557.1s (Evidence 550.4s, RCA 6.7s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed

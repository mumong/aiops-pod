## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod spec 中 volume `input` 引用了不存在的 ConfigMap `unavailable-config`（Optional=false），导致 kubelet 挂载失败，Pod 持续卡在 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | event | `FailedMount` 18m (x23 over 48m)：`MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 确认为根本原因；明确指出了缺失的配置资源名称及挂载卷名称 |
| 2 | K8s Event | event | `FailedMount` 3m36s (x20 over 46m)：`timed out waiting for the condition` | 佐证挂载操作因底层依赖（ConfigMap）失败而导致的持续重试与超时现象 |
| 3 | K8s State | pod.phase | `Pending` (fact-ae391bf9283d) | 确认 Pod 当前停滞状态，未进入运行阶段 |
| 4 | K8s State | pod.condition | `ContainersReady=False, reason=ContainersNotReady` (fact-dbc753d8e5d9) | 确认容器就绪检查失败，是挂载失败的直接下游结果 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason`=1, labels={container: app, reason: ContainerCreating} (fact-f4ec3b2ffc3b) | 与 K8s 状态事实 `ContainerCreating` 交叉验证，确认容器持续处于等待挂载或初始化阶段 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total`=0 (fact-99e9c5751ab7) | 证明容器从未成功启动，排除了应用崩溃重启导致挂载失败的可能 |
| 7 | K8s Config | container.resource_limit | memory: 32Mi, cpu: 50m | 确认资源配置极小，进一步排除因资源不足（OOMKill/Throttling）导致容器启动受阻的可能 |

**证据分析说明：**
K8s Event 1 和 2 提供了最直接的故障机理（ConfigMap 缺失导致 Mount 失败），这与 Event 的长周期重复出现（48m 内发生 43 次）相符，解释了 Pod 为何长期处于 `Pending` 且无法自动恢复。Metric 5 中的 `ContainerCreating` 原因与 K8s Event 的挂载失败直接对应，Metric 6 中重启次数为 0 确认了应用侧未产生任何生命周期事件。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 声明了不存在的 ConfigMap "unavailable-config" (Optional=false) → kubelet 执行 volume mount 时查找失败 → Pod 卡在 ContainerCreating/Pending 状态，无法拉起容器 → 集群中该 Pod 长期不可用，伴随大量 Mount 超时日志
```

### 根因结论

**已确认根因：Pod `aiops-case-03/workload-5b5fc86c8c-2xgjz` 的 Spec 配置错误。**

Pod 的 Spec 中定义了一个名为 `input` 的 Volume，该 Volume 指向一个名为 `unavailable-config` 的 ConfigMap，且该引用未被标记为 `Optional=true`。由于该 ConfigMap 在 `aiops-case-03` 命名空间中实际不存在，kubelet 在挂载卷时触发 `FailedMount` 错误。

**证据支撑：**
- 诊断结论由 **K8s Event** 中的 `MountVolume.SetUp failed ... configmap "unavailable-config" not found` (fact-2db7e3c50ed4, fact-a315f4c5a1c6) 直接证实。
- Pod 的停滞状态 `Pending` (fact-ae391bf9283d) 及 `ContainersReady=False` (fact-dbc753d8e5d9) 是挂载失败后的标准响应。
- 指标显示容器从未启动（重启 0 次，fact-99e9c5751ab7），且等待原因为 `ContainerCreating` (fact-f4ec3b2ffc3b)，排除了应用逻辑错误或资源限制（fact-7c9ddac29465）等干扰因素。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.4s
├─ 并发证据采集: 30.5s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 30.5s (Evidence 26.9s, RCA 3.5s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-config-error

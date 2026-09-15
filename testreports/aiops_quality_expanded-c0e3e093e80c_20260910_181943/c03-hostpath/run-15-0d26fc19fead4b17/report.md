## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 卡在 ContainerCreating 阶段，处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-v06/workload` | 状态 `Pending`, 阶段 `Pending`, 容器 `app` 等待原因 `ContainerCreating` | 确认当前症状：Pod 卡在启动前的挂载准备阶段，未进入运行状态 |
| 2 | K8s Event | kubelet | `FailedMount`: "MountVolume.SetUp failed for volume \"input\" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory" | **直接证据**：明确指出主机路径存在类型检查失败，这是导致挂载失败的直接原因 |
| 3 | K8s Event | kubelet | `FailedMount`: "timed out waiting for the condition" (x16 over 17m) | 佐证事件：挂载操作在长达 17 分钟内持续失败，排除了偶发性网络或短暂资源争用 |
| 4 | K8s Config | Pod Spec | Volume `input` 类型 `hostPath`, 配置路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` | 提供故障上下文，确认可疑配置对象 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=`ContainerCreating`, value=`1`) | 量化确认等待状态，与 K8s State 中的 `ContainerCreating` 状态一致 |
| 6 | Metric | Prometheus | `kube_pod_status_phase` (phase=`Pending`, value=`1`) | 量化确认调度状态，排除 Pod 被调度到节点后启动失败（Running->CrashLoopBackOff）的可能性 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (value=`0`) | 排除容器反复启动失败的干扰，确认问题发生在容器启动之前 |

**证据印证说明：**
- 证据 1、4、5、6 共同构建了一个闭环状态：Pod 被调度（Phase Pending），配置了 hostPath（Config），但由于无法完成挂载（State/Waiting Reason），导致容器无法启动。
- 证据 2 是决定性证据，其指出的 `hostPath type check failed` 完美解释了证据 1 中 `ContainerCreating` 的停滞原因，以及证据 3 中长时间的 `timed out` 现象。
- 日志与 Tracing 维度（Logging/Tracing）因 Pod 物理上未能启动且 IP 为空，未采集到相关数据，不影响基于 K8s 控制面与节点日志的诊断结论。

## 🎯 根因分析 · g1

### 因果链

```text
Node 'node2' 上的 hostPath '/var/lib/aiops-fixture-unavailable-7f394bef/input' 不存在或类型非目录 → 
Kubelet 执行 MountVolume.SetUp 失败，触发 hostPath type check failed 警告 → 
Pod volume 挂载超时，触发 FailedMount 事件，Pod 保持在 Pending 状态 → 
容器维持在 ContainerCreating 等待状态，用户无法访问应用
```

### 根因结论

**已确认根因：Pod Spec 中配置的 hostPath volume 'input' 路径挂载失败。**

具体而言，Kubelet 在节点 `node2` 上尝试挂载主机路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 时，检测发现该路径**不存在**或者**其文件类型不是目录**（`is not a directory`）。这一底层文件系统状态的不匹配导致 `MountVolume.SetUp` 操作持续报错（证据 2），进而导致 Pod 无法完成卷挂载和容器初始化，表现为长期处于 `Pending` 和 `ContainerCreating` 状态（证据 1、5、6）。

**关键证据引用：**
- 证据 2 提供了最直接的故障机制描述。
- 证据 1 和 5 描述了该机制导致的结果状态。
- 证据 4 指明了具体的故障配置项。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 42.8s
├─ 并发证据采集: 38.6s
│  └─ g1 aiops-case-v06/workload: 38.6s (Evidence 29.7s, RCA 8.8s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed

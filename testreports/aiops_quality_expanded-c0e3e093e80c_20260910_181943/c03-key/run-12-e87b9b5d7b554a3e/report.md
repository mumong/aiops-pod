## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 定义中挂载的 ConfigMap 'workload-input' 缺少所需的 key 'unavailable-key'，导致 Volume 挂载失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 直接定位 Volume 挂载失败的精确原因：ConfigMap 缺少指定 key |
| 2 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` | 确认容器因挂载受阻处于等待启动状态 |
| 3 | K8s State | kubernetes | `pod.phase: Pending` | 佐证 Pod 未进入运行阶段 |
| 4 | K8s Event | kubernetes | `Warning FailedMount ... timed out waiting for the condition` | 辅助说明挂载重试与超时等待过程 |
| 5 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi, cpu: 5m` | 排除调度资源不足导致的挂载延迟 |
| 6 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi, cpu: 50m` | 排除资源限额配置异常 |
| 7 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 与 K8s 状态一致，确认 Pod 持续处于等待阶段 |
| 8 | Metric | prometheus | `kube_pod_container_status_restarts_total = 0` | 确认容器从未启动，无重启循环现象 |

上述证据形成完整闭环：K8s 状态与 Metric 共同确认了 `ContainerCreating` 的持久化等待现象，而 `FailedMount` 事件精确指出了该现象是由 `ConfigMap 'workload-input'` 中缺失 key `'unavailable-key'` 引起的。资源请求与限制配置正常，排除了资源层面的干扰因素。日志与追踪数据不适用，因容器未能启动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 挂载 ConfigMap 'workload-input' 的 key 'unavailable-key' → Kubelet 校验失败，Volume 挂载受阻 → MountVolume.SetUp 报错并持续重试 → Pod 状态卡在 ContainerCreating
```

### 根因结论

已确认根因：Pod `aiops-case-v05/workload` 定义中挂载的 ConfigMap `workload-input` 中缺失所需的 key `unavailable-key`，且该 key 未被标记为 `Optional`，导致 Kubelet 无法完成 Volume 挂载。

依据：
- 证据 1 显示 Kubelet 明确报告 `configmap references non-existent config key: unavailable-key`，直接指向配置缺失；
- 证据 2、3、7 显示 Pod 持续处于 `ContainerCreating` / `Pending` 状态，与挂载失败导致的阻塞行为一致；
- 证据 8 表明容器未运行过，排除应用侧错误。

现有证据已足够明确，无需补充日志或追踪数据即可定论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 23.0s
├─ 并发证据采集: 32.9s
│  └─ g1 aiops-case-v05/workload: 32.9s (Evidence 27.0s, RCA 5.8s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 Pending / ContainerCreating 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount` (x17): `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 核心证据：明确指明 ConfigMap key 缺失导致挂载失败 |
| 2 | K8s Event | kubernetes | `FailedMount` (x8): `Unable to attach or mount volumes: unmounted volumes=[input]` | 辅助证据：确认 volume `input` 挂载失败的状态及重试频率 |
| 3 | K8s State | kubernetes | `pod.phase`: Pending; `container.waiting_reason`: `ContainerCreating` (container: app) | 症状确认：Pod 卡在启动阶段，等待容器创建 |
| 4 | K8s State | kubernetes | `pod.condition`: `Ready=False`, `ContainersReady=False` (reason: ContainersNotReady) | 症状确认：容器未能进入就绪状态 |
| 5 | K8s Config | kubernetes | `container.resource_request`: CPU `5m`, Memory `8Mi`; `resource_limit`: CPU `50m`, Memory `32Mi` | 上下文：排除资源请求/限制不足的调度问题 |

证据 1 与证据 2 在时间线上相互印证（均在 18 分钟内持续发生），明确指向 `input` 卷的挂载错误。证据 3 和 4 证实了 Pod 处于因挂载失败而阻塞的 `Pending/ContainerCreating` 状态，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义 ConfigMap Volume 'input' 引用 key 'unavailable-key' → ConfigMap 中实际缺少该 key → MountVolume.SetUp 失败 (configmap references non-existent config key) → Pod 卡在 ContainerCreating 状态，用户无法使用应用
```

### 根因结论

**已确认的根因**：Pod 定义的 ConfigMap volume `input` 引用了不存在的 key `unavailable-key`，导致 kubelet 挂载卷失败。
- **证据支撑**：
  - `fact-a0920ce02edb` 明确记录 `configmap references non-existent config key: unavailable-key`，直接证实配置引用错误。
  - `fact-f23d5dd05883` 和 `fact-098ec4343227` 显示 Pod 处于 `ContainerCreating` 和 `Pending` 状态，与卷挂载失败后的预期行为一致。
  - `fact-3b016f31afd6` 显示 `restart_count` 为 0，排除应用崩溃重启因素。
- 现有证据充足，无需更多决定性事实即可确认根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 49.6s
├─ 并发证据采集: 42.7s
│  └─ g1 aiops-case-v05/workload: 42.7s (Evidence 34.8s, RCA 7.8s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed

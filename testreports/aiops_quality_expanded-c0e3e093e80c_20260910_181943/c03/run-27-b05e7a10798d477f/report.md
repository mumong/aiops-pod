## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod 定义中引用了不存在的 ConfigMap 'unavailable-config' 作为 volume 'input'，且未标记为 Optional，导致 kubelet 挂载失败并持续重试。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | phase: Pending | 呈现 Pod 停滞在调度/挂载阶段的宏观异常状态 |
| 2 | K8s Event | kubelet.mount | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接指明 `input` 挂载卷因配置缺失导致的失败事实 |
| 3 | K8s Event | kubelet.mount | `Timed out waiting for the condition` (持续重试) | 证明挂载失败是周期性触发的持续故障，非瞬时异常 |
| 4 | Metric | kube_pod_container_status_waiting_reason | 值为 1 (ContainerCreating, app 容器) | 确认容器处于等待挂载资源的阻塞态 |

**证据链说明：**
`fact-7ca5bc9fab99` 提供的真实错误原因（ConfigMap 不存在）解释了 Pod 处于 `Pending` 状态（`fact-6afbd6cfb5b9`）的直接机制；`fact-80f218f7cbdd` 的超时重试与 Metric 中 `ContainerCreating` 状态的长期维持（`fact-f7efe0c24747`）相互印证，排除了偶发性网络延迟，锁定为资源定义本身的硬阻断。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用不存在的 ConfigMap 'unavailable-config' (未标记 Optional) 
  → kubelet 挂载卷 "input" 时因找不到配置对象而持续失败 
  → Pod 持续重试挂载导致 ContainerCreating 超时未就绪 
  → Pod 处于 Pending 状态且应用不可用
```

### 根因结论

**已确认根因：**
Pod 定义中引用了不存在的 ConfigMap `unavailable-config` 作为 `input` 卷，且未设置 Optional 标记，导致 kubelet 无法完成卷挂载（支持证据：`fact-7ca5bc9fab99`, `fact-80f218f7cbdd`, `fact-f7efe0c24747`）。这一挂载阻塞直接导致 Pod 处于 Pending 状态，无法进入运行模式。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 44.9s
├─ 并发证据采集: 28.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 28.6s (Evidence 23.9s, RCA 4.6s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-imagepull-failed

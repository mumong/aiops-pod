## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 ContainerCreating / Pending 状态，长时间无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `phase: Pending`, `container.waiting_reason: ContainerCreating` | 确认 Pod 处于启动阻塞状态，未进入 Running。 |
| 2 | K8s Event | kubernetes | `FailedMount` (x48 over 83m) `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接锁定挂载失败的具体资源与错误原因。 |
| 3 | K8s Event | kubernetes | `FailedMount` (x31 over 80m) `Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` | 佐证卷挂载操作长期超时，确认挂载流程完全停滞。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (reason: `ContainerCreating`) | 独立确认当前容器处于挂载/启动等待阶段。 |
| 5 | K8s Config | kubernetes | `volume "input"` 指向配置 (隐含事实：引用不存在对象) | 解释为何 Kubelet 在挂载卷 `input` 时发生阻塞。 |

**证据分析**
Kubernetes 事件（#2, #3）明确指向 `configmap "unavailable-config"` 不存在导致挂载失败，且伴随长时间的超时重试。指标数据（#4）与 Pod 状态（#1）一致，证实容器未因资源不足重启，而是卡在初始化阶段。Logging 与 Tracing 维度因 Pod 无法启动且工具查询被限，未能提供额外线索，但不影响 K8s 层面事实的充分性。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → Kubelet 尝试挂载 Volume 'input' 失败并持续重试 → 容器沙箱创建阻塞 → Pod 状态卡死在 Pending/ContainerCreating
```

### 根因结论
已确认根因：**Pod 定义的 Volume 'input' 引用了不存在的 ConfigMap 'unavailable-config'**。
该配置缺失直接导致 Kubelet 执行 `MountVolume.SetUp` 时失败，并因持续重试（事件 #2, #3）使容器无限期阻塞在 `ContainerCreating` 状态。证据链充分，无需进一步排查。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 61.1s
├─ 并发证据采集: 57.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 57.5s (Evidence 49.1s, RCA 8.3s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 处于 Pending / ContainerCreating 状态，无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount 42s (x4 over 7m32s) kubelet Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 描述挂载卷超时失败的现象 |
| 2 | K8s Event | kubernetes | `FailedMount 81s (x12 over 9m35s) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接定位根本原因：ConfigMap不存在 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (labels: `container="app", reason="ContainerCreating"`) | 确认应用容器卡在等待创建状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (labels: `container="app"`) | 排除容器启动后崩溃或 OOM 导致重启的可能性 |

**证据说明：**
- Kubernetes 事件（第1、2条）直接揭示了挂载失败的根本原因（ConfigMap 缺失）和具体症状（超时），事件1反映了持续的现象，事件2提供了根因。
- Metric（第3条）证实了容器处于 `ContainerCreating` 状态，与事件中的挂载失败现象一致。
- Metric（第4条）确认重启次数为0，排除了容器已启动但崩溃重启的场景。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用不存在的 ConfigMap 'unavailable-config' (fact-2, fact-c2d599d0b767) 
→ kubelet 执行 MountVolume.SetUp 失败 (fact-2, fact-c2d599d0b767) 
→ Volume 'input' 挂载超时，Pod 状态保持 Pending/ContainerCreating (fact-1, fact-6efc3dc14f71, fact-0e6d056e26d7)
```

### 根因结论

Pod `workload-5b5fc86c8c-2xgjz` 的 Spec 中引用了不存在的 ConfigMap `unavailable-config`（事实编号 `fact-c2d599d0b767`），导致 `kubelet` 在尝试挂载名为 `input` 的卷时失败。该挂载失败引发后续的挂载超时（事实编号 `fact-6efc3dc14f71`），最终容器无法创建，Pod 持续处于 `ContainerCreating` / `Pending` 状态。现有证据已充分证实该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 59.9s
├─ 问题定位: 15.9s
├─ 并发证据采集: 34.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 34.9s (Evidence 27.3s, RCA 7.6s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed, pod-sandbox-create-failed

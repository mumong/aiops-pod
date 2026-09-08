## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 持续处于 Pending/ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found (fact-014f9b8c2627) | 直接定位挂载失败的配置依赖缺失 |
| 2 | K8s Config | kubernetes | volume "input" 配置引用了不存在的 ConfigMap | 确认为配置不当导致无法拉起 |
| 3 | K8s State | kubernetes | Pod 状态 `Pending`，容器 `app` 等待原因为 `ContainerCreating` (fact-a1aa08abca7d) | 确认当前处于启动阻塞状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` (fact-d51e1539fa32) | 独立证实容器卡在当前状态 |

* 证据 1 和证据 3 相互印证：K8s 事件明确指出了由于缺少特定 ConfigMap 导致挂载失败，进而使 Pod 卡在 `ContainerCreating` 状态（见证据 3）。
* 证据 2 补充了配置上下文，确认了缺失对象是 `ConfigMap unavailable-config`。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → Kubelet 挂载 volume 'input' 失败 (MountVolume.SetUp failed) → Pod 持续处于 ContainerCreating/Pending 状态 → 用户应用无法运行
```

### 根因结论

已确认根因为：Pod 的 volume 'input' 指向了不存在且未设置为可选的 ConfigMap 'unavailable-config'。
该配置缺失导致 Kubelet 无法完成挂载步骤，致使 Pod 始终无法完成初始化并进入运行状态。
证据 1 (FailedMount 事件)、证据 2 (配置状态) 与证据 3 (容器状态) 完整闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.8s
├─ 并发证据采集: 43.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 43.2s (Evidence 34.0s, RCA 9.0s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed

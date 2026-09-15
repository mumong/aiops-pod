## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh 卡在 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container: "app"`, `reason: "ContainerCreating"` | 证实 Pod `workload-5dbb5dcd6c-bntfh` 卡在容器创建阶段，未启动 |
| 2 | K8s Event | kubernetes | 重复 46 次 `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) ... "unavailable-network" not found` (时间跨度 2m8s ~ 61s) | 核心证据：指出 Multus 找不到名为 `unavailable-network` 的网络定义，是阻碍 Pod 启动的直接原因 |

K8s 状态与事件高度吻合：Pod 处于等待状态的原因正是 Multus CNI 组件反复报告无法找到指定网络配置。Metric 数据与事件结果一致，但 Logging 和 Tracing 由于容器未启动而不可用，无额外补充证据。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' 
→ Multus CNI 在沙箱创建阶段无法找到网络定义 (报 NoNetworkFound) 
→ 容器网络沙箱创建失败 
→ Pod 状态卡在 ContainerCreating
```

### 根因结论

已确认根因：Pod 的 Spec 配置引用了不存在的 Multus NetworkAttachmentDefinition 资源 `unavailable-network`。
这一配置错误导致 Multus CNI 在尝试配置网络接口时失败（证据 #2），进而使得容器无法完成创建过程，导致 Pod 持续处于 `ContainerCreating` 状态（证据 #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 36.6s
├─ 并发证据采集: 44.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 44.1s (Evidence 37.5s, RCA 6.5s)
└─ 汇总总结: 6.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed

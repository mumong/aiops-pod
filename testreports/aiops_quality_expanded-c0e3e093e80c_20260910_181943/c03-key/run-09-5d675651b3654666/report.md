## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload stuck in ContainerCreating |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Pending (fact-2efc25987fa9) | 确认 Pod 处于等待调度的停滞状态 |
| 2 | K8s Event | Kubernetes | `FailedMount`: unable to attach or mount volumes: unmounted volumes=[input] (fact-8e4cea79b9ac) | 定位到具体失败的操作是挂载 `input` 卷 |
| 3 | K8s Event | Kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key (fact-bffcd57a23ad) | 揭示失败的根本原因为配置键缺失 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` for reason `ContainerCreating` (fact-833277c039ba) | 独立观测证实容器卡在创建阶段 |
| 5 | K8s State | Kubernetes | `restart_count`: 0 (fact-6c5682956e3b) | 排除因资源超限导致 CrashLoopBackOff 的可能性 |
| 6 | K8s Config | Kubernetes | Resource Request `cpu: 5m, memory: 8Mi` (fact-2a32ed74f5fa, fact-774995f6d457) | 提供上下文，排除因资源不足导致调度失败的可能 |

**证据关联说明：**
事实 #2 和 #3 的 `FailedMount` 事件在时间上紧密相连，事实 #3 提供了事实 #2 中挂载失败的具体技术原因（配置引用错误），两者互为表里。Metric #4 独立验证了 K8s State #1 中观察到的等待状态。由于 Pod 始终未完成挂载，Logging 和 Tracing 因容器未启动而无数据（事实 #5 显示无重启，进一步证实未进入应用运行阶段）。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺少键 'unavailable-key' → Kubelet 挂载卷 'input' 失败 → Pod aiops-case-v05/workload 卡在 ContainerCreating 阶段 → 应用无法启动
```

### 根因结论

已确认根因为 **配置引用错误**。

Kubelet 在尝试挂载名为 `input` 的卷时，尝试从 ConfigMap 中读取名为 `unavailable-key` 的键，但该键在 ConfigMap `workload-input` 中并不存在（引用证据 #3, #1）。这一配置层面的错误导致挂载操作永久失败（引用证据 #2），进而阻止了容器启动和 Pod 状态的推进（引用证据 #1, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 44.2s
├─ 并发证据采集: 28.4s
│  └─ g1 aiops-case-v05/workload: 28.4s (Evidence 22.9s, RCA 5.4s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed

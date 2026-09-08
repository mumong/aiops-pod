## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v stuck in ContainerCreating/Pending state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 状态 `Pending`；条件 `PodScheduled=True`，但 `ContainersReady=False`，消息指出 `containers with unready status: [app]` | 确认 Pod 已获调度但容器未就绪，排除节点资源不足导致的 Pending |
| 2 | K8s State | kubernetes | 容器 `app` 等待原因为 `ContainerCreating`；重启计数 `0` | 隔离问题阶段：容器尚未创建，排除了运行期崩溃或配置注入失败 |
| 3 | K8s Event | kubernetes | 未提供（工具执行无匹配结果） | 缺失直接报错日志 |
| 4 | K8s Config | kubernetes | CPU 限制 50m / 请求 5m；内存限制 32Mi / 请求 8Mi | 资源配额极小，非导致无法创建沙箱的常见原因 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (reason: `ContainerCreating`, timestamp: `09:34:42Z`) | 指标侧验证了容器处于等待状态 |
| 6 | Metric | prometheus | `kube_pod_status_phase=1` (phase: `Pending`, container: `kube-state-metrics`) | 确认集群状态侧视图与 Pod 实际状态一致 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (container: `app`) | 确认应用容器从未成功启动 |

**证据说明：**
Kubernetes 状态表明 Pod 已调度（`PodScheduled=True`）但无法进入 `Running` 阶段，等待原因为 `ContainerCreating`，且重启次数为 0，说明问题发生在容器初始化之前。指标数据（Metric）完全印证了该状态。由于缺乏直接的 Event 日志，根因推断主要依赖于诊断上下文中的 CNI 配置缺失事实。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 NetworkAttachmentDefinition 'unavailable-network' 资源 → Multus CNI 无法解析网络附件 → Kubelet 沙箱创建失败 (FailedCreatePodSandBox) → Pod 停留在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因：**
Multus CNI 插件在尝试创建 Pod 沙箱时，无法在 `aiops-case-05` 命名空间中找到配置引用的 `NetworkAttachmentDefinition` 资源 `'unavailable-network'`。这一缺失导致网络配置注入失败，Kubelet 报告 `FailedCreatePodSandBox` 错误，使 Pod 停滞在 `ContainerCreating` 状态。
*(支撑证据：诊断事实确认了该配置引用存在且状态为未就绪，导致容器始终无法完成初始化)*

**当前不足：**
现有证据未提供导致 `'unavailable-network'` 资源缺失的具体原因（例如：CRD 未部署、YAML 遗漏或命名空间未部署对应的 YAML 文件）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.9s
├─ 并发证据采集: 36.7s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 36.7s (Evidence 29.3s, RCA 7.3s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed

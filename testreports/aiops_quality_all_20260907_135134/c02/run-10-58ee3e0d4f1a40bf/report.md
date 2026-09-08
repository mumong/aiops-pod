## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod配置的镜像仓库域名 `registry.invalid` 无效，导致集群DNS解析失败，容器运行时无法拉取镜像 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `WaitingReason`: "ImagePullBackOff"; `WaitingMessage`: "Back-off pulling image \"registry.invalid/aiops/workload:missing\"" | 确定 Pod 处于拉取镜像失败状态，并指向具体的镜像地址 |
| 2 | K8s State | Kubernetes | `PodPhase`: "Pending"; `Ready`: "False" (ContainersNotReady); `Container`: "app" | 描述 Pod 的整体停滞状态，与拉取失败原因一致 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`=1 (Labels: `container=app`, `reason=ImagePullBackOff`); `restarts_total`=0 | 确认异常发生时长（单样本）且无重启行为，验证状态持续存在 |

**证据关联说明**：
Kubernetes 状态明确指出了“ImagePullBackOff”错误，且 WaitingMessage 中包含具体的镜像名称 `registry.invalid/aiops/workload:missing`；Prometheus 指标在相同时间窗口内（`2026-09-07T07:14:21.022000Z`）以 `reason=ImagePullBackOff` 的标签独立证实了这一等待状态。由于容器未能成功启动，Logging 与 Tracing 均因“容器未启动，物理上不会产生应用日志或业务 Trace”而无数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置的镜像仓库域名 `registry.invalid` 无效 → 集群 DNS 解析失败，镜像拉取受阻 → 容器运行时进入 `ImagePullBackOff` 状态 → Pod 处于 `Pending` 且 `Ready=False`
```

### 根因结论

**已确认的根因**：Pod 配置的镜像仓库域名 `registry.invalid` 无效，导致集群 DNS 解析失败，容器运行时无法拉取镜像。

该结论由以下证据支撑：
- **K8s State (Fact #1, #2)**：直接报告 `ImagePullBackOff` 错误及具体的失败镜像 `registry.invalid/aiops/workload:missing`，表明失败源于镜像获取阶段，而非容器内部运行逻辑。
- **Metric (Fact #3)**：指标数据独立佐证了等待原因为 `ImagePullBackOff`，且无重启记录，符合镜像拉取失败导致容器无法启动的特征。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.8s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 37.8s (Evidence 32.1s, RCA 5.6s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed

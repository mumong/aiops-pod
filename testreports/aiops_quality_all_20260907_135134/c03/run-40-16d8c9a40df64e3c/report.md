## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 持续处于 ContainerCreating 状态，未能进入 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态: `ContainerCreating`, 重启次数: `0`, Pod 阶段: `Pending` (K8s Fact IDs: `fact-aef86c13c606`, `fact-157a6995497c`) | 确认故障处于容器启动前的挂载或配置拉取阶段，尚未进入运行期。 |
| 2 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=ContainerCreating) = `1`, `kube_pod_status_phase` (Pending) = `1`, 重启总数= `0` (Metric Fact IDs: `fact-c2189aa70e21`, `fact-c183781a13ef`) | 独立确认 Pod 状态与 K8s API 一致，排除单一视图偏差，无重启说明非运行期崩溃。 |
| 3 | K8s Config | Kubernetes | `volume.input` 配置依赖 ConfigMap，但 `aiops-case-03` 命名空间中该 ConfigMap 不存在，导致 `FailedMount` (K8s Fact IDs: `fact-3c6102053c47`, `fact-d5dfb3ff8bc1`) | 揭示核心阻断原因：启动资源（配置/挂载）缺失，直接导致 `ContainerCreating` 阶段停滞。 |

**证据说明：**
- K8s State (`#1`) 的 `Pending` 阶段与 `ContainerCreating` 等待原因，与 Prometheus Metrics (`#2`) 的状态完全吻合。
- K8s Config (`#3`) 提供的根本原因（缺失 ConfigMap）解释了为什么容器停留在初始化阶段且重启次数为 0，因为容器根本无法启动。
- 由于容器未启动，Logging 和 Tracing 维度标记为 `not_applicable`，这符合 `FailedMount` 的物理现象（未启动不产生日志）。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap 'unavailable-config' 在命名空间 'aiops-case-03' 中缺失 → Volume 'input' 挂载失败 (MountVolume.SetUp failed) → Pod 卡在 ContainerCreating 状态，无法启动容器 → 现象：Pod 状态为 Pending/ContainerCreating，无日志、无监控数据
```

### 根因结论
- **已确认根因**：Pod 在 `ContainerCreating` 阶段停滞的根本原因是引用了不存在的 ConfigMap (`unavailable-config`)，导致挂载操作 (`MountVolume.SetUp`) 失败。
- **证据支撑**：K8s 配置事实（Fact IDs: `fact-3c6102053c47`, `fact-d5dfb3ff8bc1`）直接指出了缺失的资源，而 K8s 状态（Fact ID: `fact-aef86c13c606`）和 Metric（Fact ID: `fact-c2189aa70e21`）一致验证了容器未启动且等待挂载的状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.2s
├─ 并发证据采集: 33.8s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 33.8s (Evidence 25.1s, RCA 8.7s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed

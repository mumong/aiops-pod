## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ErrImagePull | Pod workload (aiops-case-v07) 处于 Pending 状态，容器 app 因 ErrImagePull 转换为 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: ErrImagePull` (Fact: fact-6916cb39758a) | 确证拉取操作失败 |
| 2 | K8s Event | kubelet | `rpc error: code = NotFound desc = ... registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908: not found` (Fact: fact-9cf5aa72ca79) | 提供决定性失败原因：镜像不存在 |
| 3 | K8s State | pod.status | `Pending` (Fact: fact-e6684accd492) | 描述当前故障现象 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff", container="app"} = 1` (Fact: fact-f083af988d74) | 确认 Pod 处于等待拉取镜像的状态 |

**证据说明**
- 证据 1 和 2 来自同一异常组（K8s Event），共同构成了从“拉取失败”到“仓库响应 NotFound”的完整证据链，直接支撑了根因。
- 证据 3 和 4 分别从 Pod 状态和 Metrics 指标层面印证了 Pod 因镜像拉取问题而卡在 `Pending` / `ImagePullBackOff` 的状态，与 K8s 事件互为佐证。
- Logging 和 Tracing 维度被判定为 `not_applicable`（容器未启动），无相关数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在的镜像 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908' 
→ 镜像仓库响应 NotFound (Fact: 2) 
→ kubelet 拉取镜像失败并进入 ImagePullBackOff (Fact: 1, 4) 
→ Pod 持续处于 Pending 状态 (Fact: 3)
```

### 根因结论

**已确认的根因**：Pod 配置了不存在的镜像标签 `aiops-fixture-unavailable-20260908`，导致镜像仓库返回 `NotFound` 错误。

- **证据支撑**：
    - 证据 2 (`fact-9cf5aa72ca79`) 明确指出错误原文为 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908: not found`。
    - 证据 1 (`fact-6916cb39758a`) 记录了 `Error: ErrImagePull`，与镜像查找失败直接对应。
    - 证据 4 (`fact-f083af988d74`) 通过 Prometheus 指标 `ImagePullBackOff` 确认了该失败状态的持续性。

- **未知项**：该特定镜像标签 `aiops-fixture-unavailable-20260908` 为何被配置（丢失、错配或测试用例遗留）在输入事实中证据不足，无法确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.3s
├─ 并发证据采集: 36.4s
│  └─ g1 aiops-case-v07/workload: 36.4s (Evidence 27.6s, RCA 8.7s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed

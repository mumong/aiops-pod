## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，容器无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-428a8306aa53` | `container.waiting_reason`: `ImagePullBackOff` | 确认核心异常状态 |
| 2 | K8s Event | `fact-20edab1fe776` | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 直接指出镜像地址及拉取失败导致的退避行为 |
| 3 | K8s State | `fact-ee2c5ecc1ea4` | `container.waiting_message`: `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 佐证拉取失败的官方容器状态反馈 |
| 4 | Metric | `fact-5d5ea54b8d13` | `kube_pod_container_status_waiting_reason` 值为 `1` (Reason: `ImagePullBackOff`) | 独立于 K8s API 的监控指标验证了拉取镜像失败的状态 |
| 5 | Metric | `fact-5266df760d9b` | `kube_pod_container_status_restarts_total` 值为 `0` | 证实容器尚未成功运行过，排除了因业务逻辑导致的反复重启可能 |

**证据分析：**
- **状态与指标互证**：K8s 事件的错误原文（#2）与容器状态（#1）高度一致，明确指向 `registry.invalid/aiops/workload:missing` 这个地址在拉取时失效。
- **逻辑排除**：重启次数为 0（#5）说明问题发生在容器启动前阶段（镜像拉取），排除了应用内部错误。
- **日志缺失说明**：因容器未能启动，日志与 Trace 维度未能采集到应用数据，属物理现象限制，不影响基于 K8s 状态与指标的根因判定。

## 🎯 根因分析 · g1

### 因果链

```text
配置了无效镜像 registry.invalid/aiops/workload:missing → kubelet 拉取失败并触发 Back-off 机制 → 容器处于 Waiting (ImagePullBackOff) 状态，Pod 保持 Pending → 用户侧 Pod 状态异常且无容器日志
```

### 根因结论

**已确认根因：容器镜像地址配置无效。**

Pod `aiops-case-02/workload-65b7f54794-rnlv4` 配置了不可达或无效的容器镜像地址 `registry.invalid/aiops/workload:missing`。这导致 `kubelet` 无法获取镜像并启动容器，随后 Kubernetes 进入 `ImagePullBackOff` 退避状态（见事实 #1, #2, #3, #4）。

现有 K8s 状态、事件记录及监控指标证据充分，且彼此印证；虽然日志和 Trace 工具调用失败，但这符合“容器未启动”的物理事实，不影响根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 21.1s
├─ 并发证据采集: 91.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 91.5s (Evidence 83.7s, RCA 7.5s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

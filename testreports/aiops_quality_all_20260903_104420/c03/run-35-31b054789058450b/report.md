## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 卡在 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `ContainerCreating` 状态，reason=`ContainerCreating` (fact-40d662c37d20) | 明确 Pod 处于挂载阶段，尚未进入运行态 |
| 2 | K8s Event | `kubernetes` | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-f24e34fc3d29) | 直接根因：Kubelet 报告找不到指定的 ConfigMap |
| 3 | K8s State | `kubernetes` | Pod Phase=`Pending`, Ready=`False`, `ContainersNotReady` (fact-2d8a183ee743, fact-c584e7b69e52, fact-a8f0069b4681) | 症状佐证：Pod 因挂载失败被调度器挂起 |
| 4 | K8s Config | `kubernetes` | Pod Spec 定义挂载 volume `input`，资源 requests: cpu=5m, memory=8Mi (fact-40d662c37d20, fact-0a924edc8615, fact-ada605d6b46d) | 确认 Pod 配置了卷挂载请求，且资源请求极低 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` = 1 (reason: ContainerCreating), `kube_pod_status_phase` = Pending (fact-c4486dc5b95a, fact-3edac325abcd) | 独立维度验证：Prometheus 指标实时映射 K8s API 的 Pending/Waiting 状态 |

**证据说明：**
Kubernetes API 获取的事件 `FailedMount` 提供了决定性事实：Pod 试图挂载名为 "input" 的卷时，由于引用的 ConfigMap "unavailable-config" 不存在而失败。K8s 状态显示 Pod 停留在 `Pending` 和 `ContainerCreating`，Metrics 数据进一步印证了容器因等待挂载而处于 `waiting` 状态。由于容器未能启动，Logging 和 Tracing 维度的查询失败是预期行为，不影响根因判定。

## 🎯 根因分析 · g1

### 因果链
```text
Pod Spec 定义挂载非可选 ConfigMap "unavailable-config" → Kubelet 执行 MountVolume.SetUp 查找失败 → 卷挂载错误阻塞容器启动 → Pod 持续处于 ContainerCreating/Pending 状态
```

### 根因结论
**已确认根因**：
Pod 的 YAML 配置中存在非可选的卷挂载（volume `input`），该卷引用了不存在或未被正确创建的 ConfigMap `unavailable-config`。

证据链（引用表格编号）：
1.  **直接错误**：K8s 事件（#2）明确记录了 `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found`，这是导致挂载停滞的直接原因。
2.  **状态印证**：Pod 当前状态为 `ContainerCreating`（#1）且 Phase 为 `Pending`（#3），与挂载失败无法继续执行 `init` 或主容器的生命周期特征一致。
3.  **指标辅助**：Prometheus 指标（#5）显示容器等待原因为 `ContainerCreating`，确认了系统层面的阻塞并未随时间推移自动解除。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.9s
├─ 并发证据采集: 36.1s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 36.1s (Evidence 27.6s, RCA 8.4s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod 配置使用了无效镜像源 `registry.invalid` 及不存在的镜像 tag `missing`，导致 kubelet 在 node2 上反复拉取失败并进入 BackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `event.message` (fact-0abfcd5a9be9) | `Normal BackOff 3m50s (x288 over 68m) kubelet Back-off pulling image "registry.invalid/aiops/workload:missing"` | 直接证据：确认为镜像拉取失败导致的 BackOff 循环。 |
| 2 | K8s State | `pod.status` (fact-a56d360b4fa8) | `Pending` | 症状：Pod 未进入运行状态，处于挂起等待。 |
| 3 | Metric | `kube_pod_container_status_waiting_reason` (fact-dbefad103ba3) | `reason=ImagePullBackOff, value=1` | 外部验证：指标系统证实 Container 处于 ImagePullBackOff 等待原因。 |

**证据关联说明**：
1. K8s Event 明确指出了失败的镜像源与 Tag，以及长达 68 分钟的反复拉取行为；Metric 提供了同一状态的独立量化确认。
2. Pod 的 Pending 状态与 BackOff 循环现象一致，表明容器引擎（kubelet）未启动容器，而是处于重试逻辑中。
3. 其余配置信息（如 32Mi Memory Limit, 50m CPU Limit）均为静态配置，非导致当前故障的原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置使用了无效镜像源 registry.invalid 及不存在的镜像 tag missing → kubelet 反复拉取镜像失败 → Pod 状态变为 Pending (ImagePullBackOff) → 用户可见 Pod 处于非运行状态且日志显示拉取失败
```

### 根因结论

已确认根因为 **Pod 配置错误**。
Pod `aiops-case-02/workload-65b7f54794-z7kdp` 的容器配置中指定了不可达的镜像仓库 `registry.invalid` 以及不存在的镜像标签 `missing`。这直接导致 `kubelet` 在拉取镜像时失败并进入指数退避（Back-off）模式，使 Pod 持续处于 `Pending` 且等待原因为 `ImagePullBackOff` 的状态（证据编号：#1, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 15.8s
├─ 并发证据采集: 554.9s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 554.9s (Evidence 547.9s, RCA 7.0s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed

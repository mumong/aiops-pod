## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 in aiops-case-02 stuck in ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `reason`: ImagePullBackOff, `message`: Back-off pulling image "registry.invalid/aiops/workload:missing" (fact-961e15bff5dc, fact-6948839ea859) | 确定 Pod 处于等待状态的根本原因是镜像拉取失败 |
| 2 | K8s Event | kubernetes | `reason`: BackOff, `message`: Back-off pulling image "registry.invalid/aiops/workload:missing", `count`: x349 over 84m (fact-559cb5c72975) | 证明镜像拉取失败是长期持续存在的系统性现象，而非短暂网络抖动 |
| 3 | Metric | prometheus | `reason`: ImagePullBackOff, `value`: 1 (fact-be4adc202d65) | 指标状态与 Kubernetes 事件描述一致，独立确认了当前异常状态 |
| 4 | K8s Config | kubernetes | `container`: app, `reason`: ImagePullBackOff, `message`: Back-off pulling image "registry.invalid/aiops/workload:missing" (fact-6948839ea859) | 直接定位到容器配置中无效的镜像引用路径及标签 |

现有 K8s 状态、指标和事件日志相互印证，一致指向 `registry.invalid/aiops/workload:missing` 这一无效镜像源是导致故障的直接原因。由于容器尚未启动，Logging 和 Tracing 维度的数据采集被跳过，但 K8s 侧的多维度事实已充分支持根因定位。

## 🎯 根因分析 · g1

### 因果链

```text
无效的镜像配置 (registry.invalid/aiops/workload:missing) → 镜像拉取长期失败 (x349次/84分钟) → Pod 处于 ImagePullBackOff (Pending) 状态 → 用户服务不可用
```

### 根因结论

已确认根因为 Pod 规范中配置了无效的镜像引用 `registry.invalid/aiops/workload:missing`。该镜像地址属于保留域名且不可达，导致 kubelet 在长达 84 分钟的周期内连续 349 次拉取失败（证据编号：1, 2, 4）。受限于 K8s 调度机制，Pod 无法启动（证据编号：4），从而引发持续的 `ImagePullBackOff` 状态（证据编号：1, 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.8s
├─ 并发证据采集: 63.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 63.2s (Evidence 55.7s, RCA 7.3s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

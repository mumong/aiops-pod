## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod配置了无效的镜像域名`registry.invalid`，导致集群DNS无法解析，镜像拉取失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-00d84295ae40) | container.waiting_message: "Back-off pulling image \"registry.invalid/aiops/workload:missing\"" | 核心证据，明确指出镜像域名无效导致拉取失败 |
| 2 | K8s State | kubernetes (fact-d53e3b98e776) | container.waiting_reason: "ImagePullBackOff" | 确认容器因镜像拉取问题处于重试退避状态 |
| 3 | K8s State | kubernetes (fact-60cdefde61cc) | pod.phase: "Pending" | 确认 Pod 未能进入运行阶段，与镜像拉取失败一致 |
| 4 | K8s State | kubernetes (fact-332c3916c566) | pod.condition ContainersReady: False, reason: "ContainersNotReady" | 确认容器未达到就绪条件 |
| 5 | Metric | prometheus (fact-cb461416175b) | kube_pod_container_status_waiting_reason (reason="ImagePullBackOff", value="1") | 监控数据独立印证镜像拉取失败状态 |
| 6 | Metric | prometheus (fact-1826a627fb54) | kube_pod_container_status_restarts_total (value="0") | 排除重启风暴，符合初次拉取失败的单点异常特征 |

Kubernetes 状态与 Prometheus 监控数据在镜像拉取失败（ImagePullBackOff）和 Pod 挂起（Pending）的状态上完全一致。重启计数为 0 且日志缺失（fact-00d84295ae40 提示 Back-off），排除了应用启动后崩溃重演的可能，确认为镜像解析层面的初始故障。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效镜像域名 registry.invalid → 镜像拉取失败 (ImagePullBackOff) → Pod 处于 Pending 状态 → 应用不可用
```

### 根因结论

已确认根因为 Pod 配置了无效的镜像域名 `registry.invalid`。
- **现象支撑**：Pod 状态卡在 `Pending`（fact-60cdefde61cc），容器等待原因为 `ImagePullBackOff`（fact-d53e3b98e776）。
- **直接原因**：K8s 状态明确捕获到拉取失败详情：“Back-off pulling image \"registry.invalid/aiops/workload:missing\"”（fact-00d84295ae40）。
- **监控印证**：Prometheus 指标 `kube_pod_container_status_waiting_reason` 记录了 `ImagePullBackOff` 状态且值为 1（fact-cb461416175b）。
- **逻辑排他**：重启计数为 0（fact-1826a627fb54）且日志/Tracing 不适用（容器未启动），证实故障发生在容器运行前的镜像拉取阶段，而非应用逻辑错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 27.9s
├─ 并发证据采集: 37.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 37.2s (Evidence 32.5s, RCA 4.6s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod workload-65b7f54794-jmq6b 处于 ImagePullBackOff 状态，容器等待启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Normal BackOff 8s (x44 over 10m) kubelet Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认 Pod 持续处于镜像拉取失败后的退避状态 |
| 2 | K8s Event | kubernetes | `Warning Failed 8m42s (x4 over 10m) kubelet Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 记录失败的具体错误原因为 DNS 解析失败，直接指向配置错误 |
| 3 | K8s Config | kubernetes | `container.waiting_reason: ImagePullBackOff` | 确认容器的最终等待原因与事件记录一致 |
| 4 | K8s State | kubernetes | `pod.status: Pending`<br>`pod.condition.Ready: False (reason: ContainersNotReady)` | 确认 Pod 因无法拉取镜像而停留在 Pending 阶段，无法进入 Running 状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (样本量: 1) | 监控侧确认当前该 Pod 处于 ImagePullBackOff 状态 |

**证据说明**：
Kubernetes 事件（#1、#2）与 K8s 状态（#3）明确指出了镜像拉取失败的根本原因是 DNS 无法解析 `registry.invalid`。指标数据（#5）验证了这一状态在监控窗口内的持续性。由于容器尚未启动，日志与链路追踪数据缺失符合物理预期，不产生冲突。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置了无效域名 'registry.invalid' → 节点 DNS 解析失败 (no such host) → 容器运行时无法建立到 Registry 的连接 → Pod 陷入 ImagePullBackOff 等待
```

### 根因结论

已确认的根因为 Pod 镜像配置中的 Registry 域名 `registry.invalid` 无效（RFC 2606 保留域名）。节点上的 DNS 服务（`127.0.0.53`）无法解析该主机名，导致 kubelet 在拉取镜像阶段即遭遇 `no such host` 错误（见证据 #2），进而使 Pod 状态卡在 `ImagePullBackOff`（见证据 #3、#5）。现有证据链完整，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.2s
├─ 并发证据采集: 42.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 42.7s (Evidence 35.7s, RCA 6.9s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed

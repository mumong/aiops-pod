## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | 镜像仓库域名 `registry.invalid` 配置错误，导致节点 DNS 解析失败（no such host），镜像拉取彻底中断。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-19c1a84653fc) | `container.waiting_reason` = `ImagePullBackOff` | 确定容器处于重试拉取镜像的异常状态 |
| 2 | K8s State | kubernetes (fact-ab801574ebab) | `container.waiting_message` = `"Back-off pulling image \"registry.invalid/aiops/workload:missing\""` | 指出具体缺失的镜像及配置的镜像仓库域名 `registry.invalid` |
| 3 | K8s State | kubernetes (fact-0731462b14c5) | `pod.phase` = `Pending` | 确认 Pod 因无法启动容器而停滞在 Pending 阶段 |
| 4 | K8s State | kubernetes (fact-a3a8c010783f) | `pod.condition` = `ContainersReady(False)` | 确认容器就绪条件未达成 |
| 5 | Metric | prometheus (fact-0a28ecf1a783) | `kube_pod_container_status_waiting_reason` = `1` (labels: `container=app`, `reason=ImagePullBackOff`) | 验证了 K8s State 中观察到的 ImagePullBackOff 状态在 Prometheus 侧持续存在 |
| 6 | Metric | prometheus (fact-ff1f42ca7932) | `kube_pod_container_status_restarts_total` = `0` (container=`app`) | 表明容器从未成功启动过，排除了容器崩溃重启的可能性 |

**证据印证说明：**
K8s State 直接给出了导致 Pod 停滞的具体错误原因（`ImagePullBackOff`）和受阻镜像地址（`registry.invalid`）。Metric 中的 `kube_pod_container_status_waiting_reason` 独立印证了该异常状态的存在，而 `restarts_total=0` 进一步佐证了镜像拉取从未成功、容器未启动过的事实。

## 🎯 根因分析 · g1

```text
镜像仓库域名 registry.invalid 配置错误 → DNS 解析失败 (no such host) → 镜像拉取彻底中断 (ImagePullBackOff) → Pod 处于 Pending 状态且 app 容器未就绪
```

### 根因结论

**已确认根因：** 镜像仓库域名 `registry.invalid` 配置错误。

**分析：** 输入提供的正式 RCA 事实指出该域名配置错误，导致节点 DNS 解析失败，从而致使镜像拉取中断。本组证据强有力地支持了这一结论：
1.  K8s 状态显示 Pod 处于 `Pending`，`app` 容器等待原因为 `ImagePullBackOff` (证据 #1, #3)。
2.  具体的等待消息明确指出受阻镜像为 `registry.invalid/aiops/workload:missing` (证据 #2)。
3.  容器重启次数为 0 (证据 #6)，说明容器从未启动，排除了运行时故障，将故障点锁定在启动前的镜像拉取阶段。

以上证据链完整闭合，直接指向镜像仓库不可达为导致 Pod 挂起的唯一原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.2s
├─ 并发证据采集: 32.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 32.0s (Evidence 25.6s, RCA 6.3s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed

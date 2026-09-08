## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status: Pending`, `pod.phase: Pending` | 确立 Pod 当前处于等待启动的阶段 |
| 2 | K8s State | kubernetes | `container.waiting_reason: ImagePullBackOff` | 指向镜像拉取失败且重试退避的根本状态 |
| 3 | K8s Event | kubernetes | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 记录 kubelet 持续拉取失败的具体镜像路径与报错模式 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}: 1` | 独立指标验证容器确实处于该异常状态，且重启次数为 0，确认处于持续等待中 |

**证据小结：**
K8s 状态、事件日志与 Prometheus 指标相互印证，一致指向镜像拉取失败（`ImagePullBackOff`）。K8s 事件明确指出了无效的镜像源，而指标确认了该状态的持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
镜像地址 registry.invalid 域名无效且无 imagePullSecrets → Kubelet 拉取镜像失败触发退避 → 容器进入 ImagePullBackOff 等待状态 → Pod 处于 Pending 异常状态
```

### 根因结论

已确认根因：**Pod 配置的镜像地址 `registry.invalid/aiops/workload:missing` 包含无效域名，且未配置 imagePullSecrets**。
- **证据**：`#3` K8s 事件明确记录 kubelet 因拉取该镜像而 Back-off；`#2` 状态与 `#4` 指标一致确认了该拉取失败导致的 `ImagePullBackOff` 状态。
- **排除**：由于容器未能启动，日志与追踪数据不可用（工具调用返回权限被拒或容器未运行），但 K8s 层面的异常足以构成充分证据。

---

## 📊 性能统计

```text
├─ 总耗时: 3.5m
├─ 问题定位: 14.5s
├─ 并发证据采集: 186.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 186.8s (Evidence 176.5s, RCA 10.1s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

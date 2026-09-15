## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s | `Warning Failed: dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 确认 DNS 解析失败，导致无法访问镜像仓库 |
| 2 | K8s Event | K8s | `Normal BackOff: Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认 kubelet 正在因拉取失败而退避重试 |
| 3 | Metric | Prom | `kube_pod_container_status_waiting_reason=1` (reason: ImagePullBackOff, sample_count: 1) | 指标确认 Pod 处于等待状态且原因匹配 |
| 4 | K8s State | K8s | `Pod status: Pending` | 确认 Pod 处于 Pending 状态，尚未运行 |

**证据印证分析：**
Kubernetes Event 中的 DNS 查询报错 `no such host` 直接解释了 ImagePullBackOff 的触发机制；Metric 的等待状态确认了该故障在采集时间点的持续存在；Pending 状态则反映了故障导致的最终生命周期结果。

## 🎯 根因分析 · g1

### 因果链

```text
DNS无法解析域名 registry.invalid → kubelet拉取镜像失败 → 容器状态等待(退避重试) → Pod呈现 ImagePullBackOff
```

### 根因结论

已确认的根因为 **DNS解析失败导致镜像仓库不可达**。事实证据（Fact 1, 2, 3）明确显示 kubelet 试图连接 `registry.invalid` 时遭遇 DNS `no such host` 错误，进而引发 `ImagePullBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 54.1s
├─ 问题定位: 21.4s
├─ 并发证据采集: 26.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 26.7s (Evidence 19.0s, RCA 7.5s)
└─ 汇总总结: 6.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed

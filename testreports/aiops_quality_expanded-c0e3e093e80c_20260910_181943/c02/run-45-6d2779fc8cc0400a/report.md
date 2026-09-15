## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod workload-65b7f54794-jmq6b 处于 Pending 状态，容器 app 处于 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-54ee498c3349` | Container `app` waiting_reason: `ImagePullBackOff` | 确立容器当前处于镜像拉取失败的状态。 |
| 2 | K8s Config | `fact-51aa9c06b725` | Container `app` waiting_message: `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认未拉取的镜像名称为 `registry.invalid/aiops/workload:missing`。 |
| 3 | K8s Event | `fact-c9a7221b1082` | `Failed to pull image... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供根因的直接证据：K8s 节点 DNS 解析域名失败。 |
| 4 | Metric | `fact-f73bb580e02d` | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 确认指标侧同步显示当前处于 `ImagePullBackOff` 状态。 |

**证据印证说明：**
Kubernetes 事件记录中的错误原因 `no such host` 与镜像状态 `ImagePullBackOff` 完全吻合，Metric 监控结果进一步佐证了该状态并非偶发。由于容器从未成功启动，Logging 和 Tracing 数据未产生，属于物理限制，不影响结论。

## 🎯 根因分析 · g1

### 因果链

```text
集群 DNS (127.0.0.53) 无法解析 registry.invalid 域名 → kubelet 尝试拉取镜像时连接被拒 → 镜像拉取失败并进入退避 → Pod 状态转为 ImagePullBackOff 并保持 Pending
```

### 根因结论

已确认根因：Pod 的容器配置中指定了无效的镜像仓库域名 `registry.invalid`。
该域名无法被集群节点的 DNS 服务 `127.0.0.53` 解析（事实编号 `fact-c9a7221b1082`），导致 `kubelet` 无法拉取镜像 `registry.invalid/aiops/workload:missing`（事实编号 `fact-51aa9c06b725`）。由于镜像拉取持续失败，Pod 持续处于 `ImagePullBackOff` 等待状态，无法启动应用容器（事实编号 `fact-54ee498c3349`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.6s
├─ 并发证据采集: 34.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 34.1s (Evidence 25.3s, RCA 8.7s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-rnlv4 持续处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (x328 over 75m) | 持续观测到镜像拉取失败的明确报错，直接指向根因 |
| 2 | K8s State | Kubernetes | Container `app` 状态为 `ImagePullBackOff`，Pod 状态为 `Pending` | 确认 Pod 因镜像问题陷入死锁且无法就绪 |
| 3 | K8s State | Kubernetes | Container `app` 重启次数为 `0` | 排除重启风暴或 OOM 等应用层崩溃因素 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` = `1` | 指标确认当前存在且持续的拉取失败状态 |

证据表明：Pod 自启动以来重启次数为 0，且长时间（75分钟）持续处于拉取失败等待状态，直接锁定为配置层的镜像地址问题，而非网络波动或应用崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效/不可达的镜像地址 registry.invalid → kubelet 拉取镜像失败并触发 Back-off 重试 → 容器处于 ImagePullBackOff 等待状态 → Pod 状态持续 Pending 无法运行
```

### 根因结论

**已确认的根因**：Pod 配置了无效的镜像仓库地址 `registry.invalid`。

该根因由多项证据强印证：
1.  **K8s Event** 显示 kubelet 在长达 75 分钟的观察窗口内，反复报告拉取 `registry.invalid/aiops/workload:missing` 失败并进入 Back-off 状态 [证据 #1]；
2.  **K8s State** 和 **Metric** 确认容器和 Pod 当前状态严格对应 `ImagePullBackOff` 和 `Pending`，且重启次数为 0，排除了应用运行期的故障 [证据 #2, #3, #4]。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 21.7s
├─ 并发证据采集: 131.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 131.1s (Evidence 122.5s, RCA 8.4s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

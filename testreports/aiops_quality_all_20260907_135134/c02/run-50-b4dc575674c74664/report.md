## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 配置了无效的镜像仓库域名 `registry.invalid` 且未配置 `imagePullSecrets`，导致 kubelet 无法解析或连接镜像仓库，镜像拉取持续失败并触发 BackOff 机制。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | fact-4483f6e57fb3 | 容器 app 等待信息："Back-off pulling image \"registry.invalid/aiops/workload:missing\"" | 直接展示拉取失败的镜像地址及 Back-off 状态 |
| 2 | K8s State | fact-4ad9df776cb9 | 容器 app 等待原因为 `ImagePullBackOff` | 确认当前 Pod 卡在镜像拉取环节，未进入启动流程 |
| 3 | K8s Event | fact-6038b4ceb1d5 | Event: `BackOff` 原因触发，kubelet 记录持续拉取失败镜像 (已发生 265 次/64 分钟) | 证实拉取行为已持续长时间，且已触发 kubelet 退避机制 |
| 4 | Metric | fact-624e44d26aba | `kube_pod_container_status_waiting_reason` 值为 1，标签 `reason: ImagePullBackOff` | 通过监控指标交叉验证了容器处于镜像拉取失败等待态 |
| 5 | K8s State | fact-126caff81d07 / fact-2d855384664a | Pod 状态 `Pending`，容器 `app` 重启次数为 `0` | 确认 Pod 从未启动成功过，排除因 OOM 或应用崩溃导致的间歇性故障 |
| 6 | K8s Config | fact-372432ee6db3 / fact-bf61689a3567 | 内存硬限制 `32Mi`，CPU 硬限制 `50m` | 排除资源超限导致容器被杀或无法启动的可能 |

证据表明：Pod 处于 `Pending` 且重启数为 0，确认应用层尚未运行。Kubernetes 状态和事件日志均指向镜像拉取失败，且因域名 `registry.invalid` 无法连接。监控指标一致确认了该等待原因，且配置显示资源限制充足，排除了资源层面的干扰。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置 registry.invalid/aiops/workload:missing 且无 imagePullSecrets → kubelet 无法解析或连接镜像仓库 → 镜像拉取反复失败触发 BackOff 机制 → Pod 持续处于 ImagePullBackOff 状态
```

### 根因结论

已确认根因为 **Pod 镜像配置无效（域名 `registry.invalid` 无法解析）**。

该无效域名导致 `kubelet` 无法建立连接以拉取镜像，进而引发拉取请求反复失败并进入 `Back-off` 退避状态，最终表现为 Pod 始终处于 `ImagePullBackOff` 状态且容器未运行 [证据 1, 2, 3]。监控指标独立验证了这一等待状态 [证据 4]，同时资源配置及重启计数排除了其他导致容器无法启动的因素 [证据 5, 6]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 23.7s
├─ 并发证据采集: 43.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 43.4s (Evidence 35.5s, RCA 7.7s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed, pod-config-error, pod-volume-mount-failed

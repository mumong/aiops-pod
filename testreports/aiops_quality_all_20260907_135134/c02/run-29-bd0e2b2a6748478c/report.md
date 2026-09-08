## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ErrImagePull | Pod aiops-case-02/workload-65b7f54794-nqrzv 持续处于 Pending 状态，Container 报错 ErrImagePull / ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Pending`, `pod.status: Pending`, `pod.condition.ContainersReady: False` | 确认 Pod 未启动，容器未就绪 |
| 2 | K8s Event | kubelet | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供确切的 DNS 解析失败事实 |
| 3 | K8s Config | kubernetes | `image: registry.invalid/aiops/workload:missing` | 确认故障触发源为特定镜像地址 |
| 4 | K8s Event | kubelet | `Error: ErrImagePull` 与 `Error: ImagePullBackOff` | 描述镜像拉取失败的状态流转 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}: 1` (fact-0b252606235b) | 外部指标确认拉取失败状态的持续性 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` | 确认容器从未运行过，排除了运行期故障 |

**证据关联说明：**
Kubernetes 事件（#2）直接指出 `registry.invalid` 域名解析失败（NXDOMAIN），该事实由 K8s 状态（#1, #2, #3）中的镜像配置及错误原因互为印证。Metrics（#5, #6）作为独立观测源，排除了网络延迟或重启等动态因素，确认为启动前因静态配置导致的拉取失败。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 'registry.invalid' 无有效 DNS 解析记录 → kubelet DNS 查询失败 (NXDOMAIN) → 无法获取镜像 Manifest 导致拉取失败 → Pod 持续处于 Pending / ImagePullBackOff 状态
```

### 根因结论

已确认根因为 **镜像仓库域名 `registry.invalid` 无法解析**，导致 Kubelet 在 Pod 启动阶段无法下载镜像，进而使容器进入 `ImagePullBackOff` 状态。

- **决定性事实**：K8s Event `fact-0b252606235b` 明确记录了 `lookup registry.invalid on 127.0.0.53:53: no such host` 的错误，且配置中的镜像地址 `registry.invalid/aiops/workload:missing` 与此错误完全对应。
- **证据交叉验证**：Metrics `fact-a3b2d4f6ab97` 显示 `waiting_reason` 为 `ImagePullBackOff`，且 `restart_count` 为 0，说明容器因无法拉取镜像而从未尝试启动，排除了启动后崩溃的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.6s
├─ 并发证据采集: 38.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 38.1s (Evidence 30.5s, RCA 7.4s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed

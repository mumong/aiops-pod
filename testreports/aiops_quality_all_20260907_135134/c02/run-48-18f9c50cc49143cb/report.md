## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod `workload-65b7f54794-nqrzv` 处于 `ImagePullBackOff` 状态，镜像拉取持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed ... Error: ErrImagePull` (fact-3487636cd267) | 确认镜像拉取失败的直接现象 |
| 2 | K8s Event | kubernetes | `BackOff 78s (x265 over 61m)  kubelet  Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-7cfb440281ff) | 验证退避行为，锁定故障镜像 |
| 3 | K8s Event | kubernetes | `Failed to pull image ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-bb2933d054ca) | **核心诊断**：DNS 解析失败直接导致网络不可达 |
| 4 | K8s State | kubernetes | `container.waiting_reason: "ImagePullBackOff"` (fact-625b3a85e172) | 定义当前容器等待状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (labels: `reason="ImagePullBackOff"`) (fact-2cf8d9f0af5c) | 指标侧独立确认当前状态 |

**证据说明**：Kubernetes Event `fact-bb2933d054ca` 中的 DNS 报错信息直接揭示了 `registry.invalid` 无法解析，是导致 `fact-3487636cd267` 拉取失败和 `fact-7cfb440281ff` 进入 BackOff 状态的唯一网络层原因；Metric `fact-2cf8d9f0af5c` 的状态值与 K8s 状态事实完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
配置了无效域名 `registry.invalid` → 集群 DNS (`127.0.0.53`) 解析失败 (`no such host`) → kubelet 无法建立网络连接 (`dial tcp` 失败) → 镜像拉取失败 (`ErrImagePull`) 并持续退避 (`ImagePullBackOff`)
```

### 根因结论

已确认根因为：**Pod 配置中的镜像仓库域名 `registry.invalid` 无效，导致 DNS 解析失败。**

证据 `fact-bb2933d054ca` 明确指出 kubelet 尝试访问 `https://registry.invalid/v2/...` 时，本地 DNS 服务器返回 `lookup ... no such host`。此网络不可达直接导致了镜像拉取失败（`fact-3487636cd267`），进而使 Pod 陷入持续的退避拉取状态（`fact-7cfb440281ff`）。指标数据（`fact-2cf8d9f0af5c`）佐证了该异常状态的持续性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.3s
├─ 并发证据采集: 43.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 43.2s (Evidence 33.7s, RCA 9.4s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed

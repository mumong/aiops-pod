## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 持续处于 ImagePullBackOff 状态，无法启动容器 app。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": rpc error: code = Unknown desc = failed to pull and unpack image "registry.invalid/aiops/workload:missing": failed to resolve reference "registry.invalid/aiops/workload:missing": failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (`fact-a138d8528f93`) | 记录镜像拉取失败的完整堆栈，直接证明镜像域名 `registry.invalid` DNS 解析失败。 |
| 2 | K8s Event | `kubernetes` | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (`fact-d017b8aaa61f`) | 描述 kubelet 指数退避行为，反映拉取失败的持续性。 |
| 3 | K8s State | `kubernetes` | Pod 状态 `Pending`，容器 `app` 状态 `ImagePullBackOff` (`fact-323bb78bd16f`) | 确认 Pod 最终异常状态与事件中的错误类型一致。 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason="ImagePullBackOff"` (`fact-8d272585de84`) | 通过监控指标确认 Pod 处于 ImagePullBackOff 状态的实时性。 |

**证据印证说明：**
1. **现象与根因关联**：K8s 事件（#1、#3）显示的 `ImagePullBackOff` 状态与 Metric 指标（#4）完全吻合；事件详情（#1）中的 DNS 报错信息 `lookup registry.invalid on 127.0.0.53:53: no such host` 直接解释了“失败原因”。
2. **持续性与机制**：事件中的指数退避提示（#2）和指标确认（#4）表明该拉取失败状态已持续一段时间，符合镜像地址配置错误导致的一贯性失败现象。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 配置了无效镜像地址 registry.invalid/aiops/workload:missing → kubelet 尝试解析镜像域名 registry.invalid 时遭遇 DNS 失败 (no such host) → 镜像拉取失败并进入指数退避 (BackOff) 状态 → Pod 容器保持 Waiting/ImagePullBackOff，应用不可用
```

### 根因结论

已确认的根因为 **Pod 镜像地址配置错误**。

部署资源中配置的镜像仓库域名 `registry.invalid` 无法解析。如证据表第 1 行（`fact-a138d8525de84`）所示，kubelet 在向 DNS 服务器 `127.0.0.53:53` 查询该域名时返回了 `no such host` 错误，导致镜像拉取失败。由于拉取持续失败，kubelet 进入指数退避（Back-off）机制，最终使 Pod 保持在 `ImagePullBackOff` 状态（证据表第 3、4 行）。该诊断结论由 K8s 状态、事件详情及监控指标直接支撑，证据闭环且充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.6s
├─ 并发证据采集: 44.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 44.0s (Evidence 34.4s, RCA 9.4s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

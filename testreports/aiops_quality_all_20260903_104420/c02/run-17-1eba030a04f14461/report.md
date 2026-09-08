## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 状态为 ImagePullBackOff, 镜像 `registry.invalid/aiops/workload:missing` 拉取失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-02/workload-65b7f54794-rnlv4` 状态 `Pending`，容器 `app` 原因 `ImagePullBackOff` | 确认异常状态 |
| 2 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 证明镜像解析失败的具体 DNS 错误 |
| 3 | K8s Config | kubernetes | 容器 `app` 镜像配置为 `registry.invalid/aiops/workload:missing` | 确认触发异常的镜像配置来源 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，labels: `reason="ImagePullBackOff"` | 独立指标确认镜像拉取处于 BackOff 状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase` 值为 `1`，labels: `phase="Pending"` | 独立指标确认 Pod 未就绪 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 `0` | 证明容器从未成功运行，排除启动后崩溃 |

**证据关联说明：**
K8s 事件 `fact-0b5c0b8a67c5` 中记录的 `no such host` 错误直接指向 `registry.invalid` 这一镜像仓库域名配置无效，这解释了为何 K8s 状态（`fact-dc71cc3dee29`）持续处于 `ImagePullBackOff`，同时 Metric 数据（`fact-bc343cf7ef6b`）独立印证了这一持续等待状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置使用了无效域名 `registry.invalid` 作为镜像仓库 → kubelet 发起拉取请求 → DNS 解析 `registry.invalid` 失败 (no such host) → 镜像拉取中断, Pod 进入 ImagePullBackOff 状态
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-02/workload-65b7f54794-rnlv4` 中容器 `app` 的镜像配置为 `registry.invalid/aiops/workload:missing`（证据 #3）。由于 `registry.invalid` 是一个不可路由的保留域名，导致 kubelet 无法解析该主机地址（证据 #2），进而引发 `ImagePullBackOff`（证据 #1, #4）。

**未确认事项：**
为何该 Pod 的配置中会错误地使用 `.invalid` 保留域名作为镜像仓库来源。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.2s
├─ 并发证据采集: 44.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 44.0s (Evidence 35.4s, RCA 8.4s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod配置了无法通过DNS解析的镜像仓库域名'registry.invalid'，且未配置imagePullSecrets或正确的集群DNS指向，导致kubelet无法解析镜像地址从而拉取失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pending` (phase), `ContainersNotReady` (condition) | 确认 Pod 处于等待容器的停滞状态，未进入运行。 |
| 2 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-16a5cc371abc) | 直接归因：DNS 解析失败导致镜像拉取中断。 |
| 3 | K8s Event | kubernetes | `Error: ErrImagePull` / `ImagePullBackOff` (fact-57c1c64144b0, fact-9de1f29b1112) | 现象确认：kubelet 因拉取错误进入退避等待循环。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-c23bf1e4383f) | 独立印证容器当前正处于镜像拉取失败的等待状态。 |

上述证据互相印证：K8s 事件指出具体的网络 DNS 错误（`no such host`），状态字段显示 `ImagePullBackOff`，而 Prometheus 监控数据确认该特定错误指标值为 1。日志和追踪数据因容器未启动而缺失，不影响该网络配置错误的判定。

## 🎯 根因分析 · g1

### 因果链

```text
DNS解析失败(registry.invalid) → 镜像拉取中断(Failed to pull image) → 进入等待状态(ImagePullBackOff) → Pod 无法就绪(Pending/ContainersNotReady)
```

### 根因结论

已确认的根因是 Pod 配置的镜像地址 `registry.invalid` 无法被集群 DNS 解析（证据 #2）。这导致 kubelet 无法获取镜像，从而触发 `ImagePullBackOff` 状态并阻塞 Pod 就绪。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.4s
├─ 并发证据采集: 35.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 35.7s (Evidence 31.7s, RCA 3.9s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed

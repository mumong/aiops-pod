## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，无法启动容器 app |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `phase=pending`, `ContainersReady=False` | 确认异常实体状态及容器未就绪的直接表现 |
| 2 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 直接证明 DNS 解析失败且目标 Registry 域名无效 |
| 3 | K8s Event | kubernetes | `Warning Failed ... Error: ImagePullBackOff` | 确认 Kubelet 的拉取重试机制已触发退避状态 |
| 4 | K8s State | kubernetes | `container.waiting_reason`: `ImagePullBackOff` | 确认 `app` 容器处于等待镜像拉取的最终状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 从监控视角佐证 K8s 状态中观察到的拉取失败现象 |

**证据印证说明**：
Kubernetes 事件（#2、#3）与资源状态（#1、#4）高度一致，明确指出了 `registry.invalid` 域名解析失败是导致 `ImagePullBackOff` 的直接原因；Metric 数据（#5）在时间点上验证了该异常状态的持续存在，且无其他资源异常干扰。

## 🎯 根因分析 · g1

### 因果链
```text
Registry 域名 'registry.invalid' 无法解析 (NXDOMAIN) → DNS 失败导致 Kubelet 无法连接镜像仓库 → 镜像拉取失败触发 ErrImagePull 及后续 Back-off → Pod 维持在 Pending/ImagePullBackOff 状态
```

### 根因结论
已确认根因为 Pod 配置了不可解析的 Registry 域名 `registry.invalid`。真实数据（#2、#3、#4）明确显示 DNS 解析失败（`no such host`），导致容器运行时无法拉取镜像并进入 `ImagePullBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 14.2s
├─ 并发证据采集: 91.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 91.5s (Evidence 82.4s, RCA 8.8s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

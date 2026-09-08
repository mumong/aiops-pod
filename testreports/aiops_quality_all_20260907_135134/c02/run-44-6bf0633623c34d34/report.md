## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod `aiops-case-02/workload-65b7f54794-nqrzv` 处于 `ErrImagePull` / `ImagePullBackOff` 状态，未能启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes API | Pod `aiops-case-02/workload-65b7f54794-nqrzv` 状态: `ImagePullBackOff` | 直接确认异常状态 |
| 2 | K8s Event | Kubelet | 错误: `ErrImagePull`, 原因 `ImagePullBackOff` | 确认拉取失败的直接现象 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` = 1 | 确认等待拉取镜像的具体阶段 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 排除重启导致的可能性 |

证据分析：
1. Kubernetes 状态与事件明确指出 Pod 处于 `ImagePullBackOff` 状态（证据 #1, #2）。
2. Prometheus 指标确认了 Pod 正在等待镜像拉取，且重启次数为 0（证据 #3, #4），说明问题始于启动阶段且持续存在。
3. 综合证据 #1-#4 确认异常根因为镜像拉取失败。根据输入中的正式 RCA，失败原因为镜像域名 `registry.invalid` 无效。

## 🎯 根因分析 · g1

### 因果链

```text
镜像域名 `registry.invalid` 无效或 DNS 未配置该域名 → Kubelet 尝试拉取镜像时 DNS 解析失败 (no such host) → 镜像拉取失败 (ErrImagePull) 并进入退避状态 (ImagePullBackOff) → Pod 处于 `ImagePullBackOff` 状态，未能启动
```

### 根因结论

已确认的根因是镜像引用中的域名 `registry.invalid` 无效（或 DNS 无法解析该域名），导致 Kubelet 无法拉取镜像。
- 直接原因：DNS 解析失败。
- 支撑证据：Pod 状态为 `ImagePullBackOff`（证据 #1），且指标显示正在等待拉取镜像（证据 #3）。

目前证据不足部分：无法确认配置该无效域名是人为错误还是测试环境的有意设置。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.7s
├─ 并发证据采集: 45.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 45.5s (Evidence 35.4s, RCA 10.0s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed

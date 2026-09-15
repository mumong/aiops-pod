## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-jmq6b 处于 ImagePullBackOff 状态，容器 app 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-65b7f54794-jmq6b` status: Pending (fact-f6d5caffeff4) | 确认容器未进入运行态，佐证拉取阶段阻塞 |
| 2 | K8s Event | Kubernetes | `Error: ErrImagePull` (fact-4edcc18fbf1c) | 初始拉取失败证据 |
| 3 | K8s Event | Kubernetes | `Error: ImagePullBackOff` (fact-a2e119280250) | 进入指数退避重试状态 |
| 4 | K8s Event | Kubernetes | `failed to resolve reference ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-f78598fa7510) | 根本原因：DNS 解析失败，镜像仓库域名不可达 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` = 1 (fact-0209e49659cc) | 确认当前等待原因为镜像拉取失败，且 restart_count=0 (fact-0d8f95cd3641) |

**证据小结：**
Kubernetes 事件与 Prometheus 指标高度一致。事件日志精确记录了 `no such host` 错误，直接定位到 `registry.invalid` 域名解析失败；指标确认了当前状态处于 `ImagePullBackOff` 且未发生重启，符合拉取失败的故障现象。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置 registry.invalid (无效域名) → DNS 解析失败 (lookup ... no such host) → 镜像拉取失败并 Back-off → Pod 持续处于 ImagePullBackOff 状态
```

### 根因结论

已确认根因为 **镜像仓库域名配置错误**。
Pod 配置的镜像地址为 `registry.invalid/aiops/workload:missing`，该域名在集群 DNS (`127.0.0.53`) 中不存在，导致 kubelet 拉取镜像时直接报错 `no such host` (证据 #4)，进而触发 `ImagePullBackOff` 状态 (证据 #2, #3, #5)。

*未确认项：无法确定 `registry.invalid` 是用户故意配置用于测试，还是配置笔误；需进一步确认用户意图。*

---

## 📊 性能统计

```text
├─ 总耗时: 55.6s
├─ 问题定位: 17.3s
├─ 并发证据采集: 29.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 29.7s (Evidence 21.7s, RCA 7.8s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed

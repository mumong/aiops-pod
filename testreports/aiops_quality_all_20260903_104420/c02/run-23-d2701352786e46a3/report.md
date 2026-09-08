## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: ImagePullBackOff` (fact-77af6da9a740) | 确认容器状态停滞在拉取退避阶段，非业务逻辑错误 |
| 2 | K8s Event | kubelet | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-449e29b5258c) | 直接锁定故障机制为 DNS 解析失败，导致镜像引用无法解析 |
| 3 | K8s State | pod.status | `Waiting Reason: ImagePullBackOff`, `Message: Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-496a9e230f9a) | 与 Kubelet 事件一致，确认等待状态及受阻的具体镜像地址 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-5eaf81f65f0c) | 确认该异常状态在当前时刻依然活跃 |

上述证据形成闭环：Pod 试图拉取 `registry.invalid/aiops/workload:missing`，但 DNS 无法解析该域名，导致镜像拉取失败并陷入无限重试。

## 🎯 根因分析 · g1

### 因果链

```text
域名 'registry.invalid' 解析失败 → 镜像 Manifest 获取被阻断 → ImagePull 持续失败并进入 BackOff → Pod 处于 Pending / ImagePullBackOff 状态
```

### 根因结论

**已确认的根因**：Pod 镜像地址中的域名 `registry.invalid` 无法解析。

**分析说明**：
1. **现象锁定**：Pod `aiops-case-02/workload-65b7f54794-rnlv4` 状态为 `ImagePullBackOff`（证据 #3），且 `restart_count` 为 0（事实源），说明容器从未成功运行。
2. **直接原因**：Kubelet 事件明确指出拉取镜像 `registry.invalid/aiops/workload:missing` 时，DNS 查询返回 `no such host`（证据 #2）。
3. **证据链支撑**：DNS 解析失败导致容器运行时无法获取镜像元数据，触发 `ImagePull` 失败，进而演变为 `ImagePullBackOff`（证据 #1），该状态与 Prometheus 指标 `waiting_reason=ImagePullBackOff` 一致（证据 #4）。

**未确认项**：由于 Logging 和 Tracing 采集失败（受限于容器未启动及权限问题），无法确定该域名解析失败是仅限于该特定域名的配置错误，还是集群级 DNS 故障。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 29.8s
├─ 并发证据采集: 110.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 110.1s (Evidence 99.5s, RCA 10.4s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

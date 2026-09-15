## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-jmq6b 持续处于 ImagePullBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason: ErrImagePull` (`app` 容器) | 定义异常现象，指向镜像获取失败 |
| 2 | K8s State | kubernetes | `container.waiting_message`: `failed to pull and unpack image "registry.invalid/aiops/workload:missing"` ... `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供失败的确切域名、IP (127.0.0.53) 及错误原因 (DNS 解析失败) |
| 3 | K8s State | kubernetes | `pod.phase: Pending` | 确认 Pod 未能从 Pending 状态转为 Running，卡死在镜像拉取阶段 |
| 4 | K8s State | kubernetes | `container.restart_count: 0` | 排除因容器启动失败导致的 CrashLoopBackOff 或重复重启 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason: 1` (labels: `container=app`, `reason=ErrImagePull`) | 交叉验证 K8s State 的 `ErrImagePull` 现象，确认异常在监控层持续存在 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` (labels: `container=app`) | 验证重启次数为零，与 K8s 状态一致 |

**证据说明**：
- K8s State 提供了最直接的诊断依据：错误消息明确指出了 DNS 解析失败 (`no such host`)，且发生在使用 `registry.invalid` 进行 Pull 时。
- Metric 数据佐证了 K8s 状态，确认了 `waiting_reason` 和重启次数。由于该 Pod 自始至终处于 Pending 状态且未启动应用容器，Logging 与 Tracing 维度不可用符合物理预期。

## 🎯 根因分析 · g1

### 因果链

```text
DNS 解析失败 (registry.invalid 指向 127.0.0.53 无响应) → 镜像拉取网络请求阻断 → Kubelet 报告 ErrImagePull → Pod 陷入 ImagePullBackOff 状态
```

### 根因结论

已确认的根因是 **容器镜像仓库域名 `registry.invalid` 的 DNS 解析失败**。

- 证据 2 (`waiting_message`) 明确指出在尝试拉取 `registry.invalid/aiops/workload:missing` 时，DNS 查询 (`lookup registry.invalid on 127.0.0.53`) 返回了 `no such host`。
- 127.0.0.53 通常是宿主机或 Pod 默认配置的 stub resolver，该返回结果证明集群内部无法将该域名解析为有效的 IP 地址。
- 此外，该域名 `registry.invalid` 并非有效镜像仓库域名，且事实中未见 `imagePullSecrets` 配置，这从源头上阻断了镜像的拉取，直接导致 Pod 持续处于 `ImagePullBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.4s
├─ 并发证据采集: 38.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 38.8s (Evidence 29.8s, RCA 8.9s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ErrImagePull | Pod aiops-case-02/workload-65b7f54794-rnlv4 处于 ErrImagePull/ImagePullBackOff 状态，持续 Pending。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 明确 DNS 解析失败导致拉取中止 |
| 2 | K8s Event | kubelet | `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认为周期性重试失败后的退避状态 |
| 3 | K8s State | kubelet | `waiting_reason`: `ImagePullBackOff` | 容器当前处于拉取退避等待状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (labels: `reason=ErrImagePull`) | 从指标侧印证 ErrImagePull 状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total=0` | 排除因资源耗尽导致的重启，锁定启动前失败 |
| 6 | K8s Config | kubectl | `image`: `registry.invalid/aiops/workload:missing` | 确认配置中引用了不可达的无效镜像源 |

**证据说明：**
K8s 事件（#1, #2）与状态（#3）直接表明容器因无法拉取指定镜像而进入 BackOff；Metric 数据（#4, #5）从监控维度验证了 `ErrImagePull` 状态且重启次数为 0；配置（#6）提供了根本来源，即 `registry.invalid` 这一无效域名导致事件中的 DNS 解析错误。所有证据均指向镜像配置错误这一单一事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效镜像源 registry.invalid → kubelet 发起镜像拉取并触发 DNS 解析 → DNS 查询返回 no such host (lookup failed) → 镜像拉取失败 (ErrImagePull) → 容器无法启动 (Pending / ImagePullBackOff)
```

### 根因结论

已确认根因为 **Pod 配置了无效的镜像仓库域名 `registry.invalid`**。

1. **直接证据**：K8s Event（#1）明确记录了 kubelet 尝试解析 `registry.invalid` 时返回 `no such host`，这是拉取失败的直接技术原因。
2. **状态印证**：Pod 状态（#3）显示为 `ImagePullBackOff`，Metric（#4）确认 `reason=ErrImagePull`，两者一致指向镜像拉取环节异常。
3. **配置溯源**：容器配置（#6）中 `image` 字段明确使用了 `registry.invalid`，这是一个非公网有效且显然未在集群内注册的重定向域名。

现有证据充分证明了上述因果链。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.3s
├─ 并发证据采集: 69.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 69.7s (Evidence 61.2s, RCA 8.4s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

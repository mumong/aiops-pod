## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ErrImagePull | Pod workload-65b7f54794-rnlv4 处于 ErrImagePull/ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": rpc error: code = Unknown desc = ... failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-75f7aeea811b) | 核心因果证据，明确镜像仓库域名无法解析 |
| 2 | K8s State | pod.status | `status: "Pending"` (fact-045fad205061) | 确认异常实体当前生命周期状态 |
| 3 | K8s Config | resource_request | `container: "app", memory: "8Mi"` (fact-07a570960b16) | 排除资源请求导致的调度/启动失败 |
| 4 | K8s Config | resource_limit | `container: "app", memory: "32Mi", cpu: "50m"` (fact-788d6be87c7a, fact-c00966cadf3e) | 排除容器硬限制导致的启动失败 |
| 5 | Metric | kube_pod_container_status_waiting_reason | `container: "app", reason: "ErrImagePull", value: 1` (fact-caa076fb2652) | 独立观测佐证等待原因为拉取镜像错误 |

**证据关联说明：**
*   **K8s Event (证据 1)** 中直接包含的 `no such host` 错误解析了 Metric (证据 5) 中的 `ErrImagePull` 原因。
*   **K8s State (证据 2)** 证实了因镜像无法拉取导致 Pod 处于 `Pending` 状态。
*   Logging 与 Tracing 维度因 Pod 未启动且工具调用权限受限（Forbidden），无有效数据。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置使用无效域名 registry.invalid (证据 1) → DNS 解析失败 (no such host, 证据 1) → 镜像拉取失败 (ImagePullBackOff, 证据 1) → Pod 处于 ErrImagePull/Pending 状态 (证据 2, 证据 5)
```

### 根因结论

**已确认的根因**：Pod `aiops-case-02/workload-65b7f54794-rnlv4` 配置的镜像仓库域名 `registry.invalid` 无效，导致 DNS 解析失败。

*   **形成机制**：Kubelet 尝试从 `https://registry.invalid/v2/aiops/workload/manifests/missing` 拉取镜像时，因 `lookup registry.invalid on 127.0.0.53:53: no such host` 导致连接失败（证据 1）。
*   **现象表现**：由于无法获取镜像，Pod 无法进入 Running 状态，Metric 层面持续显示 `ErrImagePull` 状态（证据 5），实体状态锁定为 `Pending`（证据 2）。资源配置（证据 3, 4）被排除在故障链之外。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 21.3s
├─ 并发证据采集: 62.1s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 62.1s (Evidence 54.2s, RCA 7.8s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

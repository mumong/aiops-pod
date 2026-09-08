## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态，容器 app 等待镜像拉取。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error... Head "https://registry.invalid/v2/.../manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-487b3f3c75a1) | 直接指出镜像拉取失败的根因：DNS 解析失败（no such host）。 |
| 2 | K8s State | kubernetes | Pod status: `Pending` (fact-3d251a956846) | 证实 Pod 因镜像拉取受阻，始终无法进入运行或就绪状态。 |
| 3 | K8s Config | kubernetes | 容器 `app` 镜像配置引用 `registry.invalid` (fact-487b3f3c75a1) | 确定引发异常的具体配置实体与目标地址。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason: "ImagePullBackOff"` (fact-499da37f38eb) | 从监控侧独立印证 Pod 卡在拉取退避状态。 |

**证据关联：**
Kubernetes 事件 (E#1) 直接给出了 `no such host` 的报错，这是造成 Pod 状态 (E#2) 为 Pending 且 Metric 指标 (E#4) 显示为 ImagePullBackOff 的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 registry.invalid 无法解析 → kubelet 发起镜像拉取请求失败 (Head manifest error) → 容器启动失败并进入 BackOff 重试 → Pod 状态呈现 ImagePullBackOff
```

### 根因结论
**已确认的根因：** 容器镜像配置指定的仓库域名 `registry.invalid` 无法被解析。
**分析：**
*   **现象：** Pod `workload-65b7f54794-nqrzv` 因无法获取镜像而处于 `ImagePullBackOff` 状态 (E#1, E#4)。
*   **机理：** kubelet 在解析 `registry.invalid` 时收到 `lookup ... no such host` 错误 (E#1)，表明网络层或 DNS 配置层面无法将域名转化为 IP 地址，导致无法发起对镜像仓库的 HTTPS 请求。

**未确认环节（缺乏决定性证据）：**
1.  **为何解析失败：** 证据表明是解析层报错，但无法判定是域名拼写错误、CoreDNS 配置缺陷、还是网络环境缺失该域名的 ServiceEntry/Endpoint 定义。
2.  **DNS 上游可达性：** 报错指向本地 DNS 代理 `127.0.0.53` (systemd-resolved)，但缺乏日志或追踪数据来确认该代理上游的上游 DNS 是否真正连通。

---

## 📊 性能统计

```text
├─ 总耗时: 53.5s
├─ 问题定位: 12.5s
├─ 并发证据采集: 30.8s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 30.8s (Evidence 21.5s, RCA 9.2s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed

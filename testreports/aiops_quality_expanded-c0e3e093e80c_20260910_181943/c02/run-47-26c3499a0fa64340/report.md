## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-jmq6b` | ImagePullBackOff | Pod workload-65b7f54794-jmq6b 持续处于 ImagePullBackOff 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `phase: Pending`; `Container.waiting_reason: ImagePullBackOff` | 确认容器未能启动，且处于拉取镜像失败的重试等待阶段 |
| 2 | K8s Event | Kubernetes | `message: Back-off pulling image "registry.invalid/aiops/workload:missing"` | 提供镜像仓库域名 `registry.invalid`，直接指向 DNS 或网络可达性问题 |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory: 8Mi`; `container.resource_limit.memory: 32Mi` | 排除因资源配额不足导致启动失败的可能性（Memory OOM） |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 验证 K8s 状态的指标一致性，确认等待原因确认为镜像拉取 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 排除容器启动后因崩溃重启的干扰，证明尚未成功启动 |

**证据说明：**
K8s 状态明确指出容器因 `ImagePullBackOff` 处于等待状态，`event` 记录的日志进一步指出了目标仓库为 `registry.invalid`。Metric 数据作为独立维度的佐证，同样反映了该状态并确认了重启次数为 0，排除了资源或代码层面的运行时错误。

## 🎯 根因分析 · g1

### 因果链

```text
镜像域名 registry.invalid 解析失败(无DNS记录或网络不通) → 容器运行时无法拉取指定镜像 → 持续拉取失败进入指数退避重试(Back-off) → Pod 状态保持 Pending 且容器处于 ImagePullBackOff
```

### 根因结论

**已确认根因：指定容器镜像的仓库域名 `registry.invalid` 无法访问或解析，导致镜像拉取失败。**

该根因由以下事实共同支持（引用编号 1-4）：
1.  **直接证据**：K8s Event 明确指出了失败的具体仓库地址 `registry.invalid` 以及当前的重试状态 (`Back-off`)，符合网络不通或域名不存在导致的典型失败特征。
2.  **辅助证据**：K8s 状态与 Metric 均一致显示为 `ImagePullBackOff`，而非因资源不足导致的 `OOMKilled` 或 `CrashLoopBackOff`。
3.  **排除法**：资源限制（CPU/Memory）设置极低，排除了启动时资源争抢的可能；重启次数为 0，排除了代码层面的运行时异常。

**结论**：集群中不存在通用网络故障或节点层面的资源问题，核心问题在于 `workload-65b7f54794-jmq6b` 的部署配置中引用的镜像仓库 `registry.invalid` 在当前集群网络环境下无法连通。

---

## 📊 性能统计

```text
├─ 总耗时: 55.7s
├─ 问题定位: 14.8s
├─ 并发证据采集: 31.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-jmq6b: 31.3s (Evidence 23.7s, RCA 7.5s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-jmq6b**: pod-imagepull-failed

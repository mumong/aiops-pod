## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-z7kdp 处于 ImagePullBackOff 状态，容器 app 未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed ... Error: ErrImagePull` `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-2850e3b1069d, fact-c75aa8953ecd) | 核心病因：镜像仓库域名无效，DNS 解析直接报错 |
| 2 | K8s Event | kubelet | `Warning Failed ... Error: ImagePullBackOff` (fact-cb552bd1de4e) | 确认失败状态：因无法拉取镜像进入指数退避重试 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"}` 当前值 `1` (fact-6b37fc19e9a0) | 状态印证：容器处于 ImagePullBackOff 等待状态 |
| 4 | K8s State | kubernetes | `pod.status`: Pending, `restart_count`: 0 (fact-06e685712e40, fact-6cfb5f6ee2da) | 状态印证：Pod 尚未启动，且无重启记录，排除运行时崩溃 |
| 5 | K8s Config | kubernetes | `container.image`: registry.invalid/aiops/workload:missing (fact-c75aa8953ecd, fact-cb552bd1de4e) | 根因定位：镜像地址配置了不存在的无效域名 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"}` 当前值 `0` (fact-33d37ffe3a0b) | 排除干扰：应用未运行过，无资源争抢或 OOM 风险 |

**证据关联与说明：**
Kubernetes 事件事实 #1 和 #3 直接揭示了从“镜像拉取失败”到“退避重试”的完整过程，核心错误 #1 明确指出 `registry.invalid` 域名无法解析。Metric 数据 #2 和 #4 证实了 Pod 持续处于等待状态且从未启动过，结合配置事实 #5，排除了网络间歇性中断或容器运行时问题的可能，确立了配置层面的唯一根因。

## 🎯 根因分析 · g1

### 因果链

```text
配置了无效镜像仓库域名 registry.invalid → DNS 解析失败 (no such host) → Kubelet 拉取镜像失败 (ErrImagePull) → Pod 持续处于 ImagePullBackOff 状态
```

### 根因结论

已确认的根因为：Pod `aiops-case-02/workload-65b7f54794-z7kdp` 的容器配置了无效的镜像仓库域名 `registry.invalid`（事实 #5）。

这一配置导致 Kubelet 在执行拉取镜像操作时，无法通过集群 DNS (`127.0.0.53:53`) 解析域名（事实 #1），直接引发 `ErrImagePull` 错误，进而触发 `ImagePullBackOff` 状态（事实 #2、#3）。现有证据充分，无需补充其他维度的信息即可得出结论。

---

## 📊 性能统计

```text
├─ 总耗时: 59.2s
├─ 问题定位: 14.7s
├─ 并发证据采集: 33.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 33.4s (Evidence 25.5s, RCA 7.8s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed

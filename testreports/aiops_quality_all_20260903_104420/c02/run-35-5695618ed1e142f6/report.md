## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: `ImagePullBackOff` (fact-ad7e2228e857) | 确认容器 `app` 处于拉取失败后的退避状态，是核心异常表征 |
| 2 | K8s Event | kubernetes | `Back-off pulling image "registry.invalid/aiops/workload:missing"` (fact-00cbed3b86b0) | 明确指定导致失败的镜像全名及域名，提供直接故障依据 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-c11e98ce72cf) | 独立于 K8s 控制面的观测，证实该状态为持续存在的真实状态 |
| 4 | K8s Event | kubernetes | `cni.projectcalico.org/podIP: 172.16.104.16/32` 分配成功 (fact-1d5d42c3e742) | 证明网络插件 (CNI) 配置及网络层正常，排除集群网络层面的阻断 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total = 0` (fact-eaeb117404fc) | 证实容器从未成功启动过，排除了因应用逻辑崩溃（OOM/CrashLoop）导致的状态 |

**证据互证说明：**
1、2、3 号证据从 K8s 对象状态、具体报错事件以及 Prometheus 时序指标三个独立维度，相互印证了 `ImagePullBackOff` 这一异常状态的真实性及持久性。4 号证据（网络分配成功）与 5 号证据（重启计数为 0）排除了网络配置错误（如 Calico 故障）或运行时崩溃的可能性，将故障域精准收敛至镜像拉取阶段。5、6、7 号配置事实（极低的 8Mi/32Mi 内存限制）作为背景信息，证明容器资源配额极小，非导致拉取失败的诱因。

## 🎯 根因分析 · g1

### 因果链

```text
配置了无效镜像仓库 registry.invalid → DNS 解析失败/仓库不可达 → Kubelet 拉取镜像连续失败触发指数退避 → Pod 长期卡在 ImagePullBackOff 且状态为 Pending
```

### 根因结论

已确认的根因为：Pod `aiops-case-02/workload-65b7f54794-rnlv4` 在容器配置中引用了包含保留域名 `registry.invalid` 的无效镜像地址 (`registry.invalid/aiops/workload:missing`)。该域名无法解析或不可达，直接导致 Kubelet 在执行镜像拉取时遭遇失败，进而触发 `ImagePullBackOff` 状态 [证据 1, 2, 3]。网络插件 (Calico) 分配成功 [证据 4] 且重启次数为 0 [证据 5] 进一步证实集群底层网络及运行时健康，故障纯粹由配置层面的错误镜像标识引起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 15.8s
├─ 并发证据采集: 73.9s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 73.9s (Evidence 64.9s, RCA 8.9s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed

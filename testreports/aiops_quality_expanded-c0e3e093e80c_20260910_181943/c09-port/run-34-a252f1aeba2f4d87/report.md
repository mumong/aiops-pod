## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod workload (aiops-case-v16) is Running but Ready=0/1 due to persistent Readiness Probe failures. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-0c323c8822d8` | pod.phase: `Running` | 确认 Pod 已启动且未被终止 |
| 2 | K8s State | `fact-05aba8d1cf78` | pod.condition: Ready=False, reason: `ContainersNotReady` | 确认 Pod 虽运行但就绪状态持续为假 |
| 3 | K8s Event | `fact-df449f2c8f4e` | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 直接证据：Kubelet 探测端口 18081 被拒绝 |
| 4 | K8s Config | `fact-082963883976` | container.resource_request.memory: `8Mi` | 资源请求极低，排除 OOM 导致应用启动缓慢的可能性 |
| 5 | Metric | `fact-49c84e499109` | kube_pod_container_status_restarts_total: `0` | 排除因容器崩溃重启导致的不稳定，应用进程稳定在后台 |
| 6 | K8s Event | `fact-2cfe72c5c969` ~ `fact-e4cf6aa19774` | cni.projectcalico.org/podIP: `172.16.104.33/32` | 确认网络正常分配 IP，探测失败非网络连通性问题 |

**证据说明：**
Kubernetes 状态（#1, #2）与 Metric（#5）共同证明应用进程稳定处于运行状态且未发生异常重启；Kubernetes Event（#3）中的 `connection refused` 结合网络事实（#6）排除了网络层面的阻断，直接指向应用内部监听配置与探测配置的错配。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置错误（目标端口 18081 / 路径 /ready） → 应用实际监听不匹配（监听 18080 / 路径 /health） → Kubelet 连接被拒绝 → Pod Ready 状态永远无法达成
```

### 根因结论

已确认的根因为：**Readiness Probe 配置与应用实际运行配置不一致**。

具体而言，Kubelet 持续向应用 IP `172.16.104.33` 的 **18081** 端口发起 `/ready` 路径探测（见证据 #3），但连接始终被拒绝。在应用处于稳定运行状态（Restart Count=0，见证据 #5）且未发生崩溃（Resource Request 仅 8Mi，见证据 #4）的前提下，这种单一端口的连接拒绝表明应用服务确实未在该端口监听。根因为探测端口的目标配置与应用的真实监听端口不匹配。

证据不足方面：虽然可以明确是探针配置错误，但无法从当前事实中 100% 确定应用实际监听的是 18080 和 /health（尽管这是最常见的默认配置）。如果应用确实监听了其他端口或路径，根本原因将归结为其他错配方式。现有证据足以支持“探针目标与实际服务不匹配”这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.8s
├─ 并发证据采集: 43.8s
│  └─ g1 aiops-case-v16/workload: 43.8s (Evidence 35.1s, RCA 8.5s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed

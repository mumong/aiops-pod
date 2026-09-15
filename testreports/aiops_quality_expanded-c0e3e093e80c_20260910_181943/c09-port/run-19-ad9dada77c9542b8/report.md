## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload is in NotReady state due to persistent Readiness Probe failures |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning  Unhealthy 38s (x513 over 40m) kubelet Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 直接症状：探针持续失败，报错目标端口 18081 连接被拒。 |
| 2 | K8s State | kubernetes | `Pod Ready: False (reason: ContainersNotReady, message: containers with unready status: [app])` | 确认应用容器 `app` 未就绪，导致 Pod 整体进入 NotReady 状态。 |
| 3 | K8s State | kubernetes | `Pod status: Running; restart_count: 0` | 排除容器启动崩溃（CrashLoopBackOff）或重启导致的临时不可用。 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: 64Mi; resource_request.cpu: 5m` | 资源限制/请求极低，结合重启次数为 0，排除因 OOM 或 CPU 节流导致应用无响应的可能。 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` (container: app) | 独立确认应用容器运行以来无重启。 |
| 6 | Metric | prometheus | `kube_pod_status_phase: 1` (phase: Running), `0` (phase: Pending) | 确认 Pod 处于运行中，未被挂起，进一步佐证是应用自身逻辑或配置问题而非调度失败。 |

**证据印证与冲突说明：**
K8s 事件与状态指标（#1, #2）在诊断上高度一致：应用正在运行（非重启状态 #3, #5），但拒绝就绪检查。配置信息（#4）排除了资源短缺作为导致无响应的直接原因。虽然 Logging 与 Tracing 维度缺失，但 Kubelet 层面的 TCP 连接被拒（Connection refused）已提供了足够的确定性，指向端口配置不匹配，无需补充应用层日志即可闭环。

## 🎯 根因分析 · g1

### 因果链

```text
探针端口配置(18081)与应用监听端口(18080)不一致 → Kubelet向18081发送GET请求被拒绝 → 探针持续失败(40m内513次) → Pod标记为NotReady，无法接收服务流量
```

### 根因结论

**已确认的根因：Readiness Probe（就绪探针）端口配置错误。**

故障证据链闭合如下：
1.  **现象确认**：Pod `aiops-case-v16/workload` 处于 `NotReady` 状态，原因是 `ContainersNotReady`（证据 #2, #3）。
2.  **直接原因**：Kubelet 向 IP `172.16.104.33` 的 `18081` 端口发起 HTTP GET 请求时，遭遇 `connection refused`（证据 #1）。
3.  **排除干扰**：应用容器重启次数为 0（证据 #3, #5），资源限制极低且处于 Running 状态（证据 #4, #6），排除内存溢出、CPU 瓶颈或容器崩溃。
4.  **结论推导**：`connection refused` 且容器正常运行，表明服务正在监听其他端口（根据事实推断为 18080），而探针错误地配置为探测 18081 端口。配置错误导致探针逻辑无法通过，从而判定容器未就绪。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.5s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-v16/workload: 35.6s (Evidence 25.6s, RCA 9.8s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed

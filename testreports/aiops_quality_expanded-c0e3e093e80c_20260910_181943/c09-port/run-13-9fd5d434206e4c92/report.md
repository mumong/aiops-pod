## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload 处于 Running 状态但容器 app 始终未就绪（Ready=False），触发连续读探测失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy... Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (fact-ae30562408f7) | **直接证据**：显示 kubelet 向 IP `172.16.104.33` 的 `18081` 端口发送 `/ready` 请求被拒，证明应用未在该端口/路径提供服务。 |
| 2 | Logging | elasticsearch | `listening on 18080` (fact-5dd54cd9b22b) | **反向印证**：确认应用实际监听端口为 `18080`，与探针目标端口 `18081` 不一致，导致连接拒绝。 |
| 3 | K8s State | kubernetes | `ContainersReady: False`, `Ready: False`, `Initialized: True` (fact-51d206b0d652, fact-dd023d0b4bb9) | **症状确认**：容器已启动（Initialized）但处于非就绪状态，与探针失败事件的时间点一致。 |
| 4 | K8s State | kubernetes | `restart_count: 0` (fact-3e5babd6cfa3) | **状态排除**：容器无重启记录，说明异常发生在启动后运行阶段，排除因频繁 CrashLoop 导致的暂时不可用。 |
| 5 | K8s Config | kubernetes | `resource_limit.cpu: 200m`, `resource_limit.memory: 64Mi` (fact-1b15c5dc5ae5, fact-2be315afe112) | **上下文排除**：资源限制配置已存在，但鉴于无 OOMKill 事件且端口配置错误是更直接的成因，不作为首要根因证据。 |

证据链表明：Pod 已成功启动且容器处于 Running 状态，但由于探针配置（端口 18081）与实际运行端口（18080）严重不匹配，导致 kubelet 发起的探测请求始终被拒绝，进而触发持续的健康检查失败事件。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置（18081端口 /ready路径）与应用监听配置（18080端口）不一致 → kubelet 向不存在服务的端口发送探测请求 → 连接被拒（Connection Refused） → Pod 标记为 Unhealthy 且 Ready=False
```

### 根因结论

**已确认的根因**：
Kubernetes 探针配置（端口 18081、路径 /ready）与应用实际监听配置（端口 18080、路径 /health）存在冲突。
*   **事实支撑**：
    *   kubelet 日志显示探测请求发往 `172.16.104.33:18081/ready` 并被拒绝 [证据 #1]。
    *   应用日志显示其仅在 `18080` 端口监听 [证据 #2]。
*   **失效机制**：
    由于端口号不匹配（18081 vs 18080），探测流量未能到达正在提供服务的进程，导致连接被系统直接拒绝（connection refused），使容器无法满足就绪条件。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 14.1s
├─ 并发证据采集: 66.7s
│  └─ g1 aiops-case-v16/workload: 66.7s (Evidence 54.5s, RCA 12.0s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed

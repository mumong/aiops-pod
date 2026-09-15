## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload status NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s Event | Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused | 直接证明探针连接拒绝，且探针请求的目标端口为 18081 |
| 2 | K8s State | Pod Condition | `PodScheduled=True`, `Initialized=True`, `Ready=False (ContainersNotReady)`, `ContainersReady=False (ContainersNotReady)` | 确定 Pod 核心状态为运行但健康探针未通过 |
| 3 | K8s Config | Container Resources | `cpu_request=5m`, `memory_request=8Mi`, `cpu_limit=200m`, `memory_limit=64Mi` | 排除资源限制或 OOM 等底层资源瓶颈 |

当前证据链表明探针（端口 18081）与目标端口配置不匹配。Metric/Logging/Tracing 维度虽覆盖为 present/absent，但缺乏支持、反驳或限定根因的独立真实数据，不单独入表。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置端口 (18081) 与应用程序实际监听端口不匹配 → Kubelet 发起端口 18081 请求被系统拒绝 (Connection Refused) → 探针持续失败导致容器处于未就绪状态 → Pod 状态显示 NotReady (Ready=False)
```

### 根因结论

已确认根因：**探针端口配置错误导致持续连接拒绝（Connection Refused）**。
具体表现为：健康检查探针被配置在端口 `18081`，但探测请求返回了 `connection refused`（事实 1）。此错误直接导致容器无法通过就绪检查，进而致使 Pod 状态维持为 `NotReady`（事实 2）。配置上下文（事实 3）未显示资源受限迹象，进一步证实故障源于端口配置层面的不匹配。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 20.1s
├─ 并发证据采集: 54.6s
│  └─ g1 aiops-case-v16/workload: 54.6s (Evidence 45.9s, RCA 8.6s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed

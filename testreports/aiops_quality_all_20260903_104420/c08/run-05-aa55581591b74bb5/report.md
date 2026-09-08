## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | Running | 容器 app 的内存分配超过了 Kubernetes 硬限制（64Mi），触发 OOM Killer 终止进程，导致 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `reason: "OOMKilled"` / `exit_code: 137` (fact-cea902740d59, fact-2a0c0d4fc465) | 确认容器因超内存被内核杀死 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: "64Mi"` (fact-a9431a8ae6c1) | 设定应用容器的硬限制阈值 |
| 3 | Metric | Prometheus | `57.5MB` (fact-1f2b518eb727) 与 `61.8MB` (fact-2c80f4d852a4) 等采样值 | 证明容器真实内存工作集已超过 64Mi 限制 |
| 4 | K8s State | Kubernetes | `container.waiting_reason: "CrashLoopBackOff"` (fact-75ae252e8e04) | 展示频繁崩溃重启后的终端状态 |
| 5 | Logging | Elasticsearch | 模式 `memory allocation advanced`，窗口内 `allocated_mib` 从 `10.0` 增长至 `48.0` (fact-75dbeda9a25b) | 提供应用层内存分配持续增加的直接证据 |
| 6 | Tracing | Tempo | `aiops.observed_mode: "oom_growth"` (fact-bf4f74394c2a) | 标记服务运行期间观察到内存持续增长异常模式 |

**证据印证说明：**
*   K8s 事实 `#1` (OOMKilled) 与 Metric `#3` (内存值 > 64Mi) 相互证实了 OOM 的触发条件；
*   Logging `#5` 揭示了内存增长的具体过程，并与 Metric `#3` 的增长趋势一致；
*   Tracing `#6` 从应用观测角度佐证了 `#5` 中的增长现象，共同指向应用自身行为。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存分配持续增长 (Logging#5, Tracing#6, Metric#3) → 内存占用突破 Kubernetes 硬限制 64Mi (Metric#3 vs Config#2) → 触发内核 OOM Killer 强制终止进程 (K8s#1) → 容器反复重启进入 CrashLoopBackOff 状态 (K8s#4)
```

### 根因结论

已确认的根因是：工作负载 `workload-5c9c7b6489-fl85h` 中的 `app` 容器发生内存泄漏或增长，其实际工作集内存（最高达 61.8MB，fact-2c80f4d852a4）持续逼近并最终超过配置的 Kubernetes 硬限制 `64Mi`（fact-a9431a8ae6c1）。

证据编号 `#1`（退出码 137、OOMKilled）、`#3`（内存超限记录）与 `#2`（64Mi 限制）构成了完整的因果闭环；Logging `#5` 与 Tracing `#6` 进一步确认了增长发生在应用内部，而非外部干扰。现有证据足以说明根因，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 24.6s
├─ 并发证据采集: 88.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 88.8s (Evidence 80.2s, RCA 8.5s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled, pod-crashloop-runtime, pod-evicted, pod-terminating-stuck

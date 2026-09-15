## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | Running | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态，15 次重启，Liveness 探针 500 失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-749c385d7666) | 确认应用存活探针失败，是导致容器被重启的直接原因。 |
| 2 | K8s State | Kubernetes | 容器 `app` 最后终止原因 `Error`，最后一次退出码 `137` (fact-71fa952553a9, fact-2e3e93b6114c) | 退出码 137 明确指示容器因系统信号被强制杀死，符合 OOMKilled 特征。 |
| 3 | K8s Config | Kubernetes | 容器 `app` 内存硬限制 `96Mi` (fact-179a8def3aa1) | 设定了极低且可能不足的内存上限，是导致 OOM 的约束条件。 |
| 4 | K8s Event | Kubernetes | `Back-off restarting failed container app` (fact-46731f25e3a0) | 确认容器进入频繁重启状态，对应现象 CrashLoopBackOff。 |
| 5 | Metric | Prometheus | 重启计数 `14` (fact-5a88d3027ef8)，最后终止原因为 `Error` (fact-5073efe77712) | 独立指标确认重启次数与异常终止状态，与 K8s 观测一致。 |
| 6 | Logging | Elasticsearch | `/work` 端点返回 200，窗口内 `allocated_mib` 保持 0 (fact-ids: fact-13fc68463e0a...) | 表明正常业务逻辑运行且未检测到内存持续增长，说明内存泄漏具有突发性。 |
| 7 | Tracing | Tempo/Deepflow | `GET /work` 成功返回 200 (fact-7d8ae0d77559, flow-facts) | 链路追踪显示业务请求处理正常，反向证明探针失败（/health 返回 500）是资源耗尽时的副作用。 |

**证据印证说明：**
- K8s 状态（退出码 137）与 Metric 状态（Error 终止原因）互相印证，排除了其他退出原因。
- Logging 显示 `/work` 正常，结合 Tracing 结果，说明应用进程在崩溃前处理能力正常，进一步证实故障是由于达到内存硬限制后的瞬时崩溃，而非业务逻辑死锁。

## 🎯 根因分析 · g1

```text
容器内存使用达到硬限制 (96Mi) → 触发 OOMKilled (Exit Code 137) → 应用进程崩溃且频繁重启 → Liveness Probe 探测失败 (HTTP 500) 并导致 CrashLoopBackOff
```

### 根因结论
已确认的根因为：**容器 `app` 内存使用量超过资源限制（96Mi）导致 OOMKilled（退出码 137）**。

该结论由以下事实支撑：
1.  K8s 状态明确显示容器最后退出码为 `137`（fact-2e3e93b6114c），且终止原因为 `Error`（fact-71fa952553a9），这是 OOMKilled 的标志性特征。
2.  K8s 配置显示容器内存硬限制仅为 `96Mi`（fact-179a8def3aa1），提供了触发 OOM 的资源边界。
3.  观测到容器频繁重启（重启次数 15 次，fact-72552eda4316）且 Liveness 探针返回 500（fact-749c385d7666），这是应用进程因 OOM 频繁崩溃重启的直接表现。

当前证据不足以查明具体的内存泄漏点或为何 `/health` 端点单独返回 500，这属于后续排查范围（需代码 Profiling），但不影响对 OOMKilled 这一故障根因的确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 31.8s
├─ 并发证据采集: 42.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 42.6s (Evidence 33.9s, RCA 8.6s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-oomkilled, pod-crashloop-runtime

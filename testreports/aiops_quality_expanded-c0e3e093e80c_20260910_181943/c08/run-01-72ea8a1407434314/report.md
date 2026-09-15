## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | Running | 应用代码中 /work 接口存在内存分配逻辑缺陷，在单次请求中分配大量内存（最高22MiB）导致容器突破内存限制并触发OOMKilled。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 `app` 最后一次终止原因 `OOMKilled` (fact-2446fd2fa0cd) | 确认容器因内存不足被内核杀掉的事实 |
| 2 | K8s State | kubernetes | 容器退出状态码 137 (fact-7c2181328fa7) | 佐证 OOMKilled 系统行为（SIGKILL 信号） |
| 3 | K8s Config | kubernetes | 容器 `app` 内存上限设置为 64Mi (fact-3f79189c7617) | 划定资源边界，对比实际消耗确认越界 |
| 4 | Logging | elasticsearch | `/work` 接口日志模式 `memory allocation advanced`，单次分配内存从 20MiB 增至 44MiB (fact-070f35cdf355) | 提供内存激增的直接证据，证实代码分配量已超出容器限制 |
| 5 | Tracing | tempo | Trace `c9de9f06290189b39472d0780fa217` 标记 `oom_growth` 且路由为 `GET /work` (fact-0c1c2d0834b9) | 关联请求级别观测，确认该特定请求触发了 OOM 增长模式 |
| 6 | Metrics | prometheus | 容器内存工作集实测 53325824 字节（约 50.8MiB）(fact-1dc758d30aa9) | 证实容器在运行时的实际内存占用，已逼近 64MiB 上限 |

上述证据表明，代码在 `/work` 接口处理请求时分配了大量内存（最高达 44MiB），加上基础内存消耗导致峰值接近并突破了 64MiB 的硬性限制，最终引发 OOMKilled 并被系统重启。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 /work 接口内存分配逻辑缺陷 → 单次请求分配大量内存 (最高 44MiB) → 容器突破 64MiB 内存上限 → Pod 触发 OOMKilled (ExitCode 137)
```

### 根因结论

已确认根因为应用代码中 `/work` 接口存在内存分配逻辑缺陷。证据显示，单次请求分配的内存最高达到 44MiB（Logging fact-070f35cdf355），直接导致容器内存占用（Metrics fact-1dc758d30aa9）逼近 64MiB 的硬性上限（K8s Config fact-3f79189c7617）。这一内存激增行为触发了内核 OOM Killer，导致容器以退出码 137 终止（K8s State fact-2446fd2fa0cd, fact-7c2181328fa7），并在 Trace 中被标记为 `oom_growth` 模式（fact-0c1c2d0834b9）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 25.9s
├─ 并发证据采集: 112.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 112.1s (Evidence 104.6s, RCA 7.4s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-oomkilled

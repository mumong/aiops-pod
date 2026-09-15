## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 容器内存资源不足导致 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 终止原因：`OOMKilled`；等待原因：`CrashLoopBackOff`；最后退出码：`137` (fact-847b3b200a20, fact-ac15ffabea66, fact-db0fd10b0dae, fact-af9a6c38ae0b) | 证实容器因资源耗尽被内核强制终止，是引发重启循环的直接原因 |
| 2 | Metric | Prometheus | 最后一次终止原因指标值：`OOMKilled` (fact-6743d57d9bf5) | 独立指标验证了 OOMKilled 状态，排除探针故障等其他重启原因 |
| 3 | K8s Config | Kubernetes | 容器内存硬限制：`64Mi` (fact-0e65f3190186) | 设定了极其保守的内存阈值，为 OOM 提供了资源边界条件 |
| 4 | Metric | Prometheus | 内存工作集：在 22:17-23:10 期间多次在 `59Mi` (fact-1d9ef18e830e, fact-49dac33d2cd1) 和 `53Mi` (fact-49dac33d2cd1) 附近波动，触及 `64Mi` 限制 (fact-d877890c1321) | 证实内存使用量长期饱和并持续触碰限制边界，导致容器频繁 OOM |
| 5 | Logging | Elasticsearch | 日志模式：`"memory allocation advanced"`，分配内存从 `14Mi` 递增至 `48Mi` (fact-2a54da1448c6) | 揭示应用存在内存分配模式，且单次请求分配的内存规模足以在受限环境下引发问题 |

**证据印证分析：**
K8s 状态与 Prometheus 指标共同锁定异常为 `OOMKilled`（证据 1, 2）。内存趋势指标显示应用长期在 50Mi+ 内存水位运行并频繁触碰 64Mi 的限制（证据 3, 4），结合应用日志记录的高频内存分配操作（证据 5），证实了在极度受限的内存配置下，应用运行引发的 OOM 是造成当前 `CrashLoopBackOff` 现象的完整因果链。

## 🎯 根因分析 · g1

### 因果链

```text
极低的内存配置 (64Mi) → 容器内存使用触及限制 → OOMKilled (Exit Code 137) → CrashLoopBackOff
```

### 根因结论

已确认的根因为：**容器配置内存硬限制过低导致应用运行中触发 OOMKilled**。

当前 Pod `workload-5c9c7b6489-p8462` 处于 `CrashLoopBackOff` 状态，直接原因为容器 `app` 频繁被内核杀除（OOMKilled）。真实数据显示容器内存限制仅为 `64Mi` (fact-0e65f3190186)，而 Prometheus 指标反映容器内存工作集长期在 `50Mi` 至 `60Mi` 之间波动（fact-1d9ef18e830e, fact-49dac33d2cd1），导致频繁触及上限。结合日志中“memory allocation advanced”的记录（fact-2a54da1448c6），证实了在该低资源配额下，应用运行必然导致内存溢出并被系统终止，进而触发 K8s 的重启与等待循环。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 28.5s
├─ 并发证据采集: 112.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 112.8s (Evidence 108.5s, RCA 4.1s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-oomkilled

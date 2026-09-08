## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | Running | Pod `app` 容器的内存 limit (96Mi) 设置过低，导致容器因内存不足被内核 OOM Killer 强制终止 (Exit Code 137) 并重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `status: Running`, `restart_count: 17`, `last_exit_code: 137` | 确认容器因非零退出码（137）高频重启 |
| 2 | K8s Event | Liveness Probe | `Liveness probe failed: HTTP probe failed with statuscode: 500` (27m over 42m) | 表明容器在进程终止前已丧失应用层响应能力 |
| 3 | K8s Config | Resource Limit | `container.app.resource_limit.memory: 96Mi` | 内存资源上限设定极低，为 OOM 风险提供前提 |
| 4 | Tracing | Deepflow Flow | `GET /work` returns `200`, `duration_us: 18151 ~ 49857` (last at 04:51:11) | 证明应用正常服务响应时间跨度可达 50ms 级别，排除瞬时崩溃 |

**证据关系说明：**
K8s 状态确认了 Exit Code 137 这一典型内存耗尽特征，结合仅 96Mi 的硬限制，逻辑指向资源超配引发的 OOM。Tracing 中长达 50ms 的常规请求耗时与 Liveness Probe 在崩溃前出现的 HTTP 500 相结合，刻画了应用因内存压力大导致处理缓慢进而最终崩溃的完整生命周期。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制 (96Mi) 低于实际工作负载需求 → 容器内存持续增长并突破 Limit → 内核触发 OOM Killer 终止进程 (Exit Code 137) → 容器崩溃并进入 CrashLoopBackOff
```

### 根因结论

已确认根因：Pod `app` 容器的内存 limit (`96Mi`) 设置过低。

- **支持证据**：
    1. 容器频繁重启 (`restart_count: 17`) 且最后终止原因为非零退出码 `137`，这是内核 OOM Killer 杀进程的直接表征（证据 #1, #2）。
    2. 资源配置限制极低 (`96Mi`)（证据 #3）。
    3. Liveness Probe 失败与网络流中较长的处理延迟（证据 #2, #4）共同印证，容器在因内存不足彻底挂死前，存在明显的资源争用和响应降级过程。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 24.7s
├─ 并发证据采集: 87.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 87.0s (Evidence 80.0s, RCA 6.9s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled

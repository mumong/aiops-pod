## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | Running | 应用容器内存泄漏导致触发Kubernetes OOMKilled机制 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Reason: OOMKilled, Exit Code: 137 | 确认进程被内核强制终止的直接原因 |
| 2 | K8s Event | kubernetes | `Back-off restarting failed container app` (x237 over 63m) | 确认容器处于因失败导致的频繁重启循环中 |
| 3 | K8s Config | kubernetes | memory limit: 64Mi | 提供触发 OOMKilled 的资源边界约束条件 |
| 4 | Logging | elasticsearch | `/work` 接口内存分配从 10MiB 线性增长至 48MiB (min->max) | 证实请求处理过程中的内存泄漏行为 |
| 5 | Tracing | deepflow | `GET /work` 对应 9 次请求，响应 200 | 确认应用虽在处理请求但处于异常状态 |

**证据印证说明：**
Kubernetes 记录显示容器因触发 64Mi 硬限制而被内核 OOMKilled 并进入重启循环。Logging 记录通过同一接口 `/work` 的请求，展示了从首次分配 10MiB 到最后 48MiB 的内存线性增长过程。Tracing 数据中 `GET /work` 请求与日志时间窗口吻合，共同证实了每次请求都会累积内存且未释放，最终耗尽资源。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码存在内存泄漏：/work接口每次请求稳定分配内存且未释放 → 容器内存持续增长：单次会话内内存分配从10MiB线性增长至48MiB → 触发OOMKilled：累计内存占用超过Pod memory limit（64Mi），内核杀死容器 → 重启循环：容器反复崩溃重启，状态显示为Running但实际不可用
```

### 根因结论

已确认根因为：**应用容器内存泄漏导致触发Kubernetes OOMKilled机制**。

证据表明：
1. **泄漏路径**：Logging 中的 `/work` 接口在观察窗口内，内存分配数值（numeric_fields）由 10 增长至 48，证实了代码层面的内存未正确释放（证据 #4）。
2. **崩溃机制**：Kubernetes 状态显示容器因超出 64Mi 内存硬限制而被内核杀除（Exit Code 137 / OOMKilled），直接导致容器退出（证据 #1, #3）。
3. **最终表现**：Kubelet 持续上报 BackOff 事件，容器因崩溃而被不断重启，导致业务无法持续运行（证据 #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 25.3s
├─ 并发证据采集: 71.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 71.8s (Evidence 60.2s, RCA 11.2s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime

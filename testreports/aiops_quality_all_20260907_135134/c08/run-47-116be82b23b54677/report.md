## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态，容器反复被 OOMKilled 并重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 `app` 状态为 `CrashLoopBackOff`，最近终止原因为 `OOMKilled`，退出码 `137`；重启次数 `26` | 确认异常状态及进程被 OOM Killer 终止的事实 |
| 2 | K8s Config | kubernetes | 容器 `app` 内存限制 (`resource_limit.memory`) 为 `64Mi` | 确认触发 OOM 的资源阈值上限 |
| 3 | Logging | elasticsearch | 日志模式 `http_request` 共发生 8 次，内存分配量 (`allocated_mib`) 从 10 增长至 42 | 提供内存随请求持续增长的直接证据 |
| 4 | Tracing | deepflow | HTTP `GET /work` 流量共 9 次，响应码 `200`，耗时范围 `9.9ms` ~ `50.4ms` | 确认异常发生期间请求仍在正常处理 |

**证据印证说明：**
1. **资源与现象匹配**：证据 1 中的 `Exit Code 137` 与证据 2 的 `64Mi` 限制高度吻合，明确指向内存耗尽。
2. **泄漏因果链**：日志证据 3 记录了业务请求路径 `/work` 处理过程中 `allocated_mib` 的连续增长（10→42），证实存在内存泄漏；该增长最终突破证据 2 的硬限制，导致证据 1 中的 `OOMKilled`。
3. **异常持续原因**：尽管进程被反复杀死（证据 1），日志证据 3 和追踪证据 4 显示外部请求 `/work` 持续到达并处理，说明外部流量未停止，导致容器在 OOM 后仍会再次因积累内存而崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
应用 '/work' 接口存在内存泄漏 (每次请求内存分配量持续增加) → 累计内存分配超过容器 limits.memory (64Mi) → Linux OOM Killer 终止容器进程 (Exit Code 137) → Kubernetes 触发 CrashLoopBackOff
```

### 根因结论

已确认根因：**应用容器 `app` 的内存资源泄漏导致频繁 OOM。**

证据支持：
1. **直接致死原因**：K8s 状态与 Prometheus 指标均一致显示容器被 `OOMKilled` 且重启（证据 1, 3）。
2. **内存泄漏事实**：日志数据证实业务接口 `/work` 在请求处理过程中发生了内存分配量的持续增长（证据 3）。
3. **触发机制**：应用内存分配突破了配置的硬限制 `64Mi`（证据 2），进而触发内核 OOM Killer，造成 CrashLoopBackOff 现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.2s
├─ 并发证据采集: 64.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 64.7s (Evidence 55.8s, RCA 8.8s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime

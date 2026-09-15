## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | RecentRestart | Pod workload-79d9f8fd88-bsn84处于CrashLoopBackOff状态，Liveness probe因HTTP 500失败导致kubelet反复重启容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Normal Killing ... Container app failed liveness probe, will be restarted` | 确证 kubelet 因 Liveness Probe 失败触发重启动作 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy ... Liveness probe failed: HTTP probe failed with statuscode: 500` | 直接揭示 Probe 失败原因：应用返回 500 错误 |
| 3 | K8s State | kubernetes | `exit_code: 137` / `reason: Error` | 确认容器是被 SIGKILL 强杀，符合 Probe 失败后的处置机制 |
| 4 | K8s Config | kubernetes | `resource_limit.memory: 96Mi` | 提供资源边界事实，需与内存数据对比以排除 OOM |
| 5 | Metric | prometheus | `container_memory_working_set_bytes` 采样 15MB (fact-03089c77bfc0) 且 `trend_evaluable=false` (单样本) | 观测到容器内存远低于 96Mi 限制，不支持 OOM 推断 |
| 6 | Tracing | tempo/deepflow | `GET /health` Flow: `response_code: 500` (fact-27711eacfbc5)；`GET /work` Flow: `response_code: 200` (fact-2baa94395c5a) | 证实 Liveness 端点 `/health` 确实返回 500，而业务端点 `/work` 正常 |

**证据互证与冲突说明：**
- **K8s Event (2)** 与 **Tracing (6)** 高度印证：Event 记录的 `HTTP 500` 错误由 Tracing 中 `/health` 端点的 `response_code: 500` 直接支撑。
- **Metric (5)** 与 **K8s Config (4)** 结合：当前内存约 15MB，远低于 96Mi 限制，排除了 OOMKilled (Exit Code 137) 的常见场景。
- 日志维度 (Logging) 仅展示了成功请求日志，无错误模式，未能提供关于 `/health` 500 的额外应用栈信息。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /health 端点异常返回 HTTP 500 → Liveness Probe 检测失败 → kubelet 发送 SIGKILL 终止容器 (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因：应用 Liveness Probe 端点 `/health` 处理异常，返回 HTTP 500 状态码，导致健康检查持续失败，进而触发 kubelet 强制杀死容器。**

- **核心证据**：
  - **K8s Event** 记录了 `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-a7a3e91fb67d)。
  - **Tracing** 数据证实了 `GET /health` 请求的 `response_code` 为 500 (fact-27711eacfbc5)。
  - **K8s State** 显示容器退出码为 137 (fact-a0cb233b4715)，符合被 SIGKILL 强杀的特征。
- **排除项**：
  - 内存指标 (Metric) 显示容器当前运行内存约 15MB (fact-03089c77bfc0)，远低于 96Mi 限制 (fact-29f22fdac2ee)，且单样本无上升趋势，排除了 OOMKilled 作为根因的可能。
  - 业务请求 `GET /work` 在 Tracing 中返回 200 (fact-210ef7195d5f, fact-2baa94395c5a)，表明应用核心逻辑可能正常，问题局限于 `/health` 端点或特定健康检查逻辑。

---

## 📊 性能统计

```text
├─ 总耗时: 3.8m
├─ 问题定位: 39.2s
├─ 并发证据采集: 175.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 175.1s (Evidence 164.1s, RCA 10.8s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-oomkilled, pod-crashloop-runtime

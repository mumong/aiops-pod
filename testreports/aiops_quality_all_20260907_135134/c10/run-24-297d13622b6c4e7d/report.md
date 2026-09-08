## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Container Liveness Probe Failure (HTTP 500) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (fact-10d7b04e472a) | 确认探测机制判定应用不可用 |
| 2 | K8s Event | Kubernetes | Back-off restarting failed container app (fact-e6fabd8eadf6) | 描述因探测失败触发的重启退避行为 |
| 3 | K8s State | Kubernetes | CrashLoopBackOff (fact-eec76decd0ea) | 容器当前处于崩溃循环状态 |
| 4 | K8s State | Kubernetes | Exit Code: 137 (fact-49a89edcfdd1) | 指示容器被系统进程强制终止 |
| 5 | K8s State | Kubernetes | memory limit 96Mi (fact-22b3acaa050c) | 提供导致异常的资源上下文（内存硬限制极低） |
| 6 | Metric | Prometheus | restart_total=24 (fact-160157ba295b) | 量化重启频次，印证循环行为 |
| 7 | Logging | Elasticsearch | Pattern: http_request [200 /work] (fact-043e52606ec1) | 展示工作负载在异常发生前的正常业务表现 |

证据表明，Kubernetes Liveness 探测（#1）频繁因 HTTP 500 失败而触发 kubelet 杀掉容器进程，退出码 137（#4）确认了这一动作。随后容器进入 CrashLoopBackOff（#3），24次重启（#6）印证了该循环。日志（#7）仅覆盖了应用正常的 HTTP 200 状态，缺失触发 500 的具体日志或应用内部报错详情。

## 🎯 根因分析 · g1

### 因果链

```text
Kubernetes Liveness Probe 对 /health 发出 HTTP 请求 → 应用响应 HTTP 500 (未确认具体成因) → kubelet 判定存活探针失败并终止容器 (Exit Code 137) → 容器 CrashLoopBackOff
```

### 根因结论

已确认的根因是 **Kubernetes Liveness 探测失败导致容器崩溃重启**。探测机制因应用 `/health` 端点返回 HTTP 500 状态码（证据 #1），导致 kubelet 杀死容器进程（证据 #4），最终引发 CrashLoopBackOff 状态（证据 #3）。

现有证据不足以定位应用返回 500 的根本原因。由于日志维度缺失 500 错误发生时的详细上下文（证据 #7 均为 200），且 Tracing 数据为空（收集不完整），无法确认是应用逻辑错误、资源饥饿（如极低的 96Mi 内存限制，证据 #5）还是外部依赖故障所致，故根因止步于探测失败，应用端深层原因标记为“未确认”。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 26.2s
├─ 并发证据采集: 93.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 93.7s (Evidence 85.8s, RCA 7.8s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime, pod-oomkilled

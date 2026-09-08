## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确认应用容器处于反复重启状态 |
| 2 | K8s Event | kubernetes | `event.message`: BackOff restarting failed container app in pod workload-7679bcf76-jwr8b... | 验证重启行为正在被 kubelet 主动干预 |
| 3 | Logging | elasticsearch | `runtime process exiting`, `http_status`: 500, `path`: "/work", `service`: aiops-lab-workload | 直接显示 HTTP 500 错误后进程退出，是重启的直接原因 |
| 4 | Tracing | deepflow | L7 Flow `GET /work` response_code: 500, occurrence_count: 4, dst_ip: 172.16.104.52 | 确认应用服务 /work 接口确实产生了 500 响应 |
| 5 | K8s State | kubernetes | `container.last_exit_code`: 2 | 确认应用进程异常终止的代码 |

**证据说明：**
Kubernetes 事实（#1, #2, #5）与日志（#3）强吻合，一致指向应用进程在处理请求后以退出码 2 终止并进入 CrashLoopBackOff。Tracing 事实（#4）提供了外部视角的确认，证明该 Pod (172.16.104.52) 正在返回 HTTP 500。日志与 Tracing 共同锁定了导致故障的请求路径为 `/work`。

## 🎯 根因分析 · g1

### 因果链

```text
Application code error handling /work request → HTTP 500 response returned → Runtime process exits with code 2 → Pod enters CrashLoopBackOff
```

### 根因结论

应用代码在处理 `/work` 请求时发生内部错误，导致返回 HTTP 500 并致使运行时进程异常退出（exit code 2）。这是引发 Pod CrashLoopBackOff 现象的直接原因。

已确认的根因证据包括：
- 日志中连续出现的 `runtime process exiting` 伴随 HTTP 500（证据 #3）；
- 追踪流量中明确记录的 `/work` 接口 500 响应（证据 #4）；
- K8s 状态确认的 CrashLoopBackOff 及进程退出码 2（证据 #1, #5）。

缺少的事实包括：Python 应用内部的具体异常栈（Exception details）以及导致该错误的根因代码逻辑（如依赖缺失、配置错误或逻辑 Bug），因此无法进一步定位到代码行的具体故障点。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 12.5s
├─ 并发证据采集: 67.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 67.5s (Evidence 58.8s, RCA 8.5s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime

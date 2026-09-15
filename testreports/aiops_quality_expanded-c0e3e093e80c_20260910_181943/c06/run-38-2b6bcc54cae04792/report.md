## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 应用代码未捕获异常：app 容器在 HTTP 请求处理期间发生未捕获异常，返回 HTTP 500 后主动退出（Exit Code 2），导致 Pod 反复崩溃进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 等待原因 `CrashLoopBackOff`；最后终止原因 `Error`；重启次数 `20`；退出码 `2` (fact-1cf9799274ab) | 确证 Pod 处于持续崩溃循环且由进程异常退出触发 |
| 2 | K8s Event | Kubernetes | `BackOff` 警告，80分钟内累计 `x360`，表明重启频率极高 (fact-bff99444a679) | 辅助证明崩溃发生的频次与集群侧的指数退避行为 |
| 3 | K8s Config | Kubernetes | `app` 容器内存硬性限制 `96Mi`，CPU 硬性限制 `200m` (fact-212c6db2ca21, fact-2a424fe5f56d) | 排除资源硬限制导致 OOMKill 的可能性（需结合日志确认） |
| 4 | Logging | Elasticsearch | 应用日志出现 `runtime process exiting` (错误级)，HTTP 状态码 `500`，路径 `/work` (fact-8487c7918b2e 等) | 直接关联到业务代码层处理异常并主动退出的行为 |
| 5 | Tracing | Deepflow | L7 Flow 显示对 `/work` 的 GET 请求返回 `500`，伴随响应状态 `3` (fact-4d9755cfa87d) | 在应用层日志前捕捉到 500 状态，佐证异常发生于请求处理链路中 |
| 6 | K8s State | Kubernetes | Pod 状态 `ContainersReady: False`，消息提示容器不可用 (fact-3020004cfa95) | 确证集群层面的服务可用性受损 |

**证据综合：**
Kubernetes 状态与 Metrics 一致确认了“持续重启-异常退出”的循环（证据 1, 2）。Logging 明确指出了退出前的直接动作：处理 `/work` 路径请求时返回 500 并终止进程（证据 4），而 Tracing 也捕捉到了相同的 500 响应流（证据 5）。这三者共同支撑了“应用层异常导致主动退出”而非“资源不足被系统杀死”的结论。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码处理 /work 时发生未捕获异常 (事实: 日志 fact-8487c7918b2e) 
  → HTTP 响应 500 后进程调用退出 (事实: 日志 fact-8487c7918b2e) 
  → 容器 Exit Code 2 被 Kubelet 捕获 (事实: fact-1cf9799274ab) 
  → 触发 CrashLoopBackOff 与反复重启 (事实: fact-1bf1bac6dfb3, fact-bff99444a679)
```

### 根因结论

**已确认的根因**：应用层代码在处理 `/work` 端点的 HTTP 请求时发生了未捕获的运行时异常。
该异常导致程序在返回 `HTTP 500` 后主动终止，容器退出码为 `2`。Kubernetes 检测到进程非正常退出后触发了指数退避重启机制，使 Pod 陷入 `CrashLoopBackOff` 状态（证据 1, 4, 5）。

**证据不足的方面**：
由于缺失崩溃瞬间的详细堆栈（Stack Trace）和具体业务依赖的日志，无法确定导致异常的具体代码行、异常对象类型（如空指针、除零等）或外部依赖故障（证据不足，missing_reasons: 崩溃前日志）。现有的事实仅能证实“发生了什么”以及“进程为何退出”，但无法解释“代码为何出错”。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 27.0s
├─ 并发证据采集: 75.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 75.2s (Evidence 67.4s, RCA 7.7s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime, pod-oomkilled, pod-config-error

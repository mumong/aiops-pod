## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod中app容器的应用服务在处理请求时发生内部错误（返回HTTP 500），导致Liveness探针持续检测失败，进而被Kubelet执行Killing操作（退出码137），最终使Pod进入CrashLoopBackOff状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Killing`: Container app failed liveness probe (19m, x4) | 确认 Liveness 探针判定失败，且该事件与后续的容器终止直接相关 |
| 2 | K8s Event | Kubernetes | `Unhealthy`: Liveness probe failed: HTTP probe failed with statuscode: 500 (19m, x8) | 提供探针具体的失败原因：应用返回了 HTTP 500 |
| 3 | K8s Event | Kubernetes | `BackOff`: Back-off restarting failed container app (75s, x67) | 确认 Pod 已进入 CrashLoopBackOff 状态，符合崩溃重启现象 |
| 4 | K8s State | Kubernetes | Container `app` last terminated reason: `Error` | 证实容器异常终止 |
| 5 | K8s State | Kubernetes | Container `app` exit code: `137` | 提供容器终止的具体退出码，通常关联 SIGKILL |
| 6 | K8s Config | Kubernetes | Memory Limit: `96Mi` / Request: `24Mi`；CPU Limit: `200m` / Request: `20m` | 证明该容器内存限制极低，资源受限，是评估 137 退出码成因的关键背景 |
| 7 | Logging | Elasticsearch | Pattern: `request completed` (HTTP 200, path: `/work`)；Occurrence: 8 | 显示应用能正常响应外部 HTTP 请求，作为排查探针失败原因的负面观测 |
| 8 | Tracing | Tempo/Deepflow | Span: `GET /work` (HTTP 200, mode: liveness_fail)；Flow: `GET /work` (200, 9次) | 确认 Liveness 探针本身发出的探测请求（GET /work）实际获得了 HTTP 200 响应 |

**证据关联与冲突：**
证据 1、2 明确指出探针判定失败是因为收到了 500 错误，而证据 7 和 8 却显示该端点对外返回的是 200。这种“探针报 500 但流量返回 200”的矛盾，结合证据 6 中极低的内存限制，强烈暗示探针失败并非因为常规的业务逻辑 500，而是应用因资源（如内存）耗尽导致内部崩溃（OOM Kill），此时应用无法处理探针请求从而由 Kubelet 或底层机制返回了 500/终止容器。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存极低限制(96Mi)与资源压力 → 触发容器 OOM(或资源耗尽)导致内部异常 → Liveness探针探测时应用无响应/返回500 → Kubelet执行Killing(Exit Code 137) → Pod CrashLoopBackOff
```

*注：直接触发 Liveness 判定失败的确切机制（是 OOM Kill 后的短暂崩溃还是其他代码逻辑）无法仅凭当前数据完全确认，但 Exit Code 137 和探针 500 之间的流量 200 差异由资源限制提供了高度可能的解释。*

### 根因结论

**已确认的根因与现象：**
Pod `aiops-case-10/workload-79d9f8fd88-48j8r` 的 `app` 容器频繁崩溃并进入 `CrashLoopBackOff` 状态。
根本机制确认为 **Liveness 探针失败** 触发 Kubelet 终止容器。探针在探测端点 `/work` 时接收到了 `HTTP 500` 状态码（证据 2），这导致容器被终止并带有 `Exit Code 137`（证据 5）。

**关键矛盾与进一步证据需求：**
然而，同一端点的外部流量和 Trace 显示请求均成功返回 `HTTP 200`（证据 7、8）。考虑到该容器的内存限制仅为 `96Mi`（证据 6），且 `Exit Code 137` 通常对应 `OOM Killed`，最可能的深层原因是**应用因内存耗尽而频繁崩溃**。当应用处于崩溃边缘或重启间隙时，探针请求无法被正常处理从而返回 500（或直接因 Kubelet 判定异常而终止容器，产生 137）。要最终确认是纯粹的 OOM 还是其他内存压力导致的 500，需查看崩溃前的 OOM 日志或验证探针失败时的容器内存状态，当前证据虽指向 OOM，但受限于缺失的 Crash 前日志，无法给出 100% 的断言。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 24.4s
├─ 并发证据采集: 65.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 65.4s (Evidence 54.3s, RCA 11.0s)
└─ 汇总总结: 15.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime

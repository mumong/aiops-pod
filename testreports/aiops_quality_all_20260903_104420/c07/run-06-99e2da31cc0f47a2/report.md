## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用容器在 /work 端点处理请求时因缺失关键配置（CONFIG_MISSING）而返回 HTTP 500 错误，并主动以退出码 78 终止进程，导致 Kubernetes 反复重启 Pod。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff (`fact-0bc1a224a8be`) | 确认应用容器处于反复重启的失败状态 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 78 (`fact-1eabc3cc8936`) | 指出进程由应用代码主动异常退出，而非 OOMKill 等系统行为 |
| 3 | Logging | Elasticsearch | HTTP 500 错误，`message: CONFIG_MISSING`, 路径 `/work` (`fact-193f0aa6da93`) | 提供根因线索，确认应用因缺少关键配置抛出 500 错误 |
| 4 | Tracing | Deepflow | 9 次等价 HTTP GET 请求至 `/work`，均返回 500 (`fact-522bcae1d3d8`) | 证明在异常发生前，流量确实触发了应用报错路径 |

证据表明：日志与追踪数据证实请求 `/work` 端点因 `CONFIG_MISSING` 返回 HTTP 500，且应用据此以退出码 78 终止；这与 Kubernetes 观测到的 CrashLoopBackOff 及退出码 78 完全吻合，共同指向应用层面的配置缺失导致进程主动退出。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行时缺少必要配置（CONFIG_MISSING） → 请求 /work 端点时抛出内部异常并返回 HTTP 500 → 应用捕获异常后以自定义退出码 78 主动退出 → Kubernetes 检测到容器非零退出码并触发 CrashLoopBackOff 重启机制
```

### 根因结论

已确认根因为：应用容器因缺失关键配置（`CONFIG_MISSING`）在处理 `/work` 请求时抛出 HTTP 500 错误，并据此以退出码 78 主动终止进程，进而引发 Kubernetes 的 CrashLoopBackOff 重启循环。

关键证据：
* 日志表明应用因 `CONFIG_MISSING` 返回了 500 错误（证据 #3）；
* 追踪数据显示存在 9 次导致 500 响应的请求，证明触发路径有效（证据 #4）；
* Kubernetes 状态证实了应用因非零退出码（78）被反复重启（证据 #1, #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 42.4s
├─ 并发证据采集: 64.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 64.4s (Evidence 55.5s, RCA 8.7s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime

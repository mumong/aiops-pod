## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态，日志显示接收 SIGTERM 后等待外部文件 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` [fact-1dc472c68178] | 确认 Pod 在运行后期失去响应能力 |
| 2 | Logging | elasticsearch | `SIGTERM received; waiting` [fact-5dd8ed65935f] | 证明进程接收到了终止信号但选择挂起 |
| 3 | K8s State | kubernetes | Pod 状态 `Terminating`，容器重启次数 `0` [fact-43a1d4a53524][fact-7998f514df1b] | 排除因崩溃重启（OOM/CrashLoop）导致的异常，确认是优雅退出机制卡死 |
| 4 | K8s State | kubernetes | 资源请求：CPU `5m`, Memory `8Mi` | 排除资源耗尽导致的计算或内存瓶颈 |
| 5 | K8s State | kubernetes | 容器资源限制：Memory `32Mi`, CPU `50m` | 提供资源边界上下文，非异常原因 |

**证据说明：**
- [fact-5dd8ed65935f] 和 [fact-1dc472c68178] 结合证实了应用处于非正常响应状态。
- [fact-43a1d4a53524] 和 [fact-7998f514df1b] 排除了容器意外崩溃的可能性，指向应用逻辑层面的阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
应用注册 SIGTERM 处理器并进入循环等待文件 '/state/teardown-requested' → Kubernetes 发送 SIGTERM 信号 → 应用日志显示 'SIGTERM received; waiting' 且未退出 → Pod 保持 Terminating 状态直至宽限期耗尽
```

### 根因结论

- **已确认的根因**：应用代码逻辑阻塞。
  - 应用代码显式注册了 SIGTERM 处理器，并在收到信号后进入等待外部文件 `/state/teardown-requested` 存在的循环 [fact-5dd8ed65935f]。
  - 该阻塞导致应用未执行正常的退出流程，从而触发 K8s 的强制终止机制 [fact-1dc472c68178]，表现为 Pod 长期停留在 `Terminating` 状态 [fact-43a1d4a53524]。

- **证据不足**：
  - 文件 `/state/teardown-requested` 未能正确创建或通知的原因未知（可能涉及挂载配置或上游控制器逻辑）。
  - 是否存在负责写入该文件的预期外部控制器或 Job 尚未确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.3s
├─ 并发证据采集: 51.4s
│  └─ g1 aiops-case-v13/workload: 51.4s (Evidence 42.7s, RCA 8.6s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck

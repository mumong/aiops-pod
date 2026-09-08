## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | {'message': 'cni.projectcalico.org/podIPs: 172.16.104.15/32'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Back-off 2m14s (x357 over 82m) kubelet Back-off restarting failed container app` | 确认 Pod 进入 CrashLoopBackOff 的严重状态，存在高频重启循环 |
| 2 | K8s State | kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.last_terminated_reason: Error` | 容器因错误终止且正在执行退避重启 |
| 3 | K8s State | kubernetes | `container.last_exit_code: 78` | 提供应用层直接退出原因，需结合日志确认语义 |
| 4 | Logging | elasticsearch | 模式 `http_request` [error] `CONFIG_MISSING`, `http_status: 500`, `path: /work` (连续记录中, first=0MiB, last=0MiB) | 确认应用代码在执行配置加载逻辑时明确抛出 CONFIG_MISSING 错误，退出码 78 与日志中的异常终止相吻合 |
| 5 | Tracing | deepflow | L7 Flow [HTTP GET /work] 响应 `500` (共9次), 关联 trace_ids 与日志一致 | 从流量视角确认请求被处理并返回 500，进一步证实应用能启动但逻辑层无法获取配置 |

**证据关联说明**：
日志中明确的 `CONFIG_MISSING` 错误和 Trace 中持续的 500 响应，直接解释了为何容器以退出码 78 终止。K8s 侧的 `CrashLoopBackOff` 现象是由应用启动后迅速因该错误退出触发的，证据链在应用层（日志/流量）与平台层（Pod 状态）之间完全闭环。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap workload-code 配置项挂载缺失 → 应用启动后读取配置触发 CONFIG_MISSING 异常 → 进程以退出码 78 终止 → Pod CrashLoopBackOff 循环
```

### 根因结论

**已确认的根因**：应用启动时无法获取必需的配置（日志显示 `CONFIG_MISSING`，退出码 `78`，导致请求直接返回 `500`），进而导致容器启动即失败并频繁重启。
**证据不足/未知**：虽然确定了是“配置缺失”导致，但无法从工具数据中证实 `ConfigMap workload-code` 本身是否存在于 `aiops-case-07` 命名空间，也无法确认应用代码挂载路径与 ConfigMap key 是否匹配。现有证据仅能确认应用层面的缺失现象，缺少基础设施层面的挂载校验事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 24.9s
├─ 并发证据采集: 69.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 69.6s (Evidence 58.3s, RCA 11.1s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime

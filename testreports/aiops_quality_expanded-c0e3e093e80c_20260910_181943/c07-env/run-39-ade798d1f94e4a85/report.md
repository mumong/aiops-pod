## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | 容器缺少必需的 APP_REQUIRED_CONFIG 环境变量 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 确认容器启动失败的直接原因 |
| 2 | K8s State | kubernetes | `container.last_exit_code: 78` | 支撑启动错误退出 |
| 3 | K8s State | kubernetes | `container.waiting_reason: CrashLoopBackOff` | 确认容器处于持续重启状态 |
| 4 | K8s Event | kubernetes | `event.message: Warning BackOff 5m2s (x327 over 75m)` | 确认异常已持续且进入退避重启期 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"} = 1` | 独立验证容器状态 |
| 6 | K8s Config | kubernetes | `resource_limit.memory: 32Mi` | 排除因内存硬限制导致 OOMKilled 的可能 |

**证据总结：**
日志明确指出了 `APP_REQUIRED_CONFIG` 环境变量缺失，与 `Kubernetes` 记录的 `CrashLoopBackOff` 状态及 `Metric` 的独立观测相互印证。退出码 `78` 和长期存在的 `BackOff` 事件表明故障发生在容器初始化启动阶段。内存限制 `32Mi` 排除了资源耗尽导致的崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
APP_REQUIRED_CONFIG 环境变量缺失 → 容器启动过程报错退出 (exit_code: 78) → 触发 K8s 重启机制 → CrashLoopBackOff 及用户可见服务不可用
```

### 根因结论

已确认的根因是容器应用缺少必需的 `APP_REQUIRED_CONFIG` 环境变量。该缺失导致应用在启动时直接报错退出（退出码 78），进而触发了 K8s 的崩溃重启循环（日志见证据 #1、#2，状态见证据 #3、#5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.3s
├─ 并发证据采集: 43.3s
│  └─ g1 aiops-case-v10/workload: 43.3s (Evidence 38.9s, RCA 4.2s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime

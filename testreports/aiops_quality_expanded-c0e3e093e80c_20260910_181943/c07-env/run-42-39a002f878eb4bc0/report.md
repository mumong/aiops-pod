## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod workload (aiops-case-v10)处于CrashLoopBackOff状态，无法进入Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container: `app`, last_terminated_reason: `Error`, last_exit_code: `78` | 确认应用进程异常退出，错误码 78 具有明确的语义指向。 |
| 2 | K8s State | kubernetes | container: `app`, resource_limit: `memory=32Mi` | 展示容器资源上限，内存配置极低，排除因资源超卖导致系统OOM (OOMKilled) 的可能性。 |
| 3 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 提供应用程序日志中的确切错误信息，直接证明启动时缺失环境变量。 |
| 4 | K8s Event | kubernetes | `Warning BackOff ... Back-off restarting failed container app` | 确认 Kubernetes 调度层检测到上述 Error 后触发了指数退避重启机制。 |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason(container=app, reason=Error) = 1` | 从指标视角佐证终止原因为应用主动报错退出，非系统底层异常。 |

**证据关联分析**
日志 `fact-10c09513c777` 揭示了应用进程主动退出的具体原因（`APP_REQUIRED_CONFIG` 缺失），与 K8s 状态 `fact-669670dc96af` 中的 `Exit Code 78` 形成完美闭环（通常该代码在应用框架中代表配置类错误）。同时，极低的内存限制 `fact-084f66e73011` (32Mi) 与日志报错相印证，排除了因内存溢出被 K8s 强杀（Exit Code 137）的可能性，进一步确认了是应用逻辑主动终止。

## 🎯 根因分析 · g1

### 因果链

```text
Pod定义中缺失 APP_REQUIRED_CONFIG 环境变量定义 → 容器启动时应用检测到值为 None → 应用进程调用 sys.exit(78) 主动终止退出 → Kubernetes 持续重启触发 CrashLoopBackOff
```

### 根因结论

已确认根因：**应用主进程依赖的 `APP_REQUIRED_CONFIG` 环境变量未在 Pod 定义中配置**。

这一事实由 `fact-10c09513c777` (Logging) 直接证明。应用检测到该关键配置缺失后，以 Exit Code 78 主动终止进程（由 `fact-39eb7f978f77` 和 `fact-669670dc96af` 佐证）。Kubernetes 的 `BackOff` 事件（`fact-f378caafe1e9`）是这一进程反复崩溃后的系统响应，而非故障本身。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 35.7s
├─ 并发证据采集: 34.0s
│  └─ g1 aiops-case-v10/workload: 34.0s (Evidence 25.4s, RCA 8.5s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime

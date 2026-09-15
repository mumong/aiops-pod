## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | 缺少环境变量 APP_REQUIRED_CONFIG |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: Error | 证明容器最后一次以非零状态退出 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 78 | 提供具体的进程退出码，指向应用层启动失败 |
| 3 | Logging | Elasticsearch | `log.message`: "APP_REQUIRED_CONFIG environment variable is missing" | 直接捕获应用启动时的关键报错，明确缺失依赖 |
| 4 | K8s Event | Kubernetes | `event.message`: "Warning BackOff ... kubelet Back-off restarting failed container app" | 证明 Kubernetes 正在频繁重启容器并进入退避机制 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: 1 (CrashLoopBackOff) | 监控侧确认当前容器处于等待重启状态 |

日志中明确记录了环境变量的缺失，这与 K8s 记录的 `CrashLoopBackOff` 状态及 `Exit Code 78` 高度一致：应用启动脚本因找不到 `APP_REQUIRED_CONFIG` 而主动终止。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中未配置环境变量 → 启动脚本检查缺失 → 进程以 78 退出 → CrashLoopBackOff
```

### 根因结论

**已确认根因：Pod 配置中缺少必需的环境变量 `APP_REQUIRED_CONFIG`。**

日志（#3）明确指出了具体的缺失对象，结合 K8s 状态（#1, #2）中观察到的非零退出码，形成了完整的证据闭环。该配置缺失导致应用无法正常启动，进而触发 K8s 的重启策略，表现为当前的 CrashLoopBackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 29.7s
├─ 并发证据采集: 36.4s
│  └─ g1 aiops-case-v10/workload: 36.4s (Evidence 28.7s, RCA 7.5s)
└─ 汇总总结: 6.2s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime

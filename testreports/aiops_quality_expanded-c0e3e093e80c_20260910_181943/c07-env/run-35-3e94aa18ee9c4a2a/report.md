## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | 容器配置缺失：Pod `aiops-case-v10/workload` 的启动命令硬编码依赖环境变量 `APP_REQUIRED_CONFIG`，但 Pod YAML 定义中未注入该变量（`environment: <none>`），导致容器启动即退出（Exit Code 78）并陷入 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.last_terminated_reason: Error` | 确认 Pod 处于持续重启状态 |
| 2 | K8s Config | Kubernetes | `container.resource_request.memory: 8Mi`, `container.resource_request.cpu: 5m` | 确认资源请求量极低，排除资源限制导致的 OOMKilled |
| 3 | K8s State | Kubernetes | `container.last_exit_code: 78` | 提供精确的退出码，指向运行时或配置依赖缺失 |
| 4 | Logging | Elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 直接指出应用层无法获取的环境变量名称 |
| 5 | K8s Event | Kubernetes | `Warning BackOff 98s (x281 over 61m) Back-off restarting failed container app` | 展示启动失败已形成周期性指数退避重启循环 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"} = 1` | 独立验证了 K8s 状态中的 CrashLoopBackOff 结论 |

**证据关联：**
Kubernetes 状态（#1, #3）结合退出码 78，直接对应日志中记录的特定环境变量缺失（#4）；指标数据（#6）与重启事件（#5）确认了这一失败机制的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量 `APP_REQUIRED_CONFIG` 未注入 → 应用启动读取失败 → 退出码 78 导致 CrashLoopBackOff → 用户可见 Pod 持续重启
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-v10/workload` 的配置缺失。启动命令硬编码依赖环境变量 `APP_REQUIRED_CONFIG`，但 Pod 定义中未注入该变量。这一配置缺失直接导致容器启动即失败并退出（Exit Code 78），进而触发 Kubernetes 的重启机制并进入 `CrashLoopBackOff` 状态。
证据支持：#4（日志明确报错）+ #1, #3（K8s 状态验证退出原因）。

---

## 📊 性能统计

```text
├─ 总耗时: 58.4s
├─ 问题定位: 22.9s
├─ 并发证据采集: 27.8s
│  └─ g1 aiops-case-v10/workload: 27.8s (Evidence 19.7s, RCA 7.9s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime

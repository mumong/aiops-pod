## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod workload 在容器启动命令中依赖环境变量 APP_REQUIRED_CONFIG，但该变量未在任何配置（如 ConfigMap、Secret 或 env字段）中定义。容器主进程启动时检测到该变量缺失，主动执行 sys.exit(78) 终止运行，导致 Kubernetes 持续重启容器并进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | Elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` (fact-26f5061a7001) | 证明容器启动失败的具体原因是配置缺失。 |
| 2 | K8s State | Kubernetes | 退出码 `exit_code: 78` (fact-3cbf7a678a6f) | 证实容器异常终止，与依赖缺失的特定退出逻辑一致。 |
| 3 | K8s Event | Kubernetes | `Warning BackOff 69s (x398 over 86m) ... Back-off restarting failed container app` (fact-40548cf66c0a) | 证实容器处于持续重启循环中，且重启频率正在增加。 |
| 4 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` (fact-eed442d1f106) | 描述当前容器的异常等待状态。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (CrashLoopBackOff) (fact-00e07d127115) | 独立观测到容器状态为 CrashLoopBackOff，与 K8s 状态一致。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total=21` (fact-00db3212669f) | 证实容器已重启 21 次。 |

K8s 状态显示容器因异常退出（Error）而进入 CrashLoopBackOff 状态，Metric 数据从 Prometheus 角度交叉验证了这一状态及重启次数。Elasticsearch 日志中关于缺失环境变量的明确报错，解释了为何进程以退出码 78 终止，并直接指向了缺失配置这一根本原因。

## 🎯 根因分析 · g1

### 因果链
```text
环境变量 APP_REQUIRED_CONFIG 未定义 → 容器主进程启动时检测到缺失主动退出 (sys.exit(78)) → K8s 重启容器失败并进入 CrashLoopBackOff → Pod 持续重启且无法就绪
```

### 根因结论
已确认的根因为 Pod `workload` 的容器启动命令依赖环境变量 `APP_REQUIRED_CONFIG`，但该变量在 ConfigMap、Secret 或 Pod 配置中均未定义。
这一配置缺失导致容器主进程在启动阶段检测到错误并主动终止（退出码 78），Kubernetes 随之触发重启机制，最终导致 Pod 陷入 `CrashLoopBackOff` 状态（证据 1、2、4）。日志、退出码与 K8s 等待状态相互印证，构成了完整的故障证据链。

---

## 📊 性能统计

```text
├─ 总耗时: 59.4s
├─ 问题定位: 14.6s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-v10/workload: 35.6s (Evidence 28.8s, RCA 6.6s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime

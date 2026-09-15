## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod配置缺失环境变量APP_REQUIRED_CONFIG，导致应用启动即因退出码78失败并陷入CrashLoopBackOff循环 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 确认应用因缺失关键配置无法启动的直接原因 |
| 2 | K8s State | kubernetes | `last_exit_code: 78` | 确认应用因配置缺失引发的退出码，验证启动即失败 |
| 3 | K8s Event | kubernetes | `Warning BackOff ... Back-off restarting failed container app in pod workload_aiops-case-v10` | 确认因持续重启导致指数退避的异常行为 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` (last=15.0, min=3.0) | 提供重启频次的时间趋势，确认为高频持续重启现象 |
| 5 | K8s State | kubernetes | `restart_count: 15` | 确认容器在 Pod 运行期间已频繁重启 |

证据说明：
- **日志与状态印证**：日志中的缺失环境变量（#1）直接解释了容器以退出码 78（#2）失败的原因。
- **趋势与事件印证**：退出码 78 导致容器不断重启，进而引发 Metric 中重启总数增加至 15 次（#4, #5），并触发 K8s BackOff 事件（#3）进入 CrashLoopBackOff 循环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置缺失环境变量APP_REQUIRED_CONFIG → 应用启动即因退出码78失败 → 容器持续重启触发CrashLoopBackOff循环 → 用户可见Pod状态CrashLoopBackOff及BackOff事件
```

### 根因结论

已确认的根因为 Pod 配置缺失环境变量 `APP_REQUIRED_CONFIG`。该缺失导致应用启动时无法获取必要配置，直接抛出错误并以退出码 78 终止（证据 #1, #2）。持续的启动失败触发了 K8s 的重启机制，导致重启计数攀升（证据 #4, #5）并最终进入 CrashLoopBackOff 状态（证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 28.4s
├─ 并发证据采集: 76.6s
│  └─ g1 aiops-case-v10/workload: 76.6s (Evidence 71.8s, RCA 4.6s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime

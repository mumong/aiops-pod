## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: reason=OOMKilled, container=app | 确认进程终止的直接原因是内核 OOM Killer 触发 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory`: value=64Mi, container=app | 提供硬限制基准，内存分配触及此阈值即面临被杀风险 |
| 3 | Logging | elasticsearch | `memory allocation advanced`: allocated_mib 从 10 增至 46 | 证实应用内存呈持续增长趋势，在观察窗口内逼近限制 |
| 4 | K8s State | kubernetes | `container.last_exit_code`: exit_code=137 | 确认异常退出代码，符合 OOM 终止特征 |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: reason=OOMKilled | 外部时序数据佐证容器近期终止原因为 OOM |
| 6 | K8s State | kubernetes | `container.waiting_reason`: reason=CrashLoopBackOff | 确认 kubelet 频繁重启容器导致的当前异常状态 |
| 7 | Tracing | deepflow+tempo | `GET /work`: response_code=200, aiops.observed_mode=oom_growth | 确认故障服务接口在内存增长期间仍响应成功，故障点在内存耗尽之后 |

证据互相印证：K8s 状态中的 `OOMKilled`、`exit_code=137` 与 Metrics 日志高度一致；Logging 显示应用在 `/work` 路径下持续分配内存（46 MiB），逼近 Config 中 64 MiB 的硬限制；Tracing 表明请求本身能处理完，说明失败发生在分配后、提交给内核之前。

## 🎯 根因分析 · g1

### 因果链

```text
应用持续分配内存（Logging: allocated_mib 增至 46） → 触及 64Mi 硬限制（K8s Config） → 内核 OOM Killer 终止进程（K8s/Metrics: OOMKilled, exit 137） → 导致 CrashLoopBackOff（K8s State）
```

### 根因结论

已确认根因为应用内存使用持续增长（最高观察至 46 MiB）逼近并可能突破 `64Mi` 的容器内存限制，触发内核 OOM Killer 终止进程，进而引发 Kubernetes 的 CrashLoopBackOff。证据链完整闭环，包含日志增长趋势、限制配置、终止原因及退出码的直接印证。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 37.1s
├─ 并发证据采集: 85.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 85.8s (Evidence 74.5s, RCA 11.1s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-oomkilled

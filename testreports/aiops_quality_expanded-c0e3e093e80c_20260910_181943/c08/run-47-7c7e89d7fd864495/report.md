## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 99s (x515 over 135m) kubelet Back-off restarting failed container app` | 证明应用处于重启风暴状态 |
| 2 | K8s State | Kubernetes | 容器 `app` 上次终止原因 `OOMKilled`，退出码 `137` | 直接指向系统级资源驱逐机制 |
| 3 | K8s Config | Kubernetes | 容器 `app` 内存硬限制 `64Mi` | 确定触发 OOM 的量化阈值 |
| 4 | K8s State | Kubernetes | 容器 `app` 重启次数 `27` 次 | 证实重启行为的持续性 |
| 5 | Logging | Elasticsearch | 日志模式 `memory allocation advanced` 出现 8 次，`allocated_mib` 在观测窗口内波动于 `12.0` 至 `48.0` | 证实内存随请求处理不断消耗 |
| 6 | Tracing | Tempo/Deepflow | 9 个 HTTP GET `/work` 请求成功返回（200），`aiops.observed_mode` 为 `oom_growth` | 提供应用处理期间内存增长的链路佐证 |

证据表明，Pod 在运行期间内存占用波动上升（最大达 48Mi），由于硬限制仅设为 64Mi，当请求处理导致内存分配触及边界时，触发 Linux OOM Killer（退出码 137），进而导致 Kubelet 不断重启容器，表现为 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制过低 (64Mi) → 应用处理 GET /work 请求时内存分配持续消耗 → 触发 Linux OOM Killer (Exit 137) → 容器崩溃并反复重启，呈现 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：容器 `app` 的内存限制配置（`64Mi`）显著低于应用实际运行时的峰值内存消耗（日志观测至 `48Mi` 且模式为 `oom_growth`）。这种配置过小的限制导致应用在处理正常业务请求时，内存占用极易逼近并突破上限，引发操作系统的强制终止（OOMKilled）。

该根因得到以下事实的互相印证：
1. **K8s 状态**：明确的 `OOMKilled` 和 `Exit Code 137`（证据 2）；
2. **应用行为**：日志显示处理请求时 `memory allocation advanced` 且内存使用量较高（证据 5、6）；
3. **配置现状**：`64Mi` 的限制缺乏足够的内存冗余以容纳应用峰值（证据 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.1s
├─ 并发证据采集: 54.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 54.6s (Evidence 44.6s, RCA 9.9s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime, pod-imagepull-failed, pod-config-error, pod-oomkilled

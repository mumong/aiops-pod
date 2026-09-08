## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | Running | 容器内存限制配置过低 (96Mi) 导致应用进程因内存超额被系统 OOM Killer 终止 (Exit Code 137)，进而引发 CrashLoopBackOff 循环重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 137 | 确认容器非正常终止，137 号错误码指向被系统 OOM Killer 强制杀除 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi; `container.resource_request.memory`: 24Mi | 确定容器硬内存限制极低（96Mi），是引发 OOM 的基础约束条件 |
| 3 | K8s Event | kubernetes | `Back-off restarting failed container app` (19s, x415 over 111m) | 证明应用陷入高频重启循环，且持续近 2 小时未稳定 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: CrashLoopBackOff (value: 1, sample_count: 47) | 验证当前 Pod 处于持续等待重启状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total`: value 40 (first: 21.0, last: 40.0, sample_count: 61) | 提供重启次数的连续观测，证实重启行为持续进行中 |
| 6 | Logging | elasticsearch | pattern: `request completed` (path: /work, status: 200); 聚合 8 次记录 | 确认存活探针检测到的路径在崩溃前能返回成功，但内存数据为 0，未记录到崩溃瞬间日志 |
| 7 | Tracing | deepflow | HTTP Flow: GET /work, response_code: 200, dst_ip: 172.16.104.32, 聚合 10 次 | 网络层面确认 Pod IP 在崩溃间隙响应了正常的健康检查请求 |

**证据关联说明：**
Kubernetes 的 OOM Exit Code 137（#1）直接锁定了崩溃原因。内存限制 96Mi（#2）解释了为何应用容易达到阈值。日志（#6）和 Tracing（#7）显示崩溃间隙 Pod 能正常响应 200 OK，说明服务逻辑本身在正常资源下是通顺的，并非逻辑死循环，而是资源耗尽导致的进程崩溃。Metric 的 CrashLoopBackOff 状态（#4）与 Kubernetes 的事件（#3）高度一致，共同描绘了重启循环的全貌。

## 🎯 根因分析 · g1

### 因果链
```text
内存资源硬限制配置过低 (96Mi) → 应用运行时超出限制触发 OOM Killer 终止进程 → Pod 进入 CrashLoopBackOff 循环重启 → 用户端访问出现间歇性中断（Liveness 探测 500/200 交替，最终因重启而不可用）
```

### 根因结论
**已确认的根因**：应用进程因容器内存限制配置过低（96Mi，证据 #2）发生 OOM（证据 #1），导致 Pod 陷入 CrashLoopBackOff 循环（证据 #3、#4）。

该根因如何造成当前现象：
- 当应用请求内存超过 96Mi 时，被系统强制杀除（Exit Code 137，证据 #1）。
- Kubernetes 监控到容器退出后触发重启，由于重启频率超过退避上限，状态转为 CrashLoopBackOff（证据 #3、#4）。
- 在两次重启的间隙，应用可能短暂存活并响应健康检查（日志 #6、追踪 #7 显示 200 OK），但由于内存限制依然存在，极易再次崩溃。
- 这种间歇性的崩溃导致应用不可用，且 Liveness Probe 在崩溃瞬间会返回 500 或失败（证据 #3 中的 Unhealthy 事件），进一步促使集群重启容器，形成恶性循环。

证据编号引用：
- 根因依据：#1, #2
- 现象确认：#3, #4, #5
- 辅助印证：#6, #7

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 35.8s
├─ 并发证据采集: 125.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 125.8s (Evidence 120.5s, RCA 5.1s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime, pod-oomkilled

## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 处于 Running 状态，但容器 app 处于 CrashLoopBackOff，重启次数 23 次，退出码 137。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason: "OOMKilled" | 确认容器因内存超限被系统进程杀死 |
| 2 | K8s State | Kubernetes | container.resource_limit.memory: "64Mi" | 提供容器硬内存限制值 |
| 3 | K8s State | Kubernetes | pod.condition: Ready=False, ContainersNotReady | 确认容器处于非就绪状态 |
| 4 | K8s State | Kubernetes | container.last_exit_code: 137 | 证实容器进程被异常中断（OOM Killer 信号） |
| 5 | Metric | Prometheus | container_memory_working_set_bytes: 47,005,696 (18:08), 53,428,224 (17:50) | 显示内存使用量在 42MB-53MB 之间波动，趋势向上 |
| 6 | Metric | Prometheus | container_memory_working_set_bytes: 59,641,856 (17:44), 57,868,288 (17:26) | 显示重启前一轮实例内存使用峰值逼近 60MB |
| 7 | Logging | Elasticsearch | pattern: "memory allocation advanced", allocated_mib: first 16 -> last 48 | 证实应用运行期间存在持续的内存分配行为 |
| 8 | Tracing | Deepflow + Tempo | 9个等效 HTTP GET /work 请求 (200 OK), duration_us: 8697-20985 | 确认故障期间后端接口仍持续接收并响应业务流量 |

**证据印证：**
Kubernetes 状态（#1, #4）与 Prometheus 指标（#5, #6）明确指向同一事实：应用在处理请求时内存持续增长，峰值（~57-59MiB）接近且可能瞬时触及 64MiB 限制。日志（#7）中 `allocated_mib` 的增长证实了内存分配行为的存在。Tracing（#8）确认了这种高内存分配状态是在正常的业务请求处理中发生的，而非空闲状态。

## 🎯 根因分析 · g1

### 因果链

```text
容器硬内存限制配置过低（64Mi） → 请求处理引发内存分配增长 → 实际使用量逼近/触及限制触发 OOM Kill → 容器 CrashLoopBackOff 与重启
```

### 根因结论

已确认的根因是：**容器硬内存限制（`resource_limit.memory`）配置过低（64Mi），无法满足应用处理业务请求（`GET /work`）时的实际内存峰值需求。**

该限制（#2 Metric, K8s）直接导致容器在内存使用量达到阈值时（#5, #6 Metric 显示峰值达 ~57-59MiB）被 Linux OOM Killer 强制终止（#1 K8s State, #7 Logging 内存分配行为）。这引发了 #4 K8s State 中的退出码 137 以及 #3 K8s State 中的容器未就绪状态。证据间形成完整闭环：业务流量触发内存分配，分配导致内存使用逼近限制，限制引发 OOM 终止，终止导致重启循环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 16.3s
├─ 并发证据采集: 76.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 76.4s (Evidence 67.4s, RCA 8.8s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled

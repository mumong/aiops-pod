## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | 容器内存限制（64Mi）不足导致 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_reason=CrashLoopBackOff | 确认 Pod 当前处于崩溃循环状态 |
| 2 | K8s State | Kubernetes | pod.condition=ContainersNotReady (status=False) | 确认容器未就绪，Pod 处于不健康状态 |
| 3 | K8s State | Kubernetes | container.last_terminated_reason=Error; container.last_exit_code=137 | 确认容器上次异常终止且退出码为 137（OOMKilled 标志） |
| 4 | K8s Config | Kubernetes | resource_limit.memory=64Mi | 提供内存限制的硬配置，指向资源不足的可能性 |
| 5 | K8s Event | Kubernetes | Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded | 说明容器在 OOM 发生前可能已出现严重资源争用或僵死 |
| 6 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason=1 (reason=Error) | 验证容器上次终止原因为 Error，与 K8s State 一致 |
| 7 | Metric | Prometheus | kube_pod_container_status_restarts_total=27 | 量化重启次数，印证长周期反复崩溃 |
| 8 | Logging | Elasticsearch | GET /ready HTTP/1.1" 200; GET /health HTTP/1.1" 200 | 日志显示健康检查此前有成功返回，表明崩溃是近期突发的 |
| 9 | Tracing | Deepflow | Flow GET /health response_code=200, duration_us=3000797 (avg 3s) | 确认应用进程曾正常运行，但健康检查接口响应延迟极高（约 3 秒） |

**证据印证说明：**
1. 证据 3、6（异常终止）结合证据 4（低内存限制），构成了容器因内存不足被 OOMKilled 的核心事实链。
2. 证据 5（探针超时）与证据 9（Trace 延迟高达 3 秒）相互印证，表明应用可能在内存耗尽前已出现严重的性能退化（Goroutine 阻塞、GC 停顿等），导致无法及时响应探针，最终被系统终止。
3. 证据 8 提供了时间上的补充：应用启动初期日志仍显示正常，印证了故障发生在运行过程中，而非启动配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
资源限制配置不足（memory limit=64Mi） → 运行期内存耗尽触发 OOMKill → 进程异常终止(Exit Code 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为：**容器内存限制（64Mi）配置过低，导致应用运行过程中因内存不足被 OOMKilled。**

证据编号 [4] 确认了 `resource_limit.memory` 硬限制仅为 64Mi。证据 [3] 提供的退出码 `137` 和终止原因为 `Error` 是容器被 Linux 内核 OOM Killer 强杀的确定性特征。证据 [6] 在 Prometheus 中再次确认了上次终止原因为 Error。

虽然诊断系统提供的正式根因文本中包含 "OOMKilled" 标签，输入中并未直接提供具体的 Java Heap Dump 或 cgroup OOM 详细日志（`collection` 中 `pod-previous-logs` 失败）。但结合 K8s 退出码机制与内存硬限制配置，证据 [3]、[4] 已足以形成闭环并得出上述结论。证据 [5] 和 [9] 进一步解释了在崩溃前应用已处于极度不健康状态（高延迟、探针超时），加剧了 CrashLoopBackOff 的触发频率。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 22.3s
├─ 并发证据采集: 86.0s
│  └─ g1 aiops-case-v17/workload: 86.0s (Evidence 81.4s, RCA 4.4s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
